#!/usr/bin/env python3
"""Append an idempotent bilingual handoff entry to exactly two dated reports."""
import argparse
import hashlib
import json
import sys
import harness


def generate(entry):
    if set(entry) != {'technical', 'zh-CN'} or any(
            not isinstance(x, str) or len(x.strip()) < 150 for x in entry.values()):
        raise harness.Stop('Entry requires substantive technical and zh-CN text')
    digest = hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    marker = '<!-- entry:' + digest + ' -->'
    date = harness.today()
    paths = []
    with harness.lock():
        for key, suffix in (('technical', 'technical'), ('zh-CN', 'zh-CN')):
            path = harness.inside('docs/daily/' + date + '_' + suffix + '.md')
            path.parent.mkdir(parents=True, exist_ok=True)
            old = path.read_text(encoding='utf-8') if path.exists() else ''
            if marker not in old:
                harness.atomic_text(path, old + ('\n\n---\n\n' if old else '') +
                                    marker + '\n\n' + entry[key].rstrip() + '\n')
            paths.append(str(path.relative_to(harness.ROOT)))
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', required=True, help='Project-local JSON with technical and zh-CN strings')
    args = parser.parse_args()
    print(json.dumps(generate(harness.read(harness.inside(args.entry))), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (harness.Stop, OSError, ValueError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        sys.exit(2)
