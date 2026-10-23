#!/usr/bin/env python3
"""Sequential attended task controller. Workflow checks are not a security sandbox."""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATES = {'pending', 'in_progress', 'passed', 'failed', 'blocked', 'awaiting_review', 'completed'}
REQUIRED = {'id', 'title', 'description', 'engineering_objective', 'depends_on',
            'required_files', 'acceptance_criteria', 'verification_commands',
            'priority', 'status', 'human_approval_required', 'optional'}


class Stop(RuntimeError):
    pass


def today():
    try:
        return dt.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
    except Exception as exc:
        raise Stop('America/Los_Angeles unavailable; request approved tzdata installation') from exc


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def atomic(path, value):
    atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def atomic_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.state-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def inside(name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or PureWindowsPath(name).drive:
        raise Stop('Expected project-relative path: ' + str(name))
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise Stop('Path escapes project: ' + name)
    return path


@contextlib.contextmanager
def lock():
    path = inside('.harness/lockfile')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Stop('Another process owns the state lock') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def status(state, task):
    return state['task_states'].get(task['id'], task['status'])


def load():
    plan, state = read(inside('docs/BACKLOG.json')), read(inside('.harness/state.json'))
    if state.get('schema_version') not in (2, 3):
        raise Stop('Unsupported state schema')
    tasks = plan['tasks']
    ids = [t['id'] for t in tasks]
    if not tasks or len(ids) != len(set(ids)):
        raise Stop('Empty plan or duplicate task IDs')
    byid = {t['id']: t for t in tasks}
    for task in tasks:
        if REQUIRED - task.keys():
            raise Stop('Missing task fields: ' + task['id'])
        if task['status'] not in STATES or type(task['priority']) is not int:
            raise Stop('Invalid status/priority: ' + task['id'])
        if not isinstance(task['depends_on'], list) or not set(task['depends_on']) <= byid.keys():
            raise Stop('Unknown dependency: ' + task['id'])
        for field in ('required_files', 'acceptance_criteria'):
            if not task[field] or not all(isinstance(x, str) and x for x in task[field]):
                raise Stop('Missing deliverables/acceptance: ' + task['id'])
        for name in task['required_files']:
            inside(name)
        commands = task['verification_commands']
        if not commands or not all(isinstance(c, list) and c and
                                  all(isinstance(a, str) and a for a in c) for c in commands):
            raise Stop('Invalid verification argv: ' + task['id'])
        if type(task['human_approval_required']) is not bool or type(task['optional']) is not bool:
            raise Stop('Approval/optional fields must be booleans')
    visited, visiting = set(), set()

    def walk(tid):
        if tid in visiting:
            raise Stop('Dependency cycle at ' + tid)
        if tid not in visited:
            visiting.add(tid)
            for dep in byid[tid]['depends_on']:
                walk(dep)
            visiting.remove(tid)
            visited.add(tid)
    for tid in ids:
        walk(tid)
    if set(state['task_states']) - byid.keys() or set(state['task_states'].values()) - STATES:
        raise Stop('Unknown task or invalid runtime status')
    for task in tasks:
        if status(state, task) in ('in_progress', 'passed', 'failed', 'awaiting_review', 'completed') and any(
                status(state, byid[d]) != 'completed' for d in task['depends_on']):
            raise Stop('Runtime task bypasses incomplete dependency: ' + task['id'])
    active = state['active']
    unfinished = [t['id'] for t in tasks if status(state, t) in ('in_progress', 'failed', 'passed')]
    if active not in [None] + ids or unfinished != ([] if active is None else [active]):
        raise Stop('Inconsistent active task: recover from Git, never skip it')
    if any(tid not in byid for tid in state['daily_claims'].values()):
        raise Stop('Unknown daily claim')
    for date, exception in state.get('daily_exceptions', {}).items():
        validate_day_exception(exception['evidence'], date, exception['task'], state, byid)
        if exception['sha256'] != hashlib.sha256(inside(exception['evidence']).read_bytes()).hexdigest():
            raise Stop('Daily exception evidence changed')
    history = task_days(state)
    if state['schema_version'] == 3 and state.get('daily_tasks') != history:
        raise Stop('Task history must include every preserved legacy claim/exception')
    for date, tids in history.items():
        if dt.date.fromisoformat(date).isoformat() != date or not isinstance(tids, list) or not tids:
            raise Stop('Invalid dated task history')
        if len(tids) != len(set(tids)) or any(tid not in byid for tid in tids):
            raise Stop('Duplicate or unknown task in dated history')
    if any(tid not in byid or type(n) is not int or not 0 <= n <= 3
           for tid, n in state['attempts'].items()):
        raise Stop('Invalid attempt count')
    if set(state['enabled_optional_ids']) - byid.keys():
        raise Stop('Unknown enabled optional task')
    final = byid.get(plan.get('final_review_task'))
    mandatory = {t['id'] for t in tasks if not t['optional']}
    if not final or not final['human_approval_required'] or final['optional'] or not (
            mandatory - {final['id']}) <= set(final['depends_on']):
        raise Stop('Final owner review must depend on every mandatory task')
    if state['project_status'] == 'completed' and not all(
            status(state, t) == 'completed' for t in tasks if not t['optional']):
        raise Stop('Project falsely marked completed')
    return plan, state


def save(plan, state):
    # State is authoritative. Backlog statuses are a repairable projection.
    state['daily_tasks'] = task_days(state)
    state['schema_version'] = 3
    atomic(inside('.harness/state.json'), state)
    for task in plan['tasks']:
        task['status'] = status(state, task)
    atomic(inside('docs/BACKLOG.json'), plan)


def candidates(plan, state):
    if state['active'] or state['project_status'] == 'completed':
        return []
    if any(status(state, t) in ('awaiting_review', 'blocked') for t in plan['tasks']
           if not t['optional'] or t['id'] in state['enabled_optional_ids']):
        return []
    byid = {t['id']: t for t in plan['tasks']}
    return sorted((t for t in plan['tasks'] if status(state, t) == 'pending'
                   and (not t['optional'] or t['id'] in state['enabled_optional_ids'])
                   and (not t.get('start_approval_required') or t['id'] in state.get('start_approvals', {}))
                   and all(status(state, byid[d]) == 'completed' for d in t['depends_on'])),
                  key=lambda t: (t['priority'], t['id']))


def local_env():
    env = os.environ.copy()
    temp = inside('.tmp')
    temp.mkdir(exist_ok=True)
    env.update(TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp), PYTHONDONTWRITEBYTECODE='1',
               PYTHONPYCACHEPREFIX=str(inside('build/pycache')), PYTHONIOENCODING='utf-8',
               PIP_CACHE_DIR=str(inside('build/pip-cache')), XDG_CACHE_HOME=str(inside('build/cache')))
    return env


def run(argv):
    argv = [sys.executable if x == '{python}' else x for x in argv]
    record = {'argv': argv, 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'cwd': str(ROOT), 'executable': shutil.which(argv[0]), 'status': 'NOT RUN',
              'exit_code': None, 'stdout': '', 'stderr': ''}
    try:
        proc = subprocess.run(argv, cwd=ROOT, env=local_env(), capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=300)
        record.update(exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr,
                      status='PASS' if proc.returncode == 0 else
                      ('NOT RUN' if proc.returncode in (125, 127) else 'FAIL'))
    except FileNotFoundError as exc:
        record['stderr'] = str(exc)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ''
        record.update(status='FAIL', stderr='TIMEOUT after 300 seconds',
                      stdout=output.decode('utf-8', 'replace') if isinstance(output, bytes) else output)
    return record


def git_head():
    proc = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def clean():
    proc = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode or proc.stdout.strip():
        raise Stop('New work requires a clean Git baseline; inspect and preserve existing changes')


def validate_day_exception(evidence, date, tid, state, byid):
    """Validate preserved pre-policy-change provenance, not a current quota gate."""
    record = read(inside(evidence))
    previous = state['daily_claims'].get(date)
    if (record.get('schema_version') != 1 or record.get('date') != date or
            record.get('task') != tid or record.get('previous_task') != previous or
            previous == tid or previous not in byid or tid not in byid or
            status(state, byid[previous]) != 'completed' or
            record.get('owner_answer') != 'Yes—start T004 today' or
            record.get('question_item_id') !=
            '["request_user_input_async","call_db6019c10ff8475da53c07dfb0dd2c37",0]' or
            tid != 'T004' or date != '2026-10-23'):
        raise Stop('Invalid one-time owner daily exception')


def task_days(state):
    """Ordered participation history; legacy claims/exceptions remain unchanged."""
    entries = state.get('daily_tasks', {})
    if not isinstance(entries, dict) or any(
            not isinstance(date, str) or not isinstance(tids, list) or
            not all(isinstance(tid, str) for tid in tids) for date, tids in entries.items()):
        raise Stop('Invalid dated task history structure')
    history = {date: list(tids) for date, tids in entries.items()}
    for date, tid in state['daily_claims'].items():
        if tid not in history.setdefault(date, []):
            history[date].insert(0, tid)
    for date, exception in state.get('daily_exceptions', {}).items():
        if exception['task'] not in history.setdefault(date, []):
            history[date].append(exception['task'])
    return history


def record_task_day(state, date, tid):
    history = task_days(state)
    if tid not in history.setdefault(date, []):
        history[date].append(tid)
    state['daily_tasks'] = history


def begin(tid):
    with lock():
        plan, state = load()
        date = today()
        if state['project_status'] == 'completed':
            raise Stop('Project completed: no additional implementation')
        if state['active']:
            if state['active'] != tid:
                raise Stop('Recover active task ' + state['active'])
            record_task_day(state, date, tid)
            save(plan, state)
            return {'action': 'RESUME', 'task': tid, 'attempts': state['attempts'].get(tid, 0)}
        ready = candidates(plan, state)
        if not ready or ready[0]['id'] != tid:
            raise Stop('Not the first eligible task; dependencies/review may block it')
        clean()
        state['active'] = tid
        record_task_day(state, date, tid)
        state['task_states'][tid] = 'in_progress'
        state['attempts'].setdefault(tid, 0)
        save(plan, state)
        return {'action': 'BEGIN', 'task': tid}


def finish(tid, evidence):
    with lock():
        plan, state = load()
        task = next((t for t in plan['tasks'] if t['id'] == tid), None)
        if task is None:
            raise Stop('Unknown task: ' + tid)
        if status(state, task) in ('completed', 'awaiting_review'):
            return {'action': 'ALREADY_VERIFIED', 'task': tid, 'status': status(state, task)}
        if state['active'] != tid:
            raise Stop('Only the active task can finish')
        date = today()
        record_task_day(state, date, tid)
        path = inside(evidence)
        if path != inside('evidence/daily/' + tid + '.md') or not path.is_file():
            raise Stop('Evidence must exist at evidence/daily/' + tid + '.md')
        if len(path.read_text(encoding='utf-8')) < 150:
            raise Stop('Evidence must explain acceptance, commands, results and limitations')
        for suffix in ('technical', 'zh-CN'):
            report = inside('docs/daily/' + date + '_' + suffix + '.md')
            if not report.is_file() or len(report.read_text(encoding='utf-8')) < 150:
                raise Stop('Both substantive daily reports are required before finish')
        missing = [name for name in task['required_files'] if not inside(name).is_file()]
        if missing:
            raise Stop('Missing required files: ' + ', '.join(missing))
        attempt = state['attempts'].get(tid, 0) + 1
        if attempt > 3:
            raise Stop('Three attempts exhausted; owner recovery required')
        state['attempts'][tid] = attempt
        state['task_states'][tid] = 'in_progress'
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        log = 'evidence/runs/{}/attempt-{}-{}.json'.format(tid, attempt, stamp)
        state['receipts'][tid] = log
        save(plan, state)  # A crash cannot reset the attempt budget.
        records = []
        receipt = {'task': tid, 'attempt': attempt, 'git_commit': git_head(), 'python': sys.version,
                   'stage': 'running', 'commands': records, 'waveform_paths': [], 'seed': None,
                   'evidence_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        atomic(inside(log), receipt)
        for command in task['verification_commands'] + [
                ['git', 'diff', '--check'], ['git', 'diff', '--cached', '--check']]:
            records.append(run(command))
            atomic(inside(log), receipt)
        receipt['stage'] = 'finished'
        atomic(inside(log), receipt)
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write('\n## Verification attempt {}\n\nReceipt: {}\n'.format(attempt, log))
            for record in records:
                stream.write('\n- {}: {}, exit {}\n'.format(
                    subprocess.list2cmdline(record['argv']), record['status'], record['exit_code']))
        passed = all(r['status'] == 'PASS' for r in records)
        state['receipts'][tid] = log
        if passed:
            state['task_states'][tid] = 'awaiting_review' if task['human_approval_required'] else 'completed'
            state['active'] = None
        else:
            state['task_states'][tid] = 'blocked' if attempt == 3 else 'failed'
            if attempt == 3:
                state['active'] = None
                state['blocked_reasons'][tid] = 'Three attempts exhausted; inspect ' + log
        save(plan, state)
        result = {'task': tid, 'status': state['task_states'][tid], 'receipt': log,
                  'checks': [r['status'] for r in records]}
        if not passed:
            print(json.dumps(result, indent=2))
            raise Stop('Verification failed or NOT RUN; correct within budget or block')
        return result


def owner_action(command, tid, confirmed):
    if not confirmed:
        raise Stop('Owner-only command requires --confirm-owner-review; agent must not self-approve')
    with lock():
        plan, state = load()
        task = next((t for t in plan['tasks'] if t['id'] == tid), None)
        if task is None:
            raise Stop('Unknown task')
        current = status(state, task)
        if command == 'approve':
            if current == 'completed':
                return {'action': 'ALREADY_APPROVED', 'task': tid}
            if current != 'awaiting_review' or not task['human_approval_required']:
                raise Stop('Task is not awaiting owner review')
            state['task_states'][tid] = 'completed'
            state['owner_reviews'][tid] = {'date': today(), 'receipt': state['receipts'].get(tid)}
            if all(status(state, t) == 'completed' for t in plan['tasks'] if not t['optional']):
                state['project_status'] = 'completed'
        elif command == 'reopen':
            if current != 'blocked':
                raise Stop('Only blocked tasks can be reopened')
            state['task_states'][tid] = 'pending'
            state['blocked_reasons'].pop(tid, None)
            state['attempts'][tid] = 0
        elif command == 'authorize':
            if not task.get('start_approval_required'):
                raise Stop('Task does not require execution authorization')
            state.setdefault('start_approvals', {})[tid] = {'date': today()}
        else:
            if not task['optional']:
                raise Stop('Only optional tasks can be enabled')
            state['enabled_optional_ids'] = sorted(set(state['enabled_optional_ids'] + [tid]))
        save(plan, state)
        return {'action': command.upper(), 'task': tid}


def daily(supervised):
    if not supervised:
        raise Stop('Unattended execution disabled. Configure actual sandbox controls first; '
                   '--supervised is only for an attended session')
    plan, state = load()
    reports = sorted(inside('docs/daily').glob('*_technical.md'))
    if not reports:
        raise Stop('No technical handoff; bootstrap must generate the first report')
    ready = candidates(plan, state)
    return {'mode': 'SUPERVISED ONLY', 'latest_handoff': str(reports[-1].relative_to(ROOT)),
            'handoff': reports[-1].read_text(encoding='utf-8'), 'active_task': state['active'],
            'project_status': state['project_status'], 'daily_claim': state['daily_claims'].get(today()),
            'daily_exception': state.get('daily_exceptions', {}).get(today()),
            'tasks_today': task_days(state).get(today(), []), 'daily_task_limit': None,
            'next': ready[0] if ready else None,
            'instruction': 'Read the handoff and prompts/DAILY_RUN.md; inspect Git status. '
                           'Recover active work first. After each task passes, update reports and '
                           'commit; then continue with the next ready task in this attended session.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'status', 'next'):
        sub.add_parser(name)
    p = sub.add_parser('daily'); p.add_argument('--supervised', action='store_true')
    p = sub.add_parser('begin'); p.add_argument('task_id')
    p = sub.add_parser('finish'); p.add_argument('task_id'); p.add_argument('--evidence', required=True)
    p = sub.add_parser('block'); p.add_argument('task_id'); p.add_argument('--reason', required=True)
    for name in ('approve', 'reopen', 'enable', 'authorize'):
        p = sub.add_parser(name); p.add_argument('task_id'); p.add_argument('--confirm-owner-review', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'begin':
            result = begin(args.task_id)
        elif args.command == 'finish':
            result = finish(args.task_id, args.evidence)
        elif args.command in ('approve', 'reopen', 'enable', 'authorize'):
            result = owner_action(args.command, args.task_id, args.confirm_owner_review)
        elif args.command == 'daily':
            result = daily(args.supervised)
        elif args.command == 'block':
            if len(args.reason.strip()) < 12:
                raise Stop('A concrete blocker reason is required')
            with lock():
                plan, state = load()
                if state['active'] != args.task_id:
                    raise Stop('Only the active task can be blocked')
                state['task_states'][args.task_id] = 'blocked'
                state['active'] = None
                state['blocked_reasons'][args.task_id] = args.reason
                save(plan, state)
                result = {'task': args.task_id, 'status': 'blocked', 'reason': args.reason}
        else:
            plan, state = load()
            ready = candidates(plan, state)
            result = {'valid': True, 'tasks': len(plan['tasks']), 'project_status': state['project_status']}
            result['daily_exception'] = state.get('daily_exceptions', {}).get(today())
            result.update(tasks_today=task_days(state).get(today(), []), daily_task_limit=None)
            result['execution_approval_pending'] = [t['id'] for t in plan['tasks']
                if t.get('start_approval_required') and status(state, t) == 'pending'
                and t['id'] not in state.get('start_approvals', {})]
            if args.command == 'status':
                result.update(active=state['active'], daily_claim=state['daily_claims'].get(today()),
                              counts={s: sum(status(state, t) == s for t in plan['tasks']) for s in sorted(STATES)})
            elif args.command == 'next':
                result.update(active=state['active'], daily_claim=state['daily_claims'].get(today()),
                              next=ready[0] if ready else None, planning_only=not bool(ready))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (Stop, OSError, ValueError, KeyError, TypeError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
