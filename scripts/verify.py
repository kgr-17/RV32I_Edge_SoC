#!/usr/bin/env python3
"""Run explicitly registered engineering checks; an empty registry never passes."""
import argparse
import json
import sys
from pathlib import Path
import harness


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
    records = [harness.run(command) for command in entry['commands']]
    for record in records:
        print(json.dumps(record, ensure_ascii=False))
    if any(r['status'] == 'NOT RUN' for r in records):
        return 125
    return 0 if all(r['status'] == 'PASS' for r in records) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (harness.Stop, OSError, ValueError, KeyError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
