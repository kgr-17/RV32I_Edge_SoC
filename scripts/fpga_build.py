#!/usr/bin/env python3
"""Project-local nonproject build job preparation; owner-controlled execution.

Plan runs validate Tcl/inputs/paths without synthesis. Workflow acknowledgments
are not security or authentication. Actual runtime remains unrestricted.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import harness
import tool_runner

CONFIG='config/fpga_build.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def project_path(name):
    path=Path(name)
    if path.is_absolute():
        try:name=path.resolve().relative_to(harness.ROOT).as_posix()
        except ValueError as exc:raise harness.Stop('FPGA_PATH_OUTSIDE_PROJECT') from exc
    return harness.inside(str(name))


def load_config(name=CONFIG):
    c=harness.read(project_path(name))
    keys={'schema_version','top','part','clock_period_ns','vivado_version','vivado_sw_build','design_scope','rtl_sources','constraints','memory_files'}
    if set(c)!=keys or type(c['schema_version']) is not int or c['schema_version']!=1:raise ValueError('FPGA_CONFIG_SCHEMA')
    if c['top']!='basys3_top' or c['part']!='xc7a35tcpg236-1' or type(c['clock_period_ns']) not in (int,float) or c['clock_period_ns']!=10:
        raise ValueError('FPGA_TARGET_CONTRACT')
    if c['vivado_version']!='2025.2' or str(c['vivado_sw_build'])!='6299465':raise ValueError('FPGA_VERSION_CONTRACT')
    if not isinstance(c['design_scope'],str) or not re.fullmatch(r'[A-Za-z0-9_]+',c['design_scope']):raise ValueError('FPGA_SCOPE')
    for key,suffixes,required in [('rtl_sources',{'.sv','.v'},True),('constraints',{'.xdc'},True),('memory_files',{'.mem'},False)]:
        values=c[key]
        if not isinstance(values,list) or (required and not values) or any(not isinstance(v,str) for v in values):raise ValueError('FPGA_INPUT_LIST '+key)
        resolved=[]
        for value in values:
            path=project_path(value)
            if path.suffix.lower() not in suffixes or not path.is_file():raise ValueError('FPGA_INPUT_FILE '+value)
            resolved.append(str(path).casefold())
        if len(set(resolved))!=len(resolved):raise ValueError('FPGA_DUPLICATE_INPUT '+key)
    if len({Path(n).name.casefold() for n in c['memory_files']})!=len(c['memory_files']):raise ValueError('FPGA_MEMORY_BASENAME_ALIAS')
    return c


def check_execution(config,state):
    if (state.get('active')!='T043' or 'T043' not in state.get('start_approvals',{}) or
            any(state.get('task_states',{}).get(tid)!='completed' for tid in ('T031','T044','T045')) or
            'T044' not in state.get('owner_reviews',{}) or config['design_scope']=='diagnostic_shell_before_T031'):
        raise harness.Stop('FPGA_OWNER_AUTH_REQUIRED: authorized active T043 and reviewed integrated interrupt design required')


def prepare_job(output,mode='plan',stage='all',config_name=CONFIG,checkpoint=None):
    c=load_config(config_name)
    if mode not in ('plan','execute') or stage not in ('synth','impl','all'):raise ValueError('FPGA_MODE_STAGE')
    if mode=='execute':
        _,state=harness.load();check_execution(c,state)
    jobdir=project_path(output);build=harness.inside('build')
    if jobdir==build or build not in jobdir.parents:raise ValueError('FPGA_OUTPUT_OUTSIDE_BUILD')
    if jobdir.exists():raise ValueError('FPGA_OUTPUT_EXISTS')
    checkpoint_path=None
    if checkpoint is not None:
        checkpoint_path=project_path(checkpoint)
        if checkpoint_path.suffix!='.dcp' or not checkpoint_path.is_file():raise ValueError('FPGA_CHECKPOINT_FILE')
        if build not in checkpoint_path.parents:raise ValueError('FPGA_CHECKPOINT_OUTSIDE_BUILD')
    if stage=='impl' and checkpoint_path is None:raise ValueError('FPGA_CHECKPOINT_REQUIRED')
    source_names=[config_name,'fpga/basys3/build.tcl','scripts/fpga_build.py','scripts/tool_runner.py','scripts/tool_child.py','docs/ARCH_CONTRACT.json']+c['rtl_sources']+c['constraints']+c['memory_files']
    inputs={project_path(n).relative_to(harness.ROOT).as_posix():sha(project_path(n)) for n in source_names}
    if checkpoint_path:inputs[checkpoint_path.relative_to(harness.ROOT).as_posix()]=sha(checkpoint_path)
    jobdir.mkdir(parents=True,exist_ok=False)
    data=[('schema','1'),('root',harness.ROOT.as_posix()),('mode',mode),('stage',stage),('top',c['top']),('part',c['part']),
        ('period','10.000'),('version',c['vivado_version']),('sw_build',str(c['vivado_sw_build'])),('scope',c['design_scope']),
        ('output',(jobdir/'artifacts').as_posix()),('authorization','T043' if mode=='execute' else 'none'),('checkpoint',checkpoint_path.as_posix() if checkpoint_path else '')]
    for key,kind in [('rtl_sources','source'),('constraints','constraint'),('memory_files','memory')]:
        data.extend((kind,project_path(n).as_posix()) for n in c[key])
    if any('\t' in v or '\n' in v or '\r' in v for key,v in data):raise ValueError('FPGA_JOB_TEXT')
    job=jobdir/'job.tsv';harness.atomic_text(job,''.join(key+'\t'+value+'\n' for key,value in data))
    record={'schema_version':1,'mode':mode,'stage':stage,'config':config_name,'design_scope':c['design_scope'],'source_sha256':inputs,
        'job':job.relative_to(harness.ROOT).as_posix(),'job_sha256':sha(job),'output':(jobdir/'artifacts').relative_to(harness.ROOT).as_posix(),
        'scope':'Plan is dispatch/input validation only; execution requires owner workflow and active T043. No hardware programming commands.'}
    harness.atomic(jobdir/'inputs.json',record)
    return job,record


def run_job(job,record,timeout=120):
    job=Path(job);folder=job.parent
    result=tool_runner.run(tool_runner.vendor_argv('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('fpga/basys3/build.tcl')),'-tclargs',str(job)]),folder/'tool',timeout)
    record=dict(record,command=result,finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    record['inputs_unchanged']=all(sha(harness.inside(n))==digest for n,digest in record['source_sha256'].items())
    harness.atomic(folder/'result.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('plan','execute'));parser.add_argument('--stage',choices=('synth','impl','all'),default='all')
    parser.add_argument('--output',required=True);parser.add_argument('--config',default=CONFIG);parser.add_argument('--checkpoint')
    args=parser.parse_args();job,record=prepare_job(args.output,args.mode,args.stage,args.config,args.checkpoint)
    result=run_job(job,record);output=result['command']['stdout']+result['command']['stderr']
    marker='FPGA_BUILD_PLAN_PASS' if args.mode=='plan' else 'FPGA_BUILD_EXECUTION_PASS'
    ok=result['command']['status']=='PASS' and result['command']['exit_code']==0 and marker in output and result['inputs_unchanged'] and not re.search(r'(?im)^\s*(?:WARNING:|ERROR:|FATAL:)',output)
    print(json.dumps({'status':'PASS' if ok else 'FAIL','mode':args.mode,'stage':args.stage,'result':str(job.parent.relative_to(harness.ROOT)/'result.json')}))
    return 0 if ok else 1


if __name__=='__main__':
    try:sys.exit(main())
    except (harness.Stop,ValueError,OSError,KeyError) as exc:print('FAIL: '+str(exc),file=sys.stderr);sys.exit(1)
