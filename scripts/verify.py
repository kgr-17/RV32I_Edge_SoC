#!/usr/bin/env python3
"""Run explicitly registered engineering checks; an empty registry never passes."""
import argparse
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import harness


def run_commands(commands, timeout, parallel=False, on_record=None):
    if not parallel:
        return [harness.run(command, timeout_seconds=timeout) for command in commands]
    output_lock=threading.Lock()
    def execute(item):
        index,command=item
        try:
            record=harness.run(command, timeout_seconds=timeout)
        except (harness.Stop, OSError, ValueError, KeyError) as exc:
            record={'argv':command,'status':'FAIL','exit_code':None,'stdout':'',
                    'stderr':str(exc),'timeout_seconds':timeout}
        record['registered_command_index']=index
        if on_record:
            with output_lock:on_record(record)
        return record
    # Independent targets have unique native work directories. Preserve result
    # order and join every target, including after errors; no checks are removed.
    with ThreadPoolExecutor(max_workers=2) as pool:
        # Later additions contain the larger peripheral/SoC suites. Start them
        # first, while returning records in the declared manifest order.
        records=list(pool.map(execute, reversed(list(enumerate(commands)))))
        return list(reversed(records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check')
    args = parser.parse_args()
    registry = harness.read(harness.inside('.harness/checks.json'))
    entry = registry.get(args.check)
    if not entry or not entry.get('commands') or not entry.get('inputs'):
        print('NOT RUN: no implemented check with explicit inputs: ' + args.check)
        return 125
    if any(not harness.inside(name).is_file() for name in entry['inputs']):
        print('NOT RUN: missing check inputs: ' + args.check)
        return 125
    parallel=args.check=='regress'
    emit=lambda record:print(json.dumps(record,ensure_ascii=False),flush=True)
    records = run_commands(entry['commands'], entry.get('timeout_seconds',300),
                           parallel=parallel,on_record=emit if parallel else None)
    if not parallel:
        for record in records:emit(record)
    if any(r['status'] == 'NOT RUN' for r in records):
        return 125
    return 0 if all(r['status'] == 'PASS' for r in records) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (harness.Stop, OSError, ValueError, KeyError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
