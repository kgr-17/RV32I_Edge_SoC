#!/usr/bin/env python3
"""Fresh actual pipeline coverage with independent ISA comparison and gap report."""
from collections import Counter
import argparse
import datetime as dt
import hashlib
import json
import sys
import harness
import rtl_checks
from assertion_checks import property_hits
sys.path.insert(0,str(harness.ROOT))
from dv.coverage.coverage_report import parse_bins,summarize
from dv.reference.retire import stimulus_images,expected_trace,observed_trace,compare_trace


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit',choices=('coverage','stress'),default='coverage')
    unit=parser.parse_args().unit;prefix=unit.upper()
    c=rtl_checks.Checks('stress-report' if unit=='stress' else 'coverage-report',
        task='T022' if unit=='stress' else 'T021',scope='Finite matched-ISA families and actual simultaneous EX-stage hazard/backpressure crosses'+('; selected shared-reset windows' if unit=='stress' else ''))
    c.result['excluded']=['exhaustive operand/state/cross closure','code/toggle coverage','formal proof','in-flight reset closure','SoC/MMIO/interrupts','timing','physical hardware','ASIC']
    if unit=='stress':
        c.result['excluded'].remove('in-flight reset closure')
        c.result['excluded'].append('exhaustive reset timing/state-space closure')
    c.result['seed_reports']=[]
    code=1
    try:
        manifest=rtl_checks.load_manifest(); spec=manifest['unit_sims'][unit]
        files=list(dict.fromkeys(spec['sources']+spec.get('extra_inputs',[])+[spec['testbench'],spec['reference'],
            'dv/coverage/coverage_report.py','dv/reference/retire.py','scripts/coverage_checks.py',
            'scripts/unit_checks.py','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py',
            'config/rtl_checks.json','.harness/checks.json','docs/ARCH_CONTRACT.json']))
        c.result['source_sha256']={f:digest(harness.inside(f)) for f in files}
        c.versions(manifest)
        rec=c.command([sys.executable,'-B',str(harness.inside('scripts/unit_checks.py')),unit],c.base,120)
        c.require(rtl_checks.successful(rec),'Actual coverage-instrumented pipeline backend passes',rec)
        path=harness.inside(json.loads(rec['stdout'])['evidence']);backend=harness.read(path)
        c.require(backend['status']=='PASS' and [s['seed'] for s in backend['simulations']]==spec['seeds'],'Exact actual coverage seed set')
        c.result['backend']={'path':path.relative_to(harness.ROOT).as_posix(),'sha256':digest(path)}
        required=['op:'+name for name in harness.read(harness.inside('docs/ARCH_CONTRACT.json'))['isa']['instructions']]+['fault:%d'%n for n in range(1,10)]
        merged_bins=Counter();merged_isa=Counter()
        for sim in backend['simulations']:
            seed=sim['seed'];vectors=harness.inside(sim['vector_path'])
            c.require(digest(vectors)==sim['vector_sha256'],'Exact simulated coverage program seed='+str(seed))
            row=next(x for x in backend['checks'] if x['name']==unit+' independent comparison seed='+str(seed))
            rec=backend['commands'][row['command_index']]
            c.require(row['status']=='PASS' and rtl_checks.successful(rec),'Actual coverage producer seed='+str(seed))
            expected,isa,cases=expected_trace(stimulus_images(vectors.read_text(encoding='utf-8')))
            actual=observed_trace(rec['stdout'],prefix);compare_trace(actual,expected)
            c.require(True,'Independent ISA equality seed='+str(seed))
            resets=[]
            if unit=='stress':
                from dv.random.test_stress import reset_witnesses
                resets=reset_witnesses(rec['stdout'],seed)
                c.require(True,'All seven actual shared-reset windows seed='+str(seed))
            hits=property_hits(rec['stdout'].replace(prefix+'_PROPERTY_HITS','ASSERTIONS_PROPERTY_HITS'),seed,
                sim['coverage']['expected_retirements']+sum(x['pre_retired'] for x in resets))
            bins=parse_bins(rec['stdout'],seed);summary=summarize(bins,isa,required)
            c.require(True,'Actual reachable/excluded/mandatory coverage seed='+str(seed))
            corruptions=[('missing_bin',{k:v for k,v in bins.items() if k!=(0,0)},isa),
                ('hidden_excluded_hit',{**bins,(5,1):1},isa),
                ('missing_required_feature',{k:(0 if k[1]==1 else v) for k,v in bins.items()},isa),
                ('missing_required_opcode',bins,{**isa,required[0]:0})]
            rejections=[]
            for label,changed,ops in corruptions:
                try:summarize(changed,ops,required)
                except ValueError as exc:rejections.append({'case':label,'diagnostic':str(exc)})
                else:raise ValueError('Accepted injected coverage defect: '+label)
            c.require(len(rejections)==4,'Actual coverage report defects rejected seed='+str(seed))
            artifacts={}
            for label,value in (('observed',actual),('expected',expected),('coverage',summary)):
                p=c.base/(label+'_'+str(seed)+'.json');harness.atomic(p,value);artifacts[p.relative_to(harness.ROOT).as_posix()]=digest(p)
            c.result['seed_reports'].append({'seed':seed,'events':len(actual),'retirements':sum(x[0]=='R' for x in actual),
                'faults':sum(x[0]=='F' for x in actual),'counts':summary['counts'],'uncovered_crosses':summary['uncovered_crosses'],
                'assertion_witnesses':hits,'reset_witnesses':resets,'negative_rejections':rejections,'artifacts':artifacts})
            merged_bins.update(bins);merged_isa.update(isa);c.save()
        summary=summarize(merged_bins,merged_isa,required)
        if unit=='stress':
            from dv.random.test_stress import accept_reset_leak
            c.require(summary['counts']['uncovered']==0,'Stress hits all49 reachable bins in the finite T021 inventory')
            last=backend['simulations'][-1];cwd=harness.inside(last['vector_path']).parent;wave=c.base/'reset_leak.wdb'
            rec=c.xsim(['unit_snapshot','--tclbatch',str(harness.inside(backend['tcl']['path'])),'--onerror','quit','--onfinish','quit',
                '--sv_seed',str(last['seed']),'--testplusarg','SEED='+str(last['seed']),
                '--testplusarg','COUNT='+str(last['checked_vectors']),'--testplusarg','VECTORS='+str(harness.inside(last['vector_path'])),
                '--testplusarg','RESET_LEAK=1','--log',str(c.base/'reset_leak.log'),'--wdb',str(wave)],cwd,30,'reset_leak')
            c.require(accept_reset_leak(rec),'Actual reset retention checker rejects injected fabric-model memory leak',rec)
            c.require(wave.is_file() and wave.stat().st_size>0,'Injected reset leak waveform')
            c.result['artifacts']={wave.relative_to(harness.ROOT).as_posix():digest(wave)}
        report=harness.inside('evidence/coverage/'+harness.today()+'_'+c.result['started_utc']+'.json')
        harness.atomic(report,{'task':'T022' if unit=='stress' else 'T021','scope':c.result['scope'],'seeds':spec['seeds'],'aggregate':summary,
            'seed_reports':c.result['seed_reports'],'backend':c.result['backend'],'source_sha256':c.result['source_sha256'],
            'interpretation':'EX counters count simultaneous sampled edges, including held/killed work. ISA bins require exact whole-trace ISS equality. Remaining reachable crosses are coverage gaps, never exclusions or proof.'})
        c.result['coverage_report']={'path':report.relative_to(harness.ROOT).as_posix(),'sha256':digest(report)}
        c.result['aggregate_counts']=summary['counts']
        c.require(all(digest(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'All coverage sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:
        c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,TypeError,harness.Stop,StopIteration) as exc:
        c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),
        'coverage_report':c.result.get('coverage_report'),'counts':c.result.get('aggregate_counts'),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
