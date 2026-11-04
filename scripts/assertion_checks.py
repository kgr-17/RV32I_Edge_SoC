#!/usr/bin/env python3
"""Actual pipeline assertions plus isolated, attributable assertion violations."""
import datetime as dt
import hashlib
import json
import re
import sys
import harness
import rtl_checks

NEGATIVES = {1:'P_X0_A', 2:'P_X0_B', 3:'P_RETIRE_ORDER', 4:'P_RESET_QUIET',
             5:'P_RESET_STATE', 6:'P_I_STABLE', 7:'P_D_STABLE', 8:'P_I_STABLE',
             9:'P_D_STABLE', 10:'P_FAULT_STICKY', 11:'P_FAULT_STICKY',
             12:'P_RETIRE_DEST', 13:'P_I_RESPONSE', 14:'P_D_RESPONSE',
             15:'P_I_SINGLE', 16:'P_D_SINGLE'}
HITS = ('resets','x0_a','x0_b','retires','i_holds','d_holds','faults','i_requests','d_requests')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accept_injection(record, property_id):
    text = record['stdout'] + '\n' + record['stderr']
    ids = re.findall(r'CORE_ASSERT_FAIL (P_[A-Z_0-9]+)', text)
    return (record['status'] in ('PASS','FAIL') and record['exit_code'] in (0,1) and ids == [property_id]
            and not re.search(r'(?im)^\s*(?:ERROR:|WARNING:)', text)
            and 'PROPERTY_CONTROL_PASS' not in text
            and 'Injection was not detected' not in text)


def property_hits(text, seed, expected_retires):
    pattern = r'^ASSERTIONS_PROPERTY_HITS seed=' + str(seed) + ''.join(r' '+key+r'=(\d+)' for key in HITS) + r'$'
    rows = re.findall(pattern, text, re.M)
    if len(rows)!=1:
        raise ValueError('Missing/duplicate actual property witnesses')
    result = dict(zip(HITS,map(int,rows[0])))
    if any(value<=0 for value in result.values()) or result['retires']!=expected_retires:
        raise ValueError('Vacuous/wrong actual property witnesses')
    return result


def main():
    checks = rtl_checks.Checks('assertions',task='T020',scope='Clocked immediate SV assertions on actual pipeline plus isolated negative monitor simulations')
    checks.result['excluded'] = ['concurrent SVA engine','formal proof','exhaustive coverage','in-flight reset closure','routed timing','physical hardware','ASIC']
    checks.result['property_runs'] = []
    checks.result['injections'] = []
    code=1
    try:
        manifest=rtl_checks.load_manifest(); spec=manifest['unit_sims']['assertions']
        inputs=list(dict.fromkeys(spec['sources']+spec.get('extra_inputs',[])+[spec['reference'],spec['testbench'],
            'dv/assertions/tb_property_negative.sv','scripts/assertion_checks.py','scripts/unit_checks.py',
            'scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py','config/rtl_checks.json','.harness/checks.json','docs/ARCH_CONTRACT.json']))
        checks.result['source_sha256']={f:digest(harness.inside(f)) for f in inputs}
        checks.versions(manifest)
        record=checks.command([sys.executable,'-B',str(harness.inside('scripts/unit_checks.py')),'assertions'],checks.base,120)
        checks.require(rtl_checks.successful(record),'Actual assertion-instrumented pipeline backend passes',record)
        path=harness.inside(json.loads(record['stdout'])['evidence']); run=harness.read(path)
        checks.require(run['status']=='PASS' and [s['seed'] for s in run['simulations']]==spec['seeds'],'Exact actual assertion seed set')
        checks.result['backend']={'path':path.relative_to(harness.ROOT).as_posix(),'sha256':digest(path)}
        for sim in run['simulations']:
            seed=sim['seed']; row=next(x for x in run['checks'] if x['name']=='assertions independent comparison seed='+str(seed))
            actual=run['commands'][row['command_index']]
            checks.require(row['status']=='PASS' and rtl_checks.successful(actual),'Actual instrumented trace producer seed='+str(seed))
            hits=property_hits(actual['stdout'],seed,sim['coverage']['expected_retirements'])
            checks.require(True,'Nonvacuous actual property witnesses seed='+str(seed))
            checks.result['property_runs'].append({'seed':seed,**hits})
        cwd=checks.base/'monitor_negative'; tcl=cwd/'run.tcl'
        harness.atomic_text(tcl,'log_wave /tb_property_negative/clk_i /tb_property_negative/rst_i /tb_property_negative/monitor/expected_order_q\nrun all\nquit\n')
        checks.result['tcl']={'path':tcl.relative_to(harness.ROOT).as_posix(),'sha256':digest(tcl)}
        record=checks.vendor('xvlog',['--sv',str(harness.inside('dv/assertions/core_properties.sv')),
            str(harness.inside('dv/assertions/tb_property_negative.sv'))],cwd,15)
        checks.require(rtl_checks.successful(record),'Isolated assertion monitor compile',record)
        record=checks.vendor('xelab',['work.tb_property_negative','--snapshot','property_snapshot','--timescale','1ns/1ps','--debug','typical'],cwd,30)
        checks.require(rtl_checks.successful(record),'Isolated assertion monitor elaboration',record)
        for injection in [0]+list(NEGATIVES):
            label='inject_'+str(injection); wave=cwd/(label+'.wdb')
            record=checks.xsim(['property_snapshot','--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit',
                '--sv_seed','7','--testplusarg','INJECT='+str(injection),'--log',label+'.log','--wdb',str(wave)],cwd,10,label)
            if injection==0:
                checks.require(rtl_checks.successful(record,'PROPERTY_CONTROL_PASS'),'Isolated legal control passes',record)
            else:
                prop=NEGATIVES[injection]
                checks.require(accept_injection(record,prop),'Isolated violation '+str(injection)+' detected by '+prop,record)
                checks.result['injections'].append({'injection':injection,'property':prop,'command_index':len(checks.result['commands'])-1})
            checks.require(wave.is_file() and wave.stat().st_size>0,'Isolated monitor waveform '+str(injection))
            checks.result.setdefault('artifacts',{})[wave.relative_to(harness.ROOT).as_posix()]=digest(wave)
        checks.require(all(digest(harness.inside(f))==h for f,h in checks.result['source_sha256'].items()),'All assertion inputs unchanged')
        checks.result['status']='PASS'; code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:
        checks.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,TypeError,harness.Stop,StopIteration) as exc:
        checks.result.update(status='FAIL',error=str(exc))
    checks.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();checks.save()
    print(json.dumps({'status':checks.result['status'],'evidence':checks.path.relative_to(harness.ROOT).as_posix(),
        'injections':len(checks.result['injections']),'error':checks.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
