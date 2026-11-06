#!/usr/bin/env python3
"""Independent real-SV GPIO/timer transactions, including priority fault injection."""
import datetime as dt
import hashlib
import importlib.util
import json
import sys
import harness
import rtl_checks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c=rtl_checks.Checks('mmio',task='T028',scope='Standalone synchronized GPIO and free-running timer, two independent bus channels; no SoC/IRQ')
    c.result['excluded']=['complete CDC/MTBF','SoC/compiled firmware','interrupts','full regression','formal','routed timing','hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest()
        rtl=['rtl/peripherals/input_sync.sv','rtl/peripherals/gpio.sv','rtl/peripherals/timer.sv'];tb='dv/integration/tb_mmio.sv'
        sources=rtl+[tb,'dv/integration/test_mmio.py','scripts/mmio_checks.py','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py',
            '.harness/checks.json','config/rtl_checks.json','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources};c.versions(manifest)
        spec=importlib.util.spec_from_file_location('mmio_reference',harness.inside('dv/integration/test_mmio.py'))
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        cwd=c.base/'simulation';artifacts={};c.result['seed_reports']=[]
        r=c.vendor('xvlog',['--sv']+[str(harness.inside(f)) for f in rtl+[tb]],cwd,15)
        c.require(rtl_checks.successful(r),'Actual GPIO/timer SystemVerilog compile',r)
        r=c.vendor('xelab',['work.tb_mmio','--snapshot','mmio','--timescale','1ns/1ps','--debug','typical'],cwd,30)
        c.require(rtl_checks.successful(r),'Actual MMIO elaboration',r)
        signals=['clk','rst','switches','leds','gv','ga','gw','gd','gb','gr','gq','gs','gdata','ge','tv','ta','tw','td','tb','tr','tq','ts','tdata','te']
        tcl=cwd/'run.tcl';harness.atomic_text(tcl,'log_wave '+' '.join('/tb_mmio/'+s for s in signals)+'\nrun all\nquit\n')
        artifacts[tcl.relative_to(harness.ROOT).as_posix()]=sha(tcl)
        def simulate(work,vector,name,seed=1):
            wave=work/(name+'.wdb')
            r=c.xsim(['mmio','--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit','--sv_seed',str(seed),
                '--testplusarg','SEED='+str(seed),'--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],work,30,name)
            return r,wave
        first=None
        for seed in (1,20261106):
            text,summary=model.corpus(seed);count=len(text.splitlines())
            c.require(count==summary['cycles'] and count>4096,'Counted nonempty MMIO corpus')
            names={case['name'] for case in summary['cases']}
            c.require({'gpio-all-bits-set-clear-idempotence','all-natural-lanes-and-invalid-masks','gpio-effects-wait-for-response-and-stable-input-snapshot',
                'rollover-and-counter-snapshot-during-response-stall','auto-reload-and-match-wins-status-clear','count-write-suppresses-increment-and-match',
                'single-match-wins-w1c','compare-and-control-new-values-apply-next-edge','partial-count-write-merges-pre-increment-value','shared-reset-cancels-both-pending-effects',
                'no-response-consume-edge-replacement','seeded-parallel-held-requests-and-errors'}<=names,'Required MMIO/collision scenarios')
            c.require(any(e['kind']=='timer-write' and e['would_match'] and e['count_priority'] for e in summary['effects']) and
                any(e['kind']=='match' and e['clear_collision'] for e in summary['effects']),'Executable timer priority witnesses')
            vector=cwd/('seed_%d.txt'%seed);harness.atomic_text(vector,text)
            summary_path=cwd/('seed_%d_summary.json'%seed);harness.atomic(summary_path,summary)
            r,wave=simulate(cwd,vector,'seed_%d'%seed,seed)
            c.require(rtl_checks.successful(r,'MMIO_SIM_PASS seed=%d checked=%d'%(seed,count)),'Independent MMIO pre/post seed='+str(seed),r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Positive MMIO waveform')
            c.result['simulations'].append({'seed':seed,'checked_vectors':count,'vector_path':vector.relative_to(harness.ROOT).as_posix(),'vector_sha256':sha(vector),
                'waveform':wave.relative_to(harness.ROOT).as_posix(),'waveform_sha256':sha(wave)})
            c.result['seed_reports'].append({'seed':seed,'summary':summary_path.relative_to(harness.ROOT).as_posix()});artifacts[summary_path.relative_to(harness.ROOT).as_posix()]=sha(summary_path)
            if seed==1:first=text
        lines=first.splitlines();edge=next(n for n,line in enumerate(lines) if int(line.split()[27],16))
        wrong=lines[:edge+1];row=wrong[-1].split();row[27]='%x'%(int(row[27],16)^1);wrong[-1]=' '.join(row)
        for name,text,diagnostic in [('wrong-led-effect','\n'.join(wrong)+'\n','MMIO_MISMATCH'),('empty','','MMIO_EMPTY_VECTORS'),
                ('truncated',lines[0]+'\n0 1\n','MMIO_MALFORMED_VECTOR')]:
            vector=cwd/(name+'.txt');harness.atomic_text(vector,text);r,wave=simulate(cwd,vector,name);output=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'MMIO_SIM_PASS' not in output,'Actual MMIO negative '+name,r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Negative MMIO waveform')
            artifacts.update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (vector,wave)})
        mutations=[('gpio-set-toggle','rtl/peripherals/gpio.sv','SET:output_q<=output_q|(pending_data_q & pending_mask_q);','SET:output_q<=output_q^(pending_data_q & pending_mask_q);'),
            ('timer-clear-priority','rtl/peripherals/timer.sv',"if(match_event) matched_q<=1'b1;","if(match_event && !status_clear) matched_q<=1'b1;"),
            ('timer-count-priority','rtl/peripherals/timer.sv','increment==compare_q && !count_write','increment==compare_q')]
        for name,target,before,after in mutations:
            work=c.base/('mutation-'+name);work.mkdir();original=harness.inside(target).read_text();c.require(original.count(before)==1,'Unique mutation '+name)
            changed=work/target.split('/')[-1];harness.atomic_text(changed,original.replace(before,after))
            vector=work/'vectors.txt';harness.atomic_text(vector,first)
            r=c.vendor('xvlog',['--sv']+[str(changed if f==target else harness.inside(f)) for f in rtl+[tb]],work,15)
            c.require(rtl_checks.successful(r),'Actual mutant compile '+name,r)
            r=c.vendor('xelab',['work.tb_mmio','--snapshot','mmio','--timescale','1ns/1ps','--debug','typical'],work,30)
            c.require(rtl_checks.successful(r),'Actual mutant elaborate '+name,r)
            r,wave=simulate(work,vector,name);output=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and 'MMIO_MISMATCH' in output and 'MMIO_SIM_PASS' not in output,'Actual priority/SET fault detected '+name,r)
            for p in (changed,vector,wave):
                c.require(p.is_file() and p.stat().st_size>0,'Saved mutation artifact '+p.name);artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        c.result['artifacts']=artifacts
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'MMIO source bindings unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
