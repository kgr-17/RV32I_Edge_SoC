#!/usr/bin/env python3
"""Bind the directed ISA/EEI matrix to the newest real pipeline comparison."""
import datetime as dt
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness
import rtl_checks

sys.path.insert(0, str(harness.ROOT))
from dv.integration.test_isa_complete import REQUIREMENTS, ERROR_WORDS, directed
from dv.integration.test_isa_directed import ARCH_SHA256, validate
from dv.reference.retire import compare_trace


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fence_counts(output):
    rows, totals = [], []
    for line in output.splitlines():
        if line.startswith('ISA_COMPLETE_FENCE_CASE '):
            m = re.fullmatch(r'ISA_COMPLETE_FENCE_CASE scenario=(\d+) wait=(\d+) effects=(\d+)', line)
            if not m:
                raise ValueError('Malformed actual FENCE case telemetry')
            rows.append(tuple(int(value) for value in m.groups()))
        elif line.startswith('ISA_COMPLETE_FENCE_TOTAL '):
            m = re.fullmatch(r'ISA_COMPLETE_FENCE_TOTAL cases=(\d+) wait=(\d+)', line)
            if not m:
                raise ValueError('Malformed actual FENCE total telemetry')
            totals.append(tuple(int(value) for value in m.groups()))
    if ([row[0] for row in rows] != [42, 43, 44, 45] or
            any(wait<1 or effects!=4 for _, wait, effects in rows) or
            totals != [(4, sum(row[1] for row in rows))]):
        raise ValueError('Missing/duplicate/vacuous/inconsistent actual FENCE cases')
    return [{'scenario': ident, 'wait_edges': wait, 'successful_memory_effects': effects}
            for ident, wait, effects in rows]


class FenceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.output = '\n'.join('ISA_COMPLETE_FENCE_CASE scenario=%d wait=2 effects=4' % n for n in range(42, 46))
        self.output += '\nISA_COMPLETE_FENCE_TOTAL cases=4 wait=8\n'

    def test_complete_literal_runtime_evidence(self):
        self.assertEqual(sum(row['wait_edges'] for row in fence_counts(self.output)), 8)

    def test_missing_duplicate_and_empty_rejected(self):
        for text in ('', self.output.replace('scenario=43', 'scenario=42'),
                     '\n'.join(self.output.splitlines()[1:])):
            with self.assertRaises(ValueError): fence_counts(text)

    def test_zero_wait_wrong_effects_and_unknown_rejected(self):
        for text in (self.output.replace('wait=2', 'wait=0', 1), self.output.replace('effects=4', 'effects=3', 1),
                     self.output.replace('wait=2', 'wait=x', 1)):
            with self.assertRaises(ValueError): fence_counts(text)

    def test_total_is_exact_not_a_pass_marker(self):
        for text in (self.output.replace('cases=4', 'cases=3'), self.output.replace('wait=8', 'wait=9'),
                     self.output + 'ISA_COMPLETE_FENCE_TOTAL cases=4 wait=8\n'):
            with self.assertRaises(ValueError): fence_counts(text)


def collect(checks):
    arch = harness.inside('docs/ARCH_CONTRACT.json')
    checks.require(sha(arch)==ARCH_SHA256, 'Owner-reviewed architecture identity')
    state = harness.read(harness.inside('.harness/state.json'))
    checks.require(state['task_states']['T018']=='completed' and 'T002' in state['owner_reviews'],
                   'Owner architecture and pipeline acceptance')
    paths = sorted(harness.inside('evidence/toolchain_runs').glob('isa-complete-*.json'))
    if not paths: raise rtl_checks.NotRun('No actual ISA/EEI pipeline comparison receipt')
    path = paths[-1]  # Never fall back from the newest failure.
    run = harness.read(path)
    current = {name: sha(harness.inside(name)) for name in run['source_sha256']}
    spec = rtl_checks.load_manifest()['unit_sims']['isa_complete']
    matrix = validate(harness.read(arch), run, spec['seeds'], current)
    checks.require(True, 'Fresh passing complete ISA/fault/event/state/mutation matrix')
    checks.result['source_sha256'] = current
    checks.result['pins'] = run['pins']
    checks.result['independent_receipt'] = {'path': path.relative_to(harness.ROOT).as_posix(), 'sha256': sha(path)}
    backend_path = harness.inside(run['backend']['path'])
    checks.require(sha(backend_path)==run['backend']['sha256'], 'Actual backend receipt hash')
    backend = harness.read(backend_path)
    checks.require(run['unit']=='isa_complete' and run['trace_prefix']=='ISA_COMPLETE' and backend['status']=='PASS',
                   'Actual executable pipeline backend identity')
    configured = {int(key): value for key, value in spec['error_words_by_scenario'].items()}
    checks.require(configured==ERROR_WORDS, 'Explicit in-range instruction/load/store error stimuli')
    semantic = {name: {'requirement': name, 'seeds': {}} for name in REQUIREMENTS}
    fence = []
    for comparison in run['comparisons']:
        seed = comparison['seed']; actual = expected = None
        for name, value in comparison['artifacts'].items():
            artifact = harness.inside(name)
            checks.require(sha(artifact)==value, 'Normalized trace hash '+str(seed)+' '+artifact.name)
            if artifact.name.startswith('observed_'): actual = harness.read(artifact)
            elif artifact.name.startswith('expected_'): expected = harness.read(artifact)
        compare_trace(actual, expected)
        _, _, plan = directed(seed)
        observed_ids = {event[1] for event in actual if event[0]=='F'}
        missing = {row['scenario'] for row in plan} - observed_ids
        checks.require(not missing, 'Actual semantic scenarios seed='+str(seed)+' missing='+str(sorted(missing)))
        for name in REQUIREMENTS:
            rows = [row for row in plan if row['requirement']==name]
            # Ignored fields are the same four runtime-checked FENCE programs.
            if name=='fence_ignored_fields': rows = [row for row in plan if row['requirement']=='fence_drain']
            checks.require(bool(rows), 'Nonempty semantic cases '+name+' seed='+str(seed))
            semantic[name]['seeds'][str(seed)] = rows
        command = backend['commands'][comparison['backend_command_index']]
        checks.require(rtl_checks.successful(command), 'Successful actual FENCE trace producer '+str(seed))
        fence.append({'seed': seed, 'cases': fence_counts(command['stdout'])})
        for ident, code in ((46, 3), (47, 5), (48, 7)):
            events = [event for event in actual if event[:2]==['F', ident]]
            checks.require(len(events)==1 and events[0][4]==code, 'Actual injected fault '+str(seed)+'/'+str(ident))
    matrix.update(scope='Directed project RV32I 2.1 / v0.2 fault-halt EEI; owner T041 review pending; no certification',
                  independent_receipt=checks.result['independent_receipt'], backend=run['backend'],
                  architecture_sha256=ARCH_SHA256, seeds=spec['seeds'], source_sha256=current, pins=run['pins'],
                  semantic_requirements=list(semantic.values()), runtime_fence=fence, error_words_by_scenario=spec['error_words_by_scenario'],
                  ram_sample_scope='32 words at0x10000 per case; full64KiB RAM separately checked in SV')
    output = harness.inside('evidence/isa/'+harness.today()+'_matrix-'+checks.result['started_utc']+'.json')
    harness.atomic(output, matrix)
    checks.result['matrix'] = {'path': output.relative_to(harness.ROOT).as_posix(), 'sha256': sha(output)}
    checks.require(all(sha(harness.inside(name))==value for name, value in current.items()), 'Matrix sources unchanged')


def main():
    checks = rtl_checks.Checks('isa-matrix', task='T041', scope='Actual pipeline ISA/EEI traceability and runtime FENCE evidence')
    checks.result['excluded'] = ['RISC-V certification', 'privileged ISA/interrupts', 'SoC/MMIO', 'formal', 'timing', 'hardware', 'ASIC']
    code = 1
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(FenceEvidenceTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        checks.require(result.testsRun==4 and result.wasSuccessful() and not result.skipped, 'FENCE evidence policy tests')
        collect(checks)
        checks.result['status'] = 'PASS'; code = 0
    except (rtl_checks.NotRun, FileNotFoundError) as exc:
        checks.result.update(status='NOT RUN', error=str(exc)); code = 125
    except (RuntimeError, ValueError, KeyError, TypeError, OSError, AssertionError, harness.Stop) as exc:
        checks.result.update(status='FAIL', error=str(exc))
    checks.result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(); checks.save()
    print(json.dumps({'status': checks.result['status'], 'evidence': checks.path.relative_to(harness.ROOT).as_posix(),
                      'matrix': checks.result.get('matrix'), 'error': checks.result.get('error')}))
    return code


if __name__=='__main__': sys.exit(main())
