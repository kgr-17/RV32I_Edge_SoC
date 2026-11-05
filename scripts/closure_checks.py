#!/usr/bin/env python3
"""Bind a DV review to this attempt's real gates; never reuse an older pass."""
from collections import Counter
import datetime as dt
import hashlib
import json
import sys
import harness
import rtl_checks

PROFILES={'lint','regress','decode','alu','regfile','branch','lsu','memory-model','core','retire',
    'pipeline','pipeline-iss','forwarding','hazard','load_use','control','backpressure',
    'isa_complete','isa-complete','isa-matrix','random','random-iss','assertions',
    'coverage','coverage-report','stress','stress-report'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def passed_prefix(records,commands):
    resolved=[[sys.executable if word=='{python}' else word for word in cmd] for cmd in commands]
    if len(records)!=len(resolved):raise ValueError('Missing/extra current-attempt gate records')
    for record,command in zip(records,resolved):
        if record['argv']!=command or record['status']!='PASS' or record['exit_code']!=0:
            raise ValueError('Current-attempt gate missing/failed/NOT RUN or reordered')


def metadata_objects(text):
    if not text.strip():return []
    try:return [json.loads(text)]
    except json.JSONDecodeError:
        result=[]
        for line in text.splitlines():
            try:result.append(json.loads(line))
            except json.JSONDecodeError:continue
        return result


def validate_tool(run,since,pins,digest):
    if run.get('profile')=='memory-model':
        if (run['status']!='PASS' or run['exit_code']!=0 or run['tests']!=11 or
                any(run[key]!=0 for key in ('failures','errors','skipped')) or run['source_drift'] or
                set(run['directed_defects_rejected'])!={'EarlyStore','MovingSnapshot','ReplacementAcceptance','IgnoredReset'} or
                len(run['stress'])!=12):
            raise ValueError('Incomplete/failed Python memory-model evidence')
        started=run['stamp']
    else:
        if run['status']!='PASS' or not run.get('checks') or any(x['status']!='PASS' for x in run['checks']):
            raise ValueError('Referenced actual tool receipt failed or has no successful checks')
        started=run['started_utc']
    stamp=dt.datetime.strptime(started,'%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc)
    if stamp<since:raise ValueError('Stale tool receipt predates current T024 attempt')
    for key,value in run.get('pins',{}).items():
        if key in pins and value!=pins[key]:raise ValueError('Tool pin mismatch: '+key)
    for name,value in run.get('source_sha256',{}).items():
        if digest(name)!=value:raise ValueError('Tool source changed: '+name)


def main():
    c=rtl_checks.Checks('dv-closure',task='T024',scope='Simulation DV closure review, with explicit owner-skipped formal exception')
    c.result['excluded']=['formal proof (T023 owner-skipped)','RISC-V certification','exhaustive operand/state/reset/coverage proof','SoC/MMIO','IRQ/CSR revision','routed timing','physical FPGA','ASIC']
    code=1
    try:
        plan,state=harness.load();task=next(t for t in plan['tasks'] if t['id']=='T024')
        c.require(state['active']=='T024' and state['task_states']['T024']=='in_progress','Current active T024 verification attempt')
        journal_path=harness.inside(state['receipts']['T024']);journal=harness.read(journal_path)
        c.require(journal['task']=='T024' and journal['attempt']==state['attempts']['T024'] and journal['stage']=='running','Authoritative current-attempt journal, no fallback')
        prior=task['verification_commands'][:-1]
        if task['verification_commands'][-1]!=['{python}','-B','scripts/verify.py','test-dv-closure']:
            raise ValueError('Closure gate must follow all required current-attempt gates')
        passed_prefix(journal['commands'],prior)
        c.require(True,'All earlier current-attempt gate argv/order/exits pass')
        prefix=json.dumps(journal['commands'],sort_keys=True,separators=(',',':')).encode()
        c.result['attempt_binding']={'path':state['receipts']['T024'],'attempt':journal['attempt'],
            'completed_prefix_sha256':hashlib.sha256(prefix).hexdigest(),'completed_commands':len(prior),
            'base_commit':journal['git_commit']}
        registry=harness.read(harness.inside('.harness/checks.json'))
        regression=next(row for row in journal['commands'] if row['argv'][-1]=='regress')
        rows=metadata_objects(regression['stdout']);passed_prefix(rows,registry['regress']['commands'])
        c.require(len(rows)==19,'All19 actual regression subcommands executed and passed')
        since=dt.datetime.fromisoformat(journal['commands'][0]['started_utc'])
        manifest=rtl_checks.load_manifest();pins={key:value for key,value in manifest.items() if key.endswith('_version') or key=='vivado_sw_build'}
        sources={};artifacts={};tools={}

        def check_artifact(name,value):
            path=harness.inside(name)
            if sha(path)!=value:raise ValueError('Artifact hash mismatch: '+name)
            artifacts[path.relative_to(harness.ROOT).as_posix()]=value

        def tool(name):
            name=name.replace('\\','/')
            if not name.startswith('evidence/toolchain_runs/') or not name.endswith('.json'):
                raise ValueError('Unregistered tool evidence path')
            if name in tools:return
            path=harness.inside(name);run=harness.read(path)
            validate_tool(run,since,pins,lambda f:sha(harness.inside(f)))
            tools[name]=run
            sources.update(run.get('source_sha256',{}))
            visit(run)

        def visit(obj):
            if isinstance(obj,list):
                for value in obj:visit(value)
            elif isinstance(obj,dict):
                if isinstance(obj.get('evidence'),str):tool(obj['evidence'])
                if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):
                    check_artifact(obj['path'],obj['sha256'])
                    if obj['path'].replace('\\','/').startswith('evidence/toolchain_runs/'):tool(obj['path'])
                for name,value in obj.get('artifacts',{}).items():check_artifact(name,value)
                for key in ('vector','waveform'):
                    if key+'_sha256' in obj:check_artifact(obj.get(key+'_path',obj.get(key)),obj[key+'_sha256'])
                if isinstance(obj.get('stdout'),str):
                    for value in metadata_objects(obj['stdout']):visit(value)
                for key,value in obj.items():
                    if key!='stdout' and isinstance(value,(dict,list)):visit(value)

        visit(journal['commands'])
        counts=Counter(run['profile'] for run in tools.values())
        c.require(PROFILES<=set(counts),'All required real tool profiles present, missing='+str(sorted(PROFILES-set(counts))))
        c.require(counts['coverage-report']>=2,'Both regression and explicit coverage gate bound')
        c.require(state['task_states']['T023']=='skipped' and set(state.get('owner_skips',{}))=={'T023'},'Only explicitly owner-skipped T023 exception')
        owner=state['owner_skips']['T023'];harness.skip_authority(plan,state,next(t for t in plan['tasks'] if t['id']=='T023'),owner)
        c.result['formal_disposition']={'status':'OWNER-SKIPPED','verification':'NOT RUN','proof':False,'owner_evidence':owner,
            'preserved_receipt':state['receipts']['T023'],'preserved_attempts':state['attempts']['T023']}
        c.require(all(state['task_states'][tid]=='completed' for tid in [*('T%03d'%n for n in range(1,23)),'T041']),
            'All preceding simulation milestones completed; owner reviews retained')
        summary={}
        for profile,seed_count,total in [('pipeline-iss',4,2008),('isa-complete',4,6364),('random-iss',6,14458)]:
            runs=[run for run in tools.values() if run['profile']==profile]
            for run in runs:
                c.require(len(run['comparisons'])==seed_count and sum(x['retirements'] for x in run['comparisons'])==total,'Exact scoped comparison totals '+profile)
            summary[profile]={'seeds':seed_count,'retirements':total,'executions':len(runs)}
        assertions=[run for run in tools.values() if run['profile']=='assertions' and 'property_runs' in run]
        c.require(bool(assertions) and all(len(run['property_runs'])==6 and len(run['injections'])==16 for run in assertions),'Actual assertion witnesses and16 intended violations')
        stress=[run for run in tools.values() if run['profile']=='stress-report']
        c.require(bool(stress),'Actual stress comparison present')
        for run in stress:
            windows=[r for seed in run['seed_reports'] for r in seed['reset_witnesses']]
            c.require(len(windows)==28 and sum(x['pre_retired'] for x in windows)==52 and
                sum(x['retirements'] for x in run['seed_reports'])==9840 and
                run['aggregate_counts']==dict(matrix=64,reachable=49,hit=49,uncovered=0,excluded=15),
                'Selected reset windows, main9840R and finite49/49 stress inventory')
        summary['stress']={'seeds':4,'main_retirements':9840,'pre_reset_retirements':52,'reset_windows':28,
            'coverage':stress[-1]['aggregate_counts'],'scope':'CPU plus fabric model, finite selected windows'}
        for f in ['scripts/closure_checks.py','scripts/test_closure_checks.py','scripts/harness.py','scripts/test_harness.py',
                  '.harness/checks.json','config/rtl_checks.json','docs/ARCH_CONTRACT.json',owner['evidence']]:sources[f]=sha(harness.inside(f))
        c.result.update(source_sha256=sources,pins=pins,summary=summary,artifacts=artifacts,
            tool_receipts={name:sha(harness.inside(name)) for name in tools},profile_counts=dict(sorted(counts.items())))
        c.require(all(sha(harness.inside(f))==h for f,h in sources.items()),'All collected simulation and policy sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:
        c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,TypeError,OSError,AssertionError,harness.Stop,StopIteration) as exc:
        c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),
        'summary':c.result.get('summary'),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
