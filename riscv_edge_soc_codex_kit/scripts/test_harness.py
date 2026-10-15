#!/usr/bin/env python3
"""Integration self-check of the state machine; uses a disposable Git checkout."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SOURCE = Path(__file__).resolve().parents[1]


def invoke(root, *argv, success=True):
    p = subprocess.run([sys.executable, 'scripts/harness.py', *argv], cwd=root,
                       capture_output=True, text=True)
    if (p.returncode == 0) != success:
        raise AssertionError(f'command={argv} rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}')
    return p


def run():
    with tempfile.TemporaryDirectory(prefix='riscv-harness-test-') as d:
        root = Path(d) / 'repo'
        shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns('__pycache__','.git'))
        for args in (["init"], ["config","user.email","test@example.invalid"], ["config","user.name","Test Bot"]):
            subprocess.run(['git',*args],cwd=root,check=True,capture_output=True)
        subprocess.run(['git','add','.'],cwd=root,check=True,capture_output=True)
        subprocess.run(['git','commit','-m','initial'],cwd=root,check=True,capture_output=True)
        assert 'T001' in invoke(root,'next').stdout
        invoke(root,'begin','T002',success=False)
        invoke(root,'begin','T001')
        invoke(root,'begin','T001',success=False)
        p=root/'evidence/daily/T001.md'
        p.write_text('# T001\n' + 'Task design, validation context, and test evidence. '*5)
        invoke(root,'finish','T001','--evidence','evidence/daily/T001.md',success=False)
        # Makefile gate needs to be provided by T001; make target actually runs validation.
        (root/'Makefile').write_text('preflight:\n\tpython3 scripts/harness.py validate\n')
        invoke(root,'finish','T001','--evidence','evidence/daily/T001.md')
        invoke(root,'begin','T002',success=False) # daily quota
        statefile=root/'.harness/state.json'
        obj=json.loads(statefile.read_text()); assert obj['task_states']['T001']=='done'
        obj['last_started_local_date']=str(datetime.now(ZoneInfo("America/Los_Angeles")).date()-timedelta(days=1))
        statefile.write_text(json.dumps(obj,indent=2)+'\n')
        subprocess.run(['git','add','.'],cwd=root,check=True,capture_output=True)
        subprocess.run(['git','commit','-m','complete T001'],cwd=root,check=True,capture_output=True)
        invoke(root,'begin','T002')
        (root/'evidence/daily/T002.md').write_text('# T002\n' + 'Architecture review and unresolved decisions recorded. '*6)
        invoke(root,'finish','T002','--evidence','evidence/daily/T002.md')
        invoke(root,'next',success=False)  # owner review gate
        invoke(root,'approve','T002',success=False)
        invoke(root,'approve','T002','--confirm-owner-review')
        status=invoke(root,'status').stdout
        assert 'T003' in status, status
    print('HARNESS SELFTEST PASS: one-task/day + check gates + owner approval')

if __name__=='__main__':
    run()
