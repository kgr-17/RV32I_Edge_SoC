#!/usr/bin/env python3
"""Bounded actual SBY/SMT gates; missing executables never become proof evidence."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys
import harness
import rtl_checks
import tool_runner

TASKS={'alu':'PASS','forward':'PASS','stage':'PASS','cover_stage':'PASS','negative':'FAIL'}


def accepted(record,status,expected,witnesses,cover=False):
    if expected=='FAIL':
        return record['status']=='FAIL' and record['exit_code']==2 and status=='FAIL' and bool(witnesses)
    return record['status']=='PASS' and record['exit_code']==0 and status=='PASS' and (not cover or bool(witnesses))


def has_properties(texts,cover=False):
    marker='; yosys-smt2-cover ' if cover else '; yosys-smt2-assert '
    return any(marker in text for text in texts)


def main():
    c=rtl_checks.Checks('formal-smoke',task='T023',scope='Selected12-step bounded formal tasks and cover/negative controls; no simulation substitute')
    c.result['excluded']=['whole-core formal proof','unbounded proof','complete ALU specification','architectural RF storage proof','CPU bus liveness','CDC/reset pin timing','SoC','routed timing','hardware','ASIC']
    c.result['formal_tasks']=[]
    code=1
    try:
        config=harness.read(harness.inside('.harness/formal_toolchain.json'))
        files=['formal/core_properties.sby','formal/alu_properties.sv','formal/forwarding_properties.sv','formal/stage_properties.sv',
               'rtl/core/rv32_pkg.sv','rtl/core/alu.sv','rtl/core/forwarding_unit.sv','rtl/core/pipeline_core.sv',
               '.harness/formal_toolchain.json','.harness/checks.json','docs/ARCH_CONTRACT.json',
               'formal/tool_launcher.py','scripts/formal_checks.py','scripts/test_formal_checks.py',
               'scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py']
        c.result['source_sha256']={f:hashlib.sha256(harness.inside(f).read_bytes()).hexdigest() for f in files}
        tools={};missing=[]
        for name,args in [('sby',['--version']),('yosys',['-V']),('yosys-smtbmc',['-h']),('z3',['--version'])]:
            command=config['commands'].get(name) or [shutil.which(name) or name]
            if not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command):raise ValueError('Invalid formal tool argv: '+name)
            command=[sys.executable if x=='{python}' else x for x in command];tools[name]=command
            # Probe every required executable, retaining actual125 results.
            rec=tool_runner.run(command+args,c.base/'versions'/name,10)
            c.result['commands'].append(rec);c.save()
            if rec['status']=='NOT RUN':missing.append(name)
            elif not rtl_checks.successful(rec):raise RuntimeError('Formal version probe failed: '+name)
        c.result['resolved_commands']=tools
        if missing:raise rtl_checks.NotRun('Missing actual formal tools: '+', '.join(missing))
        for name in ('sby','yosys','z3'):
            pin=config['version_contains'].get(name)
            rec=c.result['commands'][list(tools).index(name)]
            if not pin:raise rtl_checks.NotRun('Observe/review and pin installed formal version: '+name)
            c.require(pin in rec['stdout']+rec['stderr'],'Pinned formal version '+name)
        # Absolute fresh outputs stay project-local. Only the child launcher's
        # environment gains installed tool folders; host/global PATH is unchanged.
        for task,expected in TASKS.items():
            output=c.base/task
            if output.exists():raise harness.Stop('Refuse existing formal output directory')
            actual=tools['sby']+['-d',str(output),'core_properties.sby',task]
            rec=c.command([sys.executable,'-B',str(harness.inside('formal/tool_launcher.py')),
                json.dumps(tools),json.dumps(actual)],harness.inside('formal'),60)
            status_path=output/'status';status=status_path.read_text(encoding='utf-8').strip().split()[0] if status_path.is_file() else None
            witnesses=[p for pattern in ('*.vcd','*.yw') for p in output.rglob(pattern) if p.is_file() and p.stat().st_size>0]
            models=[p for p in output.rglob('*.smt2') if p.is_file() and p.stat().st_size>0]
            c.require(has_properties([p.read_text(encoding='utf-8') for p in models],cover=task=='cover_stage'),
                'Actual nonempty formal property model '+task)
            c.require(accepted(rec,status,expected,witnesses,cover=task=='cover_stage'),'Actual bounded formal '+task,rec)
            artifacts={str(p.relative_to(harness.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [status_path]+witnesses+models}
            c.result['formal_tasks'].append({'task':task,'expected':expected,'status':status,'artifacts':artifacts});c.save()
        c.require(all(hashlib.sha256(harness.inside(f).read_bytes()).hexdigest()==h for f,h in c.result['source_sha256'].items()),'Formal inputs unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:
        c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,TypeError,harness.Stop,IndexError) as exc:
        c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'formal_tasks':len(c.result['formal_tasks']),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
