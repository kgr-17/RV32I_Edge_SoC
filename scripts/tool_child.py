#!/usr/bin/env python3
"""Wait for the parent to attach cleanup controls before starting its command."""
import json
import subprocess
import sys


def main():
    if sys.stdin.readline() != 'GO\n':
        return 125
    try:
        return subprocess.call(json.loads(sys.argv[1]), shell=False)
    except FileNotFoundError as exc:
        print('NOT RUN: ' + str(exc), file=sys.stderr)
        return 125


if __name__ == '__main__':
    sys.exit(main())
