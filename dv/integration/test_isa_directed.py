#!/usr/bin/env python3
"""Validate executable L1 family/fault traceability against fresh actual evidence."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dv.reference.retire import compare_trace

ARCH_SHA256 = '403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03'
MUTATIONS = {'mutated_actual_bit', 'empty_actual', 'extra_actual_event'}


def validate(arch, run, seeds, current_hashes):
    names = arch['isa']['instructions']
    if len(names) != 40 or len(set(names)) != 40:
        raise ValueError('reviewed forty-family set is missing/duplicated')
    if run['status'] != 'PASS' or not run['checks'] or any(c['status'] != 'PASS' for c in run['checks']):
        raise ValueError('actual independent comparison is not passing')
    if not current_hashes or run['source_sha256'] != current_hashes:
        raise ValueError('actual evidence is stale or unbound to current sources')
    rows = run['comparisons']
    if not seeds or [row['seed'] for row in rows] != seeds or len(set(seeds)) != len(seeds):
        raise ValueError('missing/duplicate/wrong actual seeds')
    for row in rows:
        bins = ['op:' + name for name in names] + ['fault:%d' % n for n in range(1, 10)]
        if any(type(row['coverage'].get(key)) is not int or row['coverage'][key] < 1 for key in bins):
            raise ValueError('unhit instruction/fault bin')
        if row['retirements'] < 1 or row['faults'] != len(row['scenarios']):
            raise ValueError('empty or inconsistent scenario evidence')
        if row['gpr_words'] != 31 * row['faults'] or row['ram_words'] != 32 * row['faults']:
            raise ValueError('terminal state sample gap')
        if row['events'] != row['retirements'] + row['faults'] + row['gpr_words'] + row['ram_words']:
            raise ValueError('event accounting gap')
        negatives = row['negative_rejections']
        if len(negatives) != 3 or {n['case'] for n in negatives} != MUTATIONS or any(not n['diagnostic'] for n in negatives):
            raise ValueError('mutation rejection gap')
    return {
        'instructions': [{'instruction': name, 'hits': {str(row['seed']): row['coverage']['op:' + name] for row in rows}} for name in names],
        'faults': [{'code': code, 'name': name, 'hits': {str(row['seed']): row['coverage']['fault:%d' % code] for row in rows}}
                   for name, code in sorted(arch['fault_codes'].items(), key=lambda pair: pair[1])],
        'retirements': sum(row['retirements'] for row in rows),
        'fault_events': sum(row['faults'] for row in rows),
        'gpr_words': sum(row['gpr_words'] for row in rows),
        'ram_words': sum(row['ram_words'] for row in rows)}


class BaselinePolicyTests(unittest.TestCase):
    def setUp(self):
        self.arch = json.loads((ROOT / 'docs/ARCH_CONTRACT.json').read_text())
        coverage = {'op:' + name: 1 for name in self.arch['isa']['instructions']}
        coverage.update({'fault:%d' % n: 1 for n in range(1, 10)})
        row = {'seed': 1, 'coverage': coverage, 'retirements': 40, 'faults': 9,
               'scenarios': list(range(9)), 'gpr_words': 279, 'ram_words': 288, 'events': 616,
               'negative_rejections': [{'case': name, 'diagnostic': 'injected failure'} for name in sorted(MUTATIONS)]}
        self.run_data = {'status': 'PASS', 'checks': [{'status': 'PASS'}], 'source_sha256': {'file': 'hash'}, 'comparisons': [row]}

    def test_complete_nonempty_matrix(self):
        result = validate(self.arch, self.run_data, [1], {'file': 'hash'})
        self.assertEqual((len(result['instructions']), len(result['faults'])), (40, 9))

    def test_missing_family_or_fault_rejected(self):
        for key in ('op:ADD', 'fault:5'):
            changed = copy.deepcopy(self.run_data)
            del changed['comparisons'][0]['coverage'][key]
            with self.assertRaises(ValueError): validate(self.arch, changed, [1], {'file': 'hash'})

    def test_stale_or_failed_evidence_rejected(self):
        with self.assertRaises(ValueError): validate(self.arch, self.run_data, [1], {'file': 'changed'})
        for status in ('FAIL', 'NOT RUN', 'RUNNING'):
            changed = copy.deepcopy(self.run_data); changed['status'] = status
            with self.assertRaises(ValueError): validate(self.arch, changed, [1], {'file': 'hash'})

    def test_seed_gap_rejected(self):
        for seeds in ([], [1, 1], [2]):
            with self.assertRaises(ValueError): validate(self.arch, self.run_data, seeds, {'file': 'hash'})

    def test_state_or_event_accounting_gap_rejected(self):
        for key in ('retirements', 'gpr_words', 'ram_words', 'events'):
            changed = copy.deepcopy(self.run_data); changed['comparisons'][0][key] = 0
            with self.assertRaises(ValueError): validate(self.arch, changed, [1], {'file': 'hash'})

    def test_mutation_rejection_gap_rejected(self):
        changed = copy.deepcopy(self.run_data); changed['comparisons'][0]['negative_rejections'].pop()
        with self.assertRaises(ValueError): validate(self.arch, changed, [1], {'file': 'hash'})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect():
    arch_path = ROOT / 'docs/ARCH_CONTRACT.json'
    if sha(arch_path) != ARCH_SHA256:
        raise ValueError('reviewed architecture v0.2 identity changed')
    state = json.loads((ROOT / '.harness/state.json').read_text())
    if state['task_states']['T011'] != 'completed' or 'T002' not in state['owner_reviews']:
        raise ValueError('required implementation/architecture review gate missing')
    paths = sorted((ROOT / 'evidence/toolchain_runs').glob('retire-*.json'))
    if not paths:
        raise FileNotFoundError('no actual independent comparison receipt')
    path = paths[-1]  # Never silently fall back from the newest failed run.
    run = json.loads(path.read_text())
    current = {name: sha(ROOT / name) for name in run['source_sha256']}
    seeds = json.loads((ROOT / 'config/rtl_checks.json').read_text())['unit_sims']['core']['seeds']
    matrix = validate(json.loads(arch_path.read_text()), run, seeds, current)
    backend = ROOT / run['backend']['path']
    if sha(backend) != run['backend']['sha256']:
        raise ValueError('actual simulator evidence changed')
    for row in run['comparisons']:
        actual = expected = None
        for name, value in row['artifacts'].items():
            artifact = ROOT / name
            if sha(artifact) != value:
                raise ValueError('trace artifact changed: ' + name)
            if artifact.name.startswith('observed_'): actual = json.loads(artifact.read_text())
            if artifact.name.startswith('expected_'): expected = json.loads(artifact.read_text())
        compare_trace(actual, expected)
    matrix.update(scope='L1 directed nonpipelined reference core; owner review pending',
                  architecture_sha256=ARCH_SHA256, independent_receipt=str(path.relative_to(ROOT)),
                  independent_receipt_sha256=sha(path), backend=run['backend'], seeds=seeds,
                  source_sha256=current, pins=run['pins'], no_zero_or_missing_check_pass=True)
    return matrix


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BaselinePolicyTests)
    if suite.countTestCases() == 0:
        raise RuntimeError('NOT RUN: no baseline checks')
    tests = unittest.TextTestRunner(verbosity=2).run(suite)
    record = {'task': 'T012', 'profile': 'isa-directed', 'status': 'FAIL', 'tests': tests.testsRun,
              'python': platform.python_version(), 'argv': [sys.executable, '-B', *sys.argv],
              'source_sha256': {'dv/integration/test_isa_directed.py': sha(Path(__file__))}}
    code = 1
    try:
        if not tests.wasSuccessful() or tests.skipped:
            raise ValueError('baseline policy tests failed/skipped')
        matrix = collect()
        date = datetime.now(timezone.utc).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
        output = ROOT / 'evidence/l1' / (date + '_matrix-' + stamp + '.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes((json.dumps(matrix, indent=2) + '\n').encode('utf-8'))
        record.update(status='PASS', matrix_path=str(output.relative_to(ROOT)), matrix_sha256=sha(output),
                      instruction_rows=len(matrix['instructions']), fault_rows=len(matrix['faults']))
        code = 0
    except FileNotFoundError as exc:
        record.update(status='NOT RUN', error=str(exc)); code = 125
    except (ValueError, KeyError, TypeError, OSError) as exc:
        record['error'] = str(exc)
    record['exit_code'] = code
    path = ROOT / 'evidence/toolchain_runs' / ('isa-directed-' + stamp + '.json')
    path.write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(record))
    return code


if __name__ == '__main__':
    sys.exit(main())
