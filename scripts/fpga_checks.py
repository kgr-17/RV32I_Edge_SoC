"""Current-attempt full-SoC FPGA gates; physical programming is excluded."""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
import closure_checks
import fpga_build
import fpga_reports
import harness
import rtl_checks

STEPS={'synth':0,'impl':1,'reports':2}
NAMES=['vivado-synth','vivado-impl','fpga-reports']
RTL_CHECKS=['lint','test-interrupts','regress']
PHYSICAL_STEPS=[('opt','optimized.dcp'),('place','placed.dcp'),('phys_fanout','fanout.dcp'),
    ('phys_placement','placement_opt.dcp'),('phys_logic','logic_opt.dcp'),('phys_pin','pin_opt.dcp'),('route','routed.dcp')]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return Path(path).relative_to(harness.ROOT).as_posix()
def native_success(command,marker):
    return rtl_checks.successful(command,marker) and not re.search(r'(?im)^\s*CRITICAL WARNING:',command['stdout']+'\n'+command['stderr'])


def context(stage):
    plan,state=harness.load();config=fpga_build.load_config();fpga_build.check_execution(config,state)
    journal_name=state['receipts'].get('T043')
    if not journal_name:raise rtl_checks.NotRun('Current T043 finish journal required')
    journal=harness.read(harness.inside(journal_name));index=len(RTL_CHECKS)+STEPS[stage]
    if journal['stage']!='running' or journal['attempt']!=state['attempts']['T043'] or journal['task']!='T043':
        raise ValueError('FPGA_CURRENT_ATTEMPT_REQUIRED')
    task=next(t for t in plan['tasks'] if t['id']=='T043')
    assert task['verification_commands']==[['{python}','-B','scripts/verify.py',n] for n in RTL_CHECKS+NAMES]
    closure_checks.passed_prefix(journal['commands'],task['verification_commands'][:index])
    authority='evidence/owner_reviews/T043-2026-11-07-authorization.json'
    owner=harness.read(harness.inside(authority))
    if owner['owner_answer']!='Authorize T043 and that command' or owner['physical_programming_authorized']:
        raise ValueError('FPGA_EXPLICIT_OWNER_AUTHORITY')
    if sha(harness.inside('docs/FPGA_EXECUTION_REVIEW.md'))!=owner['review_document_sha256']:
        raise ValueError('FPGA_OWNER_REVIEW_DOCUMENT_DRIFT')
    names=[fpga_build.CONFIG,'fpga/basys3/build.tcl','scripts/fpga_build.py','scripts/fpga_reports.py',
        'scripts/fpga_checks.py','scripts/test_fpga_build.py','scripts/test_fpga_reports.py','scripts/test_fpga_checks.py',
        'dv/fpga/fixtures/manifest.json','dv/fpga/fixtures/reports.zip',
        'dv/fpga/fixtures/routed_manifest.json','dv/fpga/fixtures/routed_reports.zip','scripts/tool_runner.py',
        'scripts/tool_child.py','scripts/harness.py','scripts/rtl_checks.py','scripts/closure_checks.py',
        'scripts/verify.py','.harness/checks.json','docs/ARCH_CONTRACT.json','docs/INTERRUPT_CONTRACT.json',
        'docs/INTERRUPT_SPEC.md','config/basys3_pins.json','config/vivado_vendor_collateral.json',authority]+config['rtl_sources']+config['constraints']+config['memory_files']
    return config,state,journal,journal_name,{n:sha(harness.inside(n)) for n in dict.fromkeys(names)}


def prior_tool(journal,index,profile,journal_name):
    def links(obj):
        if isinstance(obj,list):
            for value in obj:yield from links(value)
        elif isinstance(obj,dict):
            if isinstance(obj.get('evidence'),str):yield obj['evidence']
            if isinstance(obj.get('stdout'),str):
                yield from links(closure_checks.metadata_objects(obj['stdout']))
    found=list(links(closure_checks.metadata_objects(journal['commands'][index]['stdout'])))
    if len(found)!=1:raise ValueError('FPGA_PRIOR_RECEIPT_SHAPE')
    path=harness.inside(found[0])
    if path.parent!=harness.inside('evidence/toolchain_runs') or not path.name.startswith(profile+'-') or path.suffix!='.json':
        raise ValueError('FPGA_PRIOR_RECEIPT_LOCATION')
    run=harness.read(path)
    if run['profile']!=profile or run['status']!='PASS' or not run['checks'] or any(x['status']!='PASS' for x in run['checks']):
        raise ValueError('FPGA_PRIOR_GATE_NOT_PASS')
    if run.get('attempt')!=journal['attempt'] or run.get('attempt_journal')!=journal_name or run['base_commit']!=journal['git_commit']:
        raise ValueError('FPGA_PRIOR_ATTEMPT_DRIFT')
    started=dt.datetime.strptime(run['started_utc'],'%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc)
    if started<dt.datetime.fromisoformat(journal['commands'][0]['started_utc']):
        raise ValueError('FPGA_STALE_PRIOR_RECEIPT')
    if any(sha(harness.inside(n))!=h for n,h in run['source_sha256'].items()):raise ValueError('FPGA_PRIOR_SOURCE_DRIFT')
    for n,h in run['artifacts'].items():
        if sha(harness.inside(n))!=h:raise ValueError('FPGA_PRIOR_ARTIFACT_DRIFT '+n)
    return path,run


def run_stage(c,stage,checkpoint=None):
    folder=c.base/stage
    job,binding=fpga_build.prepare_job(folder,mode='execute',stage=stage,checkpoint=checkpoint)
    result=fpga_build.run_job(job,binding)
    c.result['commands'].append(result['command']);c.result.setdefault('jobs',[]).append(
        {'stage':stage,'result':rel(folder/'result.json'),'result_sha256':sha(folder/'result.json'),
         'job':rel(job),'job_sha256':sha(job),'source_sha256':result['source_sha256'],'output':result['output']})
    c.save()
    c.require(result['inputs_unchanged'],'Exact inputs unchanged '+stage)
    c.require(native_success(result['command'],'FPGA_BUILD_EXECUTION_PASS stage='+stage),
        'Native full-design stage completed without diagnostics '+stage,result['command'])
    return harness.inside(result['output'])


def artifacts(c):
    found={}
    for job in c.result.get('jobs',[]):
        for n in [job['job'],job['result']]:found[n]=sha(harness.inside(n))
        directory=harness.inside(job['output'])
        if directory.exists():
            for p in directory.iterdir():
                if p.is_file():found[rel(p)]=sha(p)
    return found


def validate_chain(run,stages,initial_checkpoint=None):
    if [j['stage'] for j in run['jobs']]!=stages or len(run['commands'])!=len(stages):
        raise ValueError('FPGA_NATIVE_STAGE_INVENTORY')
    previous=initial_checkpoint
    names=dict(PHYSICAL_STEPS,synth='synthesis.dcp',physopt='physopt.dcp',reports='routed.dcp')
    for item,command in zip(run['jobs'],run['commands']):
        p=harness.inside(item['result']);native=harness.read(p)
        if sha(p)!=item['result_sha256'] or native['command']!=command or native['mode']!='execute' or native['stage']!=item['stage'] or not native['inputs_unchanged']:
            raise ValueError('FPGA_NATIVE_STAGE_BINDING')
        if not native_success(command,'FPGA_BUILD_EXECUTION_PASS stage='+item['stage']):
            raise ValueError('FPGA_NATIVE_STAGE_FAILED')
        if any(sha(harness.inside(n))!=h for n,h in native['source_sha256'].items()):
            raise ValueError('FPGA_NATIVE_STAGE_INPUT_DRIFT')
        job=harness.inside(item['job'])
        if sha(job)!=item['job_sha256'] or sha(job)!=native['job_sha256']:raise ValueError('FPGA_JOB_DRIFT')
        rows=dict(line.split('\t') for line in job.read_text().splitlines() if line.split('\t')[0] not in ('source','memory','constraint'))
        if rows['mode']!='execute' or rows['stage']!=item['stage']:raise ValueError('FPGA_JOB_MODE')
        if previous is None:
            if rows['checkpoint']!='':raise ValueError('FPGA_SYNTHESIS_REUSED_CHECKPOINT')
        else:
            predecessor=fpga_build.project_path(rows['checkpoint'])
            if predecessor!=previous or native['source_sha256'].get(rel(previous))!=sha(previous):
                raise ValueError('FPGA_CHECKPOINT_CHAIN')
        previous=harness.inside(native['output'])/names[item['stage']]
        if not previous.is_file() or run['artifacts'].get(rel(previous))!=sha(previous):raise ValueError('FPGA_CHECKPOINT_UNBOUND')
    return previous


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=STEPS);args=parser.parse_args()
    c=rtl_checks.Checks('fpga-'+args.stage,task='T043',scope='Actual full integrated SoC '+args.stage+' and current-attempt input/checkpoint/report bindings')
    c.result['excluded']=['physical FPGA programming/measurement','ASIC','formal T023 owner-skipped/NOT RUN','off-chip synchronous I/O timing contract']
    code=1
    try:
        config,state,journal,journal_name,sources=context(args.stage)
        c.result.update(source_sha256=sources,attempt=journal['attempt'],attempt_journal=journal_name,
            pins={'vivado_version':config['vivado_version'],'vivado_sw_build':config['vivado_sw_build']})
        c.require(True,'Explicit owner-authorized active task and exact current-attempt gate prefix')
        if args.stage=='synth':
            output=run_stage(c,'synth');checkpoint=output/'synthesis.dcp'
            c.require(checkpoint.is_file() and checkpoint.stat().st_size>1000,'Actual synthesized checkpoint retained')
            c.result['checkpoint']={'path':rel(checkpoint),'sha256':sha(checkpoint)}
            c.result['utilization']=fpga_reports.utilization((output/'synthesis_utilization.rpt').read_text(),'Synthesized')
            c.result['timing_estimate']=fpga_reports.timing((output/'synthesis_timing.rpt').read_text(),'Synthesized',False)
            c.require(True,'Synthesis resource, clock, internal-path inventory; estimate is not routed closure')
        elif args.stage=='impl':
            parent,synth=prior_tool(journal,3,'fpga-synth',journal_name);c.result['synthesis_receipt']={'path':rel(parent),'sha256':sha(parent)}
            checkpoint=validate_chain(synth,['synth'])
            c.require(synth['checkpoint']=={'path':rel(checkpoint),'sha256':sha(checkpoint)},'Exact current synthesis checkpoint, no fallback')
            for stage,name in PHYSICAL_STEPS:
                output=run_stage(c,stage,checkpoint);checkpoint=output/name
                c.require(checkpoint.is_file() and checkpoint.stat().st_size>1000,'Real checkpoint after '+stage)
            output=run_stage(c,'reports',checkpoint)
            c.result['output']=rel(output)
            c.result['timing']=fpga_reports.timing((output/'routed_timing.rpt').read_text())
            c.result['utilization']=fpga_reports.utilization((output/'routed_utilization.rpt').read_text(),'Routed')
            c.require((output/'design.bit').is_file(),'Bitstream produced only after native setup/hold/DRC guards')
        else:
            parent,synth=prior_tool(journal,3,'fpga-synth',journal_name);impl_path,impl=prior_tool(journal,4,'fpga-impl',journal_name)
            c.result['parent_receipts']=[{'path':rel(p),'sha256':sha(p)} for p in (parent,impl_path)]
            checkpoint=validate_chain(synth,['synth']);validate_chain(impl,[stage for stage,_ in PHYSICAL_STEPS]+['reports'],checkpoint)
            output=harness.inside(impl['output'])
            c.result['reports']=fpga_reports.validate_complete(output)
            c.require(True,'Independent full report completeness, clocks, route/DRC/CDC/power/bitstream checks')
            binding={'task':'T043','status':'PASS','scope':'Full-design generated FPGA implementation evidence, human review pending; no physical programming',
                'attempt':journal['attempt'],'attempt_journal':journal_name,'base_commit':journal['git_commit'],
                'verified_prefix_sha256':hashlib.sha256(json.dumps(journal['commands'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                'source_sha256':sources,'parent_receipts':c.result['parent_receipts'],'summary':c.result['reports'],
                'artifacts':{**synth['artifacts'],**impl['artifacts']},'formal':'T023 owner-skipped / NOT RUN','physical_programming':'NOT RUN','asic':'NOT RUN'}
            target=harness.inside('evidence/fpga/manifest.json')
            if target.exists():
                backup=c.base/'prior-manifest.json';backup.write_bytes(target.read_bytes())
            harness.atomic(target,binding);c.result['manifest']={'path':rel(target),'sha256':sha(target)}
        c.require(all(sha(harness.inside(n))==h for n,h in sources.items()),'All current gate sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (ValueError,KeyError,OSError,RuntimeError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['artifacts']=artifacts(c);c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':rel(c.path),'error':c.result.get('error')}));return code


if __name__=='__main__':sys.exit(main())
