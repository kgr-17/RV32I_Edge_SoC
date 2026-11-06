#!/usr/bin/env python3
"""Real combined-UART comparisons, collision mutations and synchronizer inspection."""
import datetime as dt
import hashlib
import importlib.util
import json
import sys
import harness
import rtl_checks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c=rtl_checks.Checks('uart-rx',task='T042',scope='Digital UART RX/TX MMIO, sampling and actual two-stage synthesis chain; no analog metastability claim')
    c.result['excluded']=['analog metastability/MTBF','complete SoC','full regression','formal','routed timing','hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest()
        rtl=['rtl/peripherals/uart_tx.sv','rtl/peripherals/uart_rx.sv','rtl/peripherals/uart_mmio.sv']
        tb='dv/unit/tb_uart_rx.sv'
        sources=rtl+[tb,'dv/unit/test_uart_rx.py','dv/unit/test_uart.py','dv/lint/uart_full_lint_top.sv',
            'scripts/uart_rx_checks.py','scripts/uart_rx_structure.tcl','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py',
            '.harness/checks.json','config/rtl_checks.json','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources};c.versions(manifest)
        sys.path.insert(0,str(harness.inside('dv/unit')))
        spec=importlib.util.spec_from_file_location('receiver_reference',harness.inside('dv/unit/test_uart_rx.py'))
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        cwd=c.base/'simulation';artifacts={};c.result['seed_reports']=[]
        r=c.vendor('xvlog',['--sv']+[str(harness.inside(f)) for f in rtl+[tb]],cwd,15)
        c.require(rtl_checks.successful(r),'Combined UART actual SystemVerilog compile',r)
        fast_text=None;fast_summary=None
        for label,top,root,divider in [('fast','tb_uart_rx','/tb_uart_rx',8),('odd','tb_uart_rx_odd','/tb_uart_rx_odd/body',7),('default','tb_uart_rx_default','/tb_uart_rx_default/body',868)]:
            snapshot='uart_rx_'+label
            r=c.vendor('xelab',['work.'+top,'--snapshot',snapshot,'--timescale','1ns/1ps','--debug','typical'],cwd,30)
            c.require(rtl_checks.successful(r),'RX '+label+' elaboration',r)
            tcl=cwd/(label+'_run.tcl')
            signals=['clk','rst','rx','reqv','reqr','addr','wr','data','be','rspr','rspv','rdata','err','tx','pe','received','rbyte','frame_error','busy']
            harness.atomic_text(tcl,'log_wave '+' '.join(root+'/'+s for s in signals)+'\nrun all\nquit\n')
            artifacts[tcl.relative_to(harness.ROOT).as_posix()]=sha(tcl)
            def simulate(vector,seed,name,work=cwd,snap=snapshot,tcl_path=tcl):
                wave=work/(name+'.wdb')
                record=c.xsim([snap,'--tclbatch',str(tcl_path),'--onerror','quit','--onfinish','quit','--sv_seed',str(seed),
                    '--testplusarg','SEED='+str(seed),'--testplusarg','DIV='+str(divider),'--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],work,45,name)
                return record,wave
            for seed in (1,20261106):
                text,summary=model.corpus(seed,divider);count=len(text.splitlines())
                c.require(count==summary['cycles'] and count>0,'Nonempty counted RX corpus '+label)
                if label=='fast':c.require(summary['completed_rx_bytes']==list(range(256)),'All256 good RX payloads')
                c.require(summary['phases']==[0,1,2,3] and summary['false_starts']>0 and summary['partial_aborts']>=10,'Async phases/false start/reset coverage')
                names={case['name'] for case in summary['cases']}
                c.require({'bad-stop-break-and-recovery','overrun-retains-old-and-high-lane-does-not-pop','read-snapshot-held-while-new-frame-overruns',
                    'empty-read-cannot-consume-later-byte','consume-and-receive-keeps-new','new-overrun-wins-w1c','new-frame-error-wins-w1c',
                    'disable-aborts-partial','completed-byte-survives-disable','reset-in-start-data-stop','seeded-full-duplex'}<=names,'Required RX scenarios')
                vector=cwd/('%s_seed_%d.txt'%(label,seed));harness.atomic_text(vector,text)
                summary_path=cwd/('%s_seed_%d_summary.json'%(label,seed));harness.atomic(summary_path,summary)
                r,wave=simulate(vector,seed,'%s_seed_%d'%(label,seed))
                c.require(rtl_checks.successful(r,'UART_RX_SIM_PASS div=%d seed=%d checked=%d'%(divider,seed,count)),'Independent RX pre/post seed=%d %s'%(seed,label),r)
                c.require(wave.is_file() and wave.stat().st_size>0,'Actual RX waveform')
                c.result['simulations'].append({'variant':label,'divider':divider,'seed':seed,'checked_vectors':count,
                    'vector_path':vector.relative_to(harness.ROOT).as_posix(),'vector_sha256':sha(vector),
                    'waveform':wave.relative_to(harness.ROOT).as_posix(),'waveform_sha256':sha(wave)})
                artifacts[summary_path.relative_to(harness.ROOT).as_posix()]=sha(summary_path)
                c.result['seed_reports'].append({'variant':label,'seed':seed,'cycles':count,'summary':summary_path.relative_to(harness.ROOT).as_posix()})
                if label=='fast' and seed==1:fast_text=text;fast_summary=summary
            if label=='fast':
                lines=fast_text.splitlines();index=next(i for i,line in enumerate(lines) if int(line.split()[24],16))
                wrong=lines[:index+1];row=wrong[-1].split();row[25]='%x'%(int(row[25],16)^1);wrong[-1]=' '.join(row)
                for name,text,diagnostic in [('wrong-received-byte','\n'.join(wrong)+'\n','UART_RX_MISMATCH'),('empty','','UART_RX_EMPTY_VECTORS'),
                        ('truncated',lines[0]+'\n0 1\n','UART_RX_MALFORMED_VECTOR')]:
                    vector=cwd/(name+'.txt');harness.atomic_text(vector,text);r,wave=simulate(vector,1,name);output=r['stdout']+r['stderr']
                    c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'UART_RX_SIM_PASS' not in output,'Actual RX negative '+name,r)
                    c.require(wave.is_file() and wave.stat().st_size>0,'Actual negative waveform')
                    artifacts.update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (vector,wave)})
        # Test meaningful RTL faults in isolated working directories. Production
        # sources stay intact; exactly the intended collision must detect each.
        original=harness.inside('rtl/peripherals/uart_mmio.sv').read_text()
        mutations=[('pop-priority','if(!full_q || pop)','if(!full_q)',next(e['cycle'] for e in fast_summary['effects'] if e['kind']=='replace')),
            ('frame-clear-priority',"if(frame_event) frame_q<=1'b1;","if(frame_event && !clear_frame) frame_q<=1'b1;",next(e['cycle'] for e in fast_summary['effects'] if e['kind']=='frame-error' and e['clear']&2))]
        for name,before,after,edge in mutations:
            work=c.base/('mutation-'+name);work.mkdir();changed=work/'uart_mmio.sv'
            c.require(original.count(before)==1,'Unique isolated mutation '+name)
            harness.atomic_text(changed,original.replace(before,after))
            vector=work/'vectors.txt';harness.atomic_text(vector,'\n'.join(fast_text.splitlines()[:edge+8])+'\n')
            r=c.vendor('xvlog',['--sv']+[str(changed if f.endswith('/uart_mmio.sv') else harness.inside(f)) for f in rtl+[tb]],work,15)
            c.require(rtl_checks.successful(r),'Actual mutant compile '+name,r)
            r=c.vendor('xelab',['work.tb_uart_rx','--snapshot','mutant','--timescale','1ns/1ps','--debug','typical'],work,30)
            c.require(rtl_checks.successful(r),'Actual mutant elaborate '+name,r)
            tcl=work/'run.tcl';harness.atomic_text(tcl,'log_wave /tb_uart_rx/rspv /tb_uart_rx/rdata /tb_uart_rx/rx\nrun all\nquit\n')
            # Use local definition, avoiding the last default-divider closure.
            wave=work/'mutation.wdb'
            r=c.xsim(['mutant','--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit','--testplusarg','SEED=1','--testplusarg','DIV=8',
                '--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],work,45,name)
            output=r['stdout']+r['stderr']
            # Collision affects internal state at edge, next accepted STATUS/RX
            # request exposes it within the deliberately retained next8 rows.
            c.require(r['status'] in ('PASS','FAIL') and 'UART_RX_MISMATCH' in output and 'UART_RX_SIM_PASS' not in output,'Actual collision mutation detected '+name,r)
            for p in (changed,vector,tcl,wave):
                c.require(p.is_file() and p.stat().st_size>0,'Saved mutation artifact '+p.name)
                artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        work=c.base/'synchronizer';work.mkdir();source_file=work/'sources.txt'
        harness.atomic_text(source_file,'\n'.join(str(harness.inside(f)) for f in rtl+['dv/lint/uart_full_lint_top.sv'])+'\n')
        r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('scripts/uart_rx_structure.tcl')),
            '-tclargs',str(source_file)],work,60)
        c.require(rtl_checks.successful(r,'UART_RX_SYNC_PASS stages=2 fanout=1 clock=common'),'Actual synthesized ASYNC_REG chain/first-stage isolation',r)
        for p in (source_file,work/'synchronizer.txt'):artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        c.result['artifacts']=artifacts
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'RX source bindings unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
