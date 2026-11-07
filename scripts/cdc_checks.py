#!/usr/bin/env python3
"""Digital reset/input DV plus actual nonempty, unwaived scoped CDC analysis."""
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
import harness
import rtl_checks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c=rtl_checks.Checks('cdc',task='T029',scope='Digital reset/input primitive DV and scoped18-input synthesized CDC fixture; retained independent-GPIO CDC-6 Warning')
    c.result['excluded']=['analog metastability/MTBF','atomic multibit transfer/pulse capture/debounce','complete SoC/routed CDC','formal','routed timing','hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest()
        rtl=['rtl/peripherals/reset_sync.sv','rtl/peripherals/input_sync.sv'];tb='dv/cdc/tb_cdc.sv'
        structure=rtl+['rtl/peripherals/uart_rx.sv','dv/cdc/cdc_probe.sv','dv/cdc/cdc_registered_probe.sv']
        sources=structure+[tb,'dv/cdc/test_cdc.py','scripts/cdc_checks.py','scripts/cdc_structure.tcl',
            'scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py','.harness/checks.json','config/rtl_checks.json','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources};c.versions(manifest)
        spec=importlib.util.spec_from_file_location('cdc_reference',harness.inside('dv/cdc/test_cdc.py'))
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        cwd=c.base/'simulation';artifacts={};c.result['seed_reports']=[]
        r=c.vendor('xvlog',['--sv']+[str(harness.inside(f)) for f in rtl+[tb]],cwd,15)
        c.require(rtl_checks.successful(r),'Actual reset/input SystemVerilog compile',r)
        r=c.vendor('xelab',['work.tb_cdc','--snapshot','cdc','--timescale','1ns/1ps','--debug','typical'],cwd,30)
        c.require(rtl_checks.successful(r),'Actual CDC digital elaboration',r)
        tcl=cwd/'run.tcl';harness.atomic_text(tcl,'log_wave /tb_cdc/clk /tb_cdc/run_clock /tb_cdc/arst /tb_cdc/rst /tb_cdc/data /tb_cdc/word_out /tb_cdc/wide_out /tb_cdc/bit_in /tb_cdc/bit_out\nrun all\nquit\n')
        artifacts[tcl.relative_to(harness.ROOT).as_posix()]=sha(tcl)
        def simulate(work,vector,name,seed=1,snapshot='cdc',script=tcl):
            wave=work/(name+'.wdb')
            r=c.xsim([snapshot,'--tclbatch',str(script),'--onerror','quit','--onfinish','quit','--sv_seed',str(seed),
                '--testplusarg','SEED='+str(seed),'--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],work,30,name)
            return r,wave
        first=None
        for seed in (1,20261106):
            text,summary=model.vectors(seed);count=len(text.splitlines())
            c.require(count==summary['cycles'] and count>1500 and summary['one_hot_bits']==list(range(32)) and summary['phases']==[0,1,2,3] and summary['subcycle_pulses']>30,'Counted reset/input phases/patterns/pulses')
            vector=cwd/('seed_%d.txt'%seed);harness.atomic_text(vector,text)
            summary_path=cwd/('seed_%d_summary.json'%seed);harness.atomic(summary_path,summary)
            r,wave=simulate(cwd,vector,'seed_%d'%seed,seed)
            c.require(rtl_checks.successful(r,'CDC_SIM_PASS seed=%d checked=%d'%(seed,count)),'Independent asynchronous reset/input native seed='+str(seed),r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Saved actual CDC digital waveform')
            c.result['simulations'].append({'seed':seed,'checked_vectors':count,'vector_path':vector.relative_to(harness.ROOT).as_posix(),'vector_sha256':sha(vector),
                'waveform':wave.relative_to(harness.ROOT).as_posix(),'waveform_sha256':sha(wave)})
            c.result['seed_reports'].append({'seed':seed,'summary':summary_path.relative_to(harness.ROOT).as_posix()});artifacts[summary_path.relative_to(harness.ROOT).as_posix()]=sha(summary_path)
            if seed==1:first=text
        lines=first.splitlines();wrong=lines[0].split();wrong[9]='0'
        for name,text,diagnostic in [('wrong-reset-expectation',' '.join(wrong)+'\n','CDC_MISMATCH'),('empty','','CDC_EMPTY_VECTORS'),
                ('truncated',lines[0]+'\n0 1\n','CDC_MALFORMED_VECTOR')]:
            vector=cwd/(name+'.txt');harness.atomic_text(vector,text);r,wave=simulate(cwd,vector,name);output=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'CDC_SIM_PASS' not in output,'Actual CDC input negative '+name,r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Saved negative waveform');artifacts.update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (vector,wave)})
        r=c.vendor('xelab',['work.tb_cdc_bad_width','--snapshot','badwidth','--timescale','1ns/1ps','--debug','typical'],cwd,30)
        c.require(rtl_checks.successful(r),'Invalid-width test elaborates',r)
        bad_tcl=cwd/'badwidth.tcl';harness.atomic_text(bad_tcl,'log_wave /tb_cdc_bad_width/result\nrun all\nquit\n')
        r,wave=simulate(cwd,cwd/'seed_1.txt','bad-width',snapshot='badwidth',script=bad_tcl)
        c.require(r['status'] in ('PASS','FAIL') and 'INPUT_SYNC_WIDTH' in r['stdout']+r['stderr'] and 'CDC_WIDTH_CHECK_MISSING' not in r['stdout']+r['stderr'],'Actual invalid WIDTH33 rejects',r)
        for p in (bad_tcl,wave):artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        mutations=[('one-edge-release',rtl[0],'assign rst_o=release_q[1];','assign rst_o=release_q[0];','CDC_MISMATCH'),
            ('missing-async-assert',rtl[0],'@(posedge clk_i or posedge arst_i)','@(posedge clk_i)','CDC_ASYNC_ASSERT'),
            ('input-stage-bypass',rtl[1],'assign sync_o=sync_q;','assign sync_o=meta_q;','CDC_MISMATCH')]
        for name,target,before,after,diagnostic in mutations:
            work=c.base/('mutation-'+name);work.mkdir();original=harness.inside(target).read_text();c.require(original.count(before)==1,'Unique digital mutation '+name)
            changed=work/target.split('/')[-1];harness.atomic_text(changed,original.replace(before,after));vector=work/'vectors.txt';harness.atomic_text(vector,first)
            r=c.vendor('xvlog',['--sv']+[str(changed if f==target else harness.inside(f)) for f in rtl+[tb]],work,15)
            c.require(rtl_checks.successful(r),'Actual digital mutant compile '+name,r)
            r=c.vendor('xelab',['work.tb_cdc','--snapshot','cdc','--timescale','1ns/1ps','--debug','typical'],work,30)
            c.require(rtl_checks.successful(r),'Actual digital mutant elaborate '+name,r)
            r,wave=simulate(work,vector,name);output=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'CDC_SIM_PASS' not in output,'Digital fault detected '+name,r)
            for p in (changed,vector,wave):
                c.require(p.is_file() and p.stat().st_size>0,'Saved digital mutant '+p.name);artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        c.result['structural_runs']=[]
        for name,target,before,after in [('positive',None,None,None),
                ('missing-rx-attribute','rtl/peripherals/uart_rx.sv','(* ASYNC_REG="TRUE" *)',''),
                ('input-stage-bypass',rtl[1],'assign sync_o=sync_q;','assign sync_o=meta_q;')]:
            work=c.base/('structure-'+name);work.mkdir();changed=None
            if target:
                original=harness.inside(target).read_text();c.require(original.count(before)==1,'Unique structure mutation '+name)
                changed=work/target.split('/')[-1];harness.atomic_text(changed,original.replace(before,after));artifacts[changed.relative_to(harness.ROOT).as_posix()]=sha(changed)
            source_list=work/'sources.txt';harness.atomic_text(source_list,'\n'.join(str(changed if f==target else harness.inside(f)) for f in structure)+'\n')
            r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('scripts/cdc_structure.tcl')),'-tclargs',str(source_list)],work,60)
            output=r['stdout']+r['stderr']
            if target:c.require(r['status'] in ('PASS','FAIL') and 'CDC_RULE_REJECTED' in output and 'CDC_STRUCTURE_PASS' not in output,'Actual unsafe/untagged CDC rejected '+name,r)
            else:
                c.require(rtl_checks.successful(r,'CDC_STRUCTURE_PASS chains=18 stages=36 rules=3 retained_warning=CDC-6') and 'SW Build '+str(manifest['vivado_sw_build']) in output,'Actual18 chains/nonempty3-rule CDC, Warning retained',r)
                checks=(work/'timing_checks.rpt').read_text()
                c.require(re.findall(r'^\d+\. checking \S+ \((\d+)\)',checks,re.M) and all(int(n)==0 for n in re.findall(r'^\d+\. checking \S+ \((\d+)\)',checks,re.M)),'Analysis clocks/I/O constraints cover all endpoints')
            for p in work.glob('*'):
                if p.is_file():artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
            c.result['structural_runs'].append({'variant':name,'command_index':len(c.result['commands'])-1,'cwd':work.relative_to(harness.ROOT).as_posix()})
        c.result['artifacts']=artifacts
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'CDC source bindings unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
