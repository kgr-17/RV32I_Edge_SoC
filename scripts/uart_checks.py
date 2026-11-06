#!/usr/bin/env python3
"""Real UART PHY/MMIO waveform comparison at fast and production divisors."""
import datetime as dt
import hashlib
import importlib.util
import json
import sys
import harness
import rtl_checks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c=rtl_checks.Checks('uart',task='T027',scope='TX serializer and TX-side local MMIO only; RX/SoC integration remains later')
    c.result['excluded']=['UART RX reception/flags','full SoC/compiled firmware execution','IRQ','formal','routed timing','hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest()
        sources=['rtl/peripherals/uart_tx.sv','rtl/peripherals/uart_mmio_tx.sv','dv/unit/tb_uart.sv','dv/unit/test_uart.py',
            'rtl/peripherals/uart_rx.sv','rtl/peripherals/uart_mmio.sv',
            'scripts/uart_checks.py','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py',
            '.harness/checks.json','config/rtl_checks.json','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources};c.versions(manifest)
        spec=importlib.util.spec_from_file_location('uart_reference',harness.inside('dv/unit/test_uart.py'))
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        cwd=c.base/'simulation'
        r=c.vendor('xvlog',['--sv']+[str(harness.inside(f)) for f in sources if f.endswith('.sv')],cwd,15)
        c.require(rtl_checks.successful(r),'Actual UART SystemVerilog compile',r)
        c.result['seed_reports']=[];artifacts={}
        for label,top,root,divider in [('fast','tb_uart','/tb_uart',4),('default','tb_uart_default','/tb_uart_default/body',868)]:
            snapshot='uart_'+label
            r=c.vendor('xelab',['work.'+top,'--snapshot',snapshot,'--timescale','1ns/1ps','--debug','typical'],cwd,30)
            c.require(rtl_checks.successful(r),'UART '+label+' elaboration',r)
            tcl=cwd/(label+'_run.tcl')
            signals=['clk','rst','reqv','reqr','addr','wr','data','be','rspr','rspv','rdata','err','tx','pe','pv','pdata','pr','pb','pt']
            harness.atomic_text(tcl,'log_wave '+' '.join(root+'/'+s for s in signals)+'\nrun all\nquit\n')
            artifacts[tcl.relative_to(harness.ROOT).as_posix()]=sha(tcl)
            def simulate(vector,seed,name):
                wave=cwd/(name+'.wdb')
                record=c.xsim([snapshot,'--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit','--sv_seed',str(seed),
                    '--testplusarg','SEED='+str(seed),'--testplusarg','DIV='+str(divider),'--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],cwd,30,name)
                return record,wave
            for seed in (1,20261106):
                text,summary=model.corpus(seed,divider)
                count=len(text.splitlines());c.require(count==summary['cycles'] and count>0,'Nonempty counted UART corpus '+label)
                if label=='fast':c.require(summary['mmio_completed_bytes']==list(range(256)) and summary['phy_completed_bytes']==list(range(256)),'All256 complete payloads through MMIO and direct PHY')
                names={case['name'] for case in summary['cases']}
                c.require({'effect-after-stalled-response','status-snapshot-across-frame-finish','disable-active-frame','lanes-reserved-readonly-and-unmapped','no-consume-edge-replacement','reset-cancels-pending-tx','reset-active-and-offered-traffic'}<=names,'Required UART transaction/reset scenarios present')
                vector=cwd/('%s_seed_%d.txt'%(label,seed));harness.atomic_text(vector,text)
                summary_path=cwd/('%s_seed_%d_summary.json'%(label,seed));harness.atomic(summary_path,summary)
                r,wave=simulate(vector,seed,'%s_seed_%d'%(label,seed))
                c.require(rtl_checks.successful(r,'UART_SIM_PASS div=%d seed=%d checked=%d'%(divider,seed,count)),'Independent pre/post UART waveform seed='+str(seed)+' '+label,r)
                c.require(wave.is_file() and wave.stat().st_size>0,'Positive UART waveform')
                c.result['simulations'].append({'variant':label,'divider':divider,'seed':seed,'checked_vectors':count,
                    'vector_path':vector.relative_to(harness.ROOT).as_posix(),'vector_sha256':sha(vector),
                    'waveform':wave.relative_to(harness.ROOT).as_posix(),'waveform_sha256':sha(wave)})
                artifacts[summary_path.relative_to(harness.ROOT).as_posix()]=sha(summary_path)
                c.result['seed_reports'].append({'variant':label,'seed':seed,'divider':divider,'cycles':count,
                    'requests':summary['requests'],'replies':summary['replies'],'errors':summary['errors'],'canceled':summary['canceled'],
                    'mmio_frames':len(summary['mmio_frames']),'phy_frames':len(summary['phy_frames']),
                    'summary':summary_path.relative_to(harness.ROOT).as_posix()})
            if label=='fast':
                first=model.corpus(1,divider)[0].splitlines()[0].split();first[22]='0'
                for name,text,diagnostic in [('wrong-expected',' '.join(first)+'\n','UART_MISMATCH'),('empty','','UART_EMPTY_VECTORS'),
                                             ('truncated',model.corpus(1,divider)[0].splitlines()[0]+'\n0 1\n','UART_MALFORMED_VECTOR')]:
                    vector=cwd/(name+'.txt');harness.atomic_text(vector,text);r,wave=simulate(vector,1,name)
                    output=r['stdout']+r['stderr']
                    c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'UART_SIM_PASS' not in output,'Actual UART negative '+name,r)
                    c.require(wave.is_file() and wave.stat().st_size>0,'Negative UART waveform')
                    artifacts.update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (vector,wave)})
        c.result['artifacts']=artifacts
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'UART sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
