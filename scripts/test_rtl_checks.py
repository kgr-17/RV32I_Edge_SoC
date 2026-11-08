#!/usr/bin/env python3
"""Mutation tests for evidence acceptance and the independent vector oracle."""
import copy
import tempfile
import unittest
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from pathlib import Path
import rtl_checks


class CheckPolicyTests(unittest.TestCase):
    def test_legacy_interface_definitions_are_scoped_to_exact_lint_units(self):
        manifest=rtl_checks.load_manifest()
        for bad in ('arbitrary',['DISABLE_CHECKS'],['RV32_CORE_LEGACY_PORTS'],[1],True):
            changed=copy.deepcopy(manifest);changed['lint_designs'][0]['defines']=bad
            with mock.patch.object(rtl_checks.harness,'read',return_value=changed):
                with self.assertRaises(ValueError):rtl_checks.load_manifest()
        for top,definitions in rtl_checks.LEGACY_LINT_DEFINES.items():
            self.assertEqual(next(d for d in manifest['lint_designs'] if d['top']==top)['defines'],definitions)
    def test_concurrent_evidence_is_complete_with_valid_command_indices(self):
        root = rtl_checks.harness.inside('build/evidence_concurrency_tests')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(root)) as folder:
            c = object.__new__(rtl_checks.Checks)
            c._lock = threading.RLock()
            c.path = Path(folder)/'result.json'
            c.result = {'commands': [], 'checks': []}
            def native(argv, directory, timeout):
                time.sleep(0.005)
                return {'argv': argv, 'status': 'PASS', 'exit_code': 0}
            def job(index):
                record = c.command([str(index)], Path(folder), 15)
                c.require(True, str(index), record)
            with mock.patch.object(rtl_checks.tool_runner, 'run', side_effect=native):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    list(pool.map(job, range(12)))
            evidence = json.loads(c.path.read_text())
            self.assertEqual(len(evidence['commands']), 12)
            self.assertEqual(len(evidence['checks']), 12)
            for check in evidence['checks']:
                self.assertEqual(evidence['commands'][check['command_index']]['argv'], [check['name']])

    def test_bounded_lint_runs_every_design_and_retains_failures(self):
        checks = object.__new__(rtl_checks.Checks)
        guard = threading.Lock()
        activity = {'live': 0, 'peak': 0, 'seen': []}
        def job(sources, top, manifest, **kwargs):
            with guard:
                activity['live'] += 1
                activity['peak'] = max(activity['peak'], activity['live'])
                activity['seen'].append((top, kwargs['timeout']))
            time.sleep(0.02)
            with guard:
                activity['live'] -= 1
            if top == 'bad':
                raise rtl_checks.NotRun('missing tool')
        checks.lint = job
        manifest = {'lint_designs': [dict(top=n, sources=[n], timeout_seconds=45)
                                    for n in ('a', 'bad', 'c', 'd')]}
        with self.assertRaisesRegex(rtl_checks.NotRun, 'missing tool'):
            checks.lint_manifest(manifest)
        self.assertCountEqual(activity['seen'], [(n, 45) for n in ('a', 'bad', 'c', 'd')])
        self.assertEqual(activity['live'], 0)
        self.assertEqual(activity['peak'], 2)

    def setUp(self):
        self.record = {'status': 'PASS', 'exit_code': 0, 'stdout': 'COMPLETED\n', 'stderr': ''}

    def test_positive_completion(self):
        self.assertTrue(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_memory_initialization_inputs_must_be_unique_and_present(self):
        manifest=rtl_checks.load_manifest()
        for invalid in ('not-a-list',[7],['wrong.txt'],['a/rom.mem','b/rom.mem']):
            changed=copy.deepcopy(manifest);changed['lint_designs'][0]['memory_files']=invalid
            with mock.patch.object(rtl_checks.harness,'read',return_value=changed):
                with self.assertRaises(ValueError):rtl_checks.load_manifest()
        changed=copy.deepcopy(manifest);changed['lint_designs'][0]['memory_files']=['missing_t026_image.mem']
        with mock.patch.object(rtl_checks.harness,'read',return_value=changed):
            with self.assertRaises(rtl_checks.NotRun):rtl_checks.load_manifest()

    def test_invalid_synthesis_budgets_rejected(self):
        manifest=rtl_checks.load_manifest()
        for value in (0,-1,True,121,float('inf')):
            changed=copy.deepcopy(manifest);changed['lint_designs'][0]['timeout_seconds']=value
            with mock.patch.object(rtl_checks.harness,'read',return_value=changed):
                with self.assertRaises(ValueError):rtl_checks.load_manifest()

    def test_zero_tests_or_missing_completion_rejected(self):
        self.record['stdout'] = 'simulation exited normally\n'
        self.assertFalse(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_duplicate_completion_rejected(self):
        self.record['stdout'] *= 2
        self.assertFalse(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_error_despite_exit_zero_rejected(self):
        for diagnostic in ('ERROR: bad', 'Fatal: bad', 'WARNING: width mismatch'):
            with self.subTest(diagnostic=diagnostic):
                self.record['stderr'] = diagnostic
                self.assertFalse(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_timeout_or_nonzero_rejected(self):
        for status in ('TIMEOUT', 'FAIL', 'NOT RUN'):
            self.record['status'] = status
            self.assertFalse(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_nonzero_cannot_be_accepted_as_pass(self):
        self.record['exit_code'] = 7
        self.assertFalse(rtl_checks.successful(self.record, 'COMPLETED'))

    def test_unregistered_production_source_not_run(self):
        with mock.patch.object(Path, 'rglob', return_value=[rtl_checks.harness.ROOT / 'rtl/orphan.sv']):
            with self.assertRaises(rtl_checks.NotRun):
                rtl_checks.load_manifest()

    def test_replay_and_seed_variation(self):
        self.assertEqual(rtl_checks.vectors(1), rtl_checks.vectors(1))
        self.assertNotEqual(rtl_checks.vectors(1), rtl_checks.vectors(2))

    def test_oracle_reset_wins_and_hold(self):
        rows = [[int(value, 16) for value in line.split()] for line in rtl_checks.vectors(1).splitlines()]
        self.assertEqual(len(rows), 134)
        self.assertEqual([row[3] for row in rows[:6]], [0, 0, 0x80000001, 0x80000001, 0, 0])

    def test_empty_manifest_rejected(self):
        manifest = rtl_checks.load_manifest()
        for field in ('designs', 'seeds'):
            changed = copy.deepcopy(manifest)
            changed[field] = []
            with mock.patch.object(rtl_checks.harness, 'read', return_value=changed):
                with self.assertRaises(ValueError):
                    rtl_checks.load_manifest()

    def test_missing_source_not_run(self):
        manifest = rtl_checks.load_manifest()
        manifest['designs'][0]['sources'] = ['rtl/missing_unit.sv']
        with mock.patch.object(rtl_checks.harness, 'read', return_value=manifest):
            with self.assertRaises(rtl_checks.NotRun):
                rtl_checks.load_manifest()

    def test_invalid_seed_rejected(self):
        manifest = rtl_checks.load_manifest()
        for seed in (0, -1, True, 2**31):
            changed = copy.deepcopy(manifest)
            changed['seeds'] = [seed]
            with mock.patch.object(rtl_checks.harness, 'read', return_value=changed):
                with self.assertRaises(ValueError):
                    rtl_checks.load_manifest()

    def test_production_lint_only_designs_registered_without_fixture_protocol(self):
        manifest = rtl_checks.load_manifest()
        self.assertTrue(any('rtl/core/decoder.sv' in design['sources']
                            for design in manifest['lint_designs']))
        self.assertTrue(all('rtl/core/decoder.sv' not in design['sources']
                            for design in manifest['designs']))

    def test_missing_lint_only_source_is_not_run(self):
        manifest = rtl_checks.load_manifest()
        manifest['lint_designs'][0]['sources'] = ['rtl/missing_decoder.sv']
        with mock.patch.object(rtl_checks.harness, 'read', return_value=manifest):
            with self.assertRaises(rtl_checks.NotRun):
                rtl_checks.load_manifest()

    def test_xsim_batch_does_not_receive_equals_arguments(self):
        root = rtl_checks.harness.inside('build/argument_transport_tests')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(root)) as name:
            directory = Path(name)
            checks = object.__new__(rtl_checks.Checks)
            checks.vendor = mock.Mock(return_value={})
            checks.save = mock.Mock()
            intended = ['snapshot', '--sv_seed', '1', '--testplusarg', 'SEED=1',
                        '--testplusarg', 'VECTORS=C:\\project\\vector_file.txt']
            record = checks.xsim(intended, directory, 15, 'transport')
            sent = checks.vendor.call_args[0][1]
            self.assertEqual(sent[:2], ['snapshot', '--file'])
            self.assertFalse(any('=' in arg for arg in sent))
            normalized = [arg.replace('\\', '/') for arg in intended]
            self.assertEqual(Path(sent[2]).read_text(encoding='utf-8').splitlines(), normalized[1:])
            self.assertEqual(record['argument_file']['intended_argv'], normalized)


if __name__ == '__main__':
    unittest.main(verbosity=2)
