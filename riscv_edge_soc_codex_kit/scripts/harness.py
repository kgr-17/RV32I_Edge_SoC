#!/usr/bin/env python3
"""Conservative one-task-per-day state controller, not a security sandbox."""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / 'docs/BACKLOG.json'
STATE = ROOT / '.harness/state.json'
LOCK = ROOT / '.harness/lockfile'
TZ = ZoneInfo('America/Los_Angeles')


def today():
    return dt.datetime.now(TZ).date().isoformat()


def load_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, pathname = tempfile.mkstemp(prefix='.state-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(pathname, path)
    finally:
        if os.path.exists(pathname):
            os.unlink(pathname)


@contextlib.contextmanager
def lock_state():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a+') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def fail(message):
    print('STOP:', message, file=sys.stderr)
    raise SystemExit(2)


def verify_plan():
    p = load_json(BACKLOG)
    s = load_json(STATE)
    tasks = p.get('tasks', [])
    ids = [t['id'] for t in tasks]
    if not ids or len(ids) != len(set(ids)):
        fail('empty or duplicated task ID')
    known = set(ids)
    for t in tasks:
        if not isinstance(t['depends_on'], list) or not set(t['depends_on']) <= known:
            fail(f"invalid dependency in {t['id']}")
        if t['id'] in t['depends_on']:
            fail(f"self-dependent task: {t['id']}")
        if not t['checks'] or not all(isinstance(c, list) and c for c in t['checks']):
            fail(f"task has no test/check gate: {t['id']}")
        if any(not isinstance(x, str) for c in t['checks'] for x in c):
            fail(f"invalid check command: {t['id']}")
    visited, visiting = set(), set()
    byid = {t['id']: t for t in tasks}

    def walk(task_id):
        if task_id in visited:
            return
        if task_id in visiting:
            fail(f'dependency cycle at {task_id}')
        visiting.add(task_id)
        for parent in byid[task_id]['depends_on']:
            walk(parent)
        visiting.remove(task_id)
        visited.add(task_id)

    for tid in ids:
        walk(tid)
    allowed = {'todo', 'in_progress', 'done', 'blocked', 'awaiting_review'}
    if set(s.get('task_states', {}).values()) - allowed:
        fail('unexpected state string')
    if set(s.get('task_states', {})) - known:
        fail('state references unknown task')
    if s.get('active') is not None and s['active'] not in known:
        fail('unknown active task')
    print(f'VALID PLAN: {len(tasks)} tasks, DAG acyclic; state valid')
    return tasks, s


def state_of(state, task_id):
    return state['task_states'].get(task_id, 'todo')


def ready(tasks, state):
    if state['active'] is not None:
        return []
    if any(v in ('awaiting_review', 'blocked') for v in state['task_states'].values()):
        return []
    enabled = set(state.get('enabled_optional_ids', []))
    return [t for t in tasks
            if state_of(state, t['id']) == 'todo'
            and (not t.get('optional', False) or t['id'] in enabled)
            and all(state_of(state, d) == 'done' for d in t['depends_on'])]


def git_clean():
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                       capture_output=True, text=True, timeout=15)
    if r.returncode:
        fail('initialize this kit as a Git repository first (`git init`, `git add .`, commit)')
    if r.stdout.strip():
        fail('working tree is dirty: commit/review previous changes before begin')


def cmd_status(args):
    tasks, s = verify_plan()
    counts = {x: 0 for x in ('todo', 'in_progress', 'awaiting_review', 'done', 'blocked')}
    for t in tasks:
        counts[state_of(s, t['id'])] += 1
    print('Progress:', counts)
    print('Active:', s['active'], '| Last start (America/Los_Angeles):', s['last_started_local_date'])
    if any(x in ('awaiting_review', 'blocked') for x in s['task_states'].values()):
        print('HOLD: owner review or blocked task must be resolved')
    elif ready(tasks, s):
        print('Next:', ready(tasks, s)[0]['id'], '-', ready(tasks, s)[0]['title'])
    else:
        print('No currently eligible task')


def cmd_next(args):
    tasks, s = verify_plan()
    if s['active']:
        fail(f"task already active: {s['active']}")
    if any(x in ('awaiting_review', 'blocked') for x in s['task_states'].values()):
        fail('owner review or blocked task unresolved')
    candidates = ready(tasks, s)
    if not candidates:
        print('No eligible tasks (plan completed or optional work disabled)')
        return
    t = candidates[0]
    print(json.dumps({k: t[k] for k in ('id', 'phase', 'title', 'depends_on', 'deliverables', 'checks', 'review_gate')}, indent=2, ensure_ascii=False))
    if s['last_started_local_date'] == today():
        print('DAILY LIMIT REACHED: next task shown for planning only, cannot begin today')


def task_lookup(tasks, id):
    for t in tasks:
        if t['id'] == id:
            return t
    fail(f'unknown task {id}')


def cmd_begin(args):
    with lock_state():
        tasks, s = verify_plan()
        if s['last_started_local_date'] == today():
            fail('daily quota already used (America/Los_Angeles)')
        if not ready(tasks, s):
            fail('no eligible task; address active/blocked/review gate first')
        expected = ready(tasks, s)[0]['id']
        if args.task_id != expected:
            fail(f'only the first ready task may begin: {expected}')
        git_clean()
        s['active'] = args.task_id
        s['last_started_local_date'] = today()
        s['task_states'][args.task_id] = 'in_progress'
        save_json(STATE, s)
    print(f'BEGIN {args.task_id}; quota used for {today()}; complete or block ONE task then STOP')


def inside_repo(relative):
    p = (ROOT / relative).resolve()
    if not p.is_relative_to(ROOT.resolve()):
        fail(f'evidence path escapes repository: {relative}')
    return p


def run_check(command):
    # No shell injection: command arrays are exact argv, executed without shell.
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                              timeout=180, check=False)
        output = ((proc.stdout or '') + '\n' + (proc.stderr or ''))[-12000:]
        return proc.returncode, output
    except (FileNotFoundError, subprocess.TimeoutExpired) as ex:
        return 127, str(ex)


def cmd_finish(args):
    with lock_state():
        tasks, s = verify_plan()
        t = task_lookup(tasks, args.task_id)
        if s['active'] != args.task_id or state_of(s, args.task_id) != 'in_progress':
            fail(f'task not active: {args.task_id}')
        path = inside_repo(args.evidence)
        expected_dir = (ROOT / 'evidence/daily').resolve()
        if path.parent != expected_dir or path.name != f'{args.task_id}.md':
            fail('evidence must be evidence/daily/<TASK_ID>.md')
        if not path.is_file() or len(path.read_text(encoding='utf8')) < 150:
            fail('substantive evidence file (at least 150 chars) is required')
        missing = [name for name in t['deliverables'] if not inside_repo(name).is_file()]
        if missing:
            fail(f'missing deliverables: {missing}')
        logs = []
        success = True
        for check in t['checks']:
            rc, output = run_check(check)
            status = 'PASS' if rc == 0 else 'FAIL'
            logs.append((check, rc, output))
            print(f'{status}: {check!r} (exit {rc})')
            if rc != 0:
                success = False
        rc_diff, out_diff = run_check(['git', 'diff', '--check'])
        logs.append((['git', 'diff', '--check'], rc_diff, out_diff))
        print(('PASS' if rc_diff == 0 else 'FAIL') + ': git diff --check')
        if rc_diff:
            success = False
        with path.open('a', encoding='utf8') as f:
            f.write('\n## Harness-verified commands (automatically captured)\n')
            for check, rc, output in logs:
                f.write(f'\n- `{check!r}`: exit `{rc}`\n')
                if output.strip():
                    f.write('```text\n' + output.strip()[:12000].replace('```', "'''" ) + '\n```\n')
        if not success:
            print('FAILED CHECKS. Task remains in_progress. Fix it or block with a reason; no success state written.')
            raise SystemExit(1)
        s['active'] = None
        s['completed_evidence'][args.task_id] = args.evidence
        s['task_states'][args.task_id] = 'awaiting_review' if t['review_gate'] else 'done'
        save_json(STATE, s)
    print(f'{args.task_id}: {s["task_states"][args.task_id]} — commit task files/state/evidence; STOP')


def cmd_block(args):
    with lock_state():
        _, s = verify_plan()
        if s['active'] != args.task_id:
            fail('only active task can be blocked')
        if len(args.reason.strip()) < 12:
            fail('a concrete reason >=12 chars is required')
        s['task_states'][args.task_id] = 'blocked'
        s['blocked_reasons'][args.task_id] = args.reason
        s['active'] = None
        save_json(STATE, s)
    print(f'BLOCKED {args.task_id}: {args.reason}. Owner must review and reopen later.')


def cmd_approve(args):
    if not args.confirm_owner_review:
        fail('owner-only action requires --confirm-owner-review')
    with lock_state():
        tasks, s = verify_plan()
        t = task_lookup(tasks, args.task_id)
        if not t['review_gate'] or state_of(s, args.task_id) != 'awaiting_review':
            fail('task is not awaiting owner milestone review')
        s['task_states'][args.task_id] = 'done'
        save_json(STATE, s)
    print(f'OWNER REVIEW APPROVED {args.task_id}. Commit change before next daily run.')


def cmd_reopen(args):
    if not args.confirm_owner_review:
        fail('owner-only action requires --confirm-owner-review')
    with lock_state():
        _, s = verify_plan()
        if state_of(s, args.task_id) != 'blocked':
            fail('only blocked tasks can be reopened')
        s['task_states'][args.task_id] = 'todo'
        s['blocked_reasons'].pop(args.task_id, None)
        save_json(STATE, s)
    print(f'REOPENED {args.task_id}; daily start limit still applies')


def cmd_enable(args):
    if not args.confirm_owner_review:
        fail('owner-only action requires --confirm-owner-review')
    with lock_state():
        tasks, s = verify_plan()
        t = task_lookup(tasks, args.task_id)
        if not t.get('optional', False):
            fail('task is not optional')
        enabled = set(s.get('enabled_optional_ids', []))
        enabled.add(args.task_id)
        s['enabled_optional_ids'] = sorted(enabled)
        save_json(STATE, s)
    print(f'ENABLED OPTIONAL {args.task_id} (owner-only). Commit state before next run.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    sub.add_parser('status')
    sub.add_parser('next')
    begin = sub.add_parser('begin'); begin.add_argument('task_id')
    finish = sub.add_parser('finish'); finish.add_argument('task_id'); finish.add_argument('--evidence', required=True)
    block = sub.add_parser('block'); block.add_argument('task_id'); block.add_argument('--reason', required=True)
    for name in ('approve','reopen','enable'):
        p = sub.add_parser(name); p.add_argument('task_id'); p.add_argument('--confirm-owner-review', action='store_true')
    args = parser.parse_args()
    fn = {'validate': verify_plan, 'status': cmd_status, 'next': cmd_next,
          'begin': cmd_begin, 'finish': cmd_finish, 'block': cmd_block,
          'approve': cmd_approve, 'reopen': cmd_reopen, 'enable': cmd_enable}[args.command]
    if args.command == 'validate':
        fn()
    else:
        fn(args)


if __name__ == '__main__':
    main()
