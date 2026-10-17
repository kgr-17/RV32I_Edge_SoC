#!/usr/bin/env python3
"""Mutation tests for evidence acceptance and the independent vector oracle."""
import copy
import tempfile
import unittest
from unittest import mock
from pathlib import Path
import rtl_checks


class CheckPolicyTests(unittest.TestCase):
    def setUp(self):
        self.record = {'status': 'PASS', 'exit_code': 0, 'stdout': 'COMPLETED\n', 'stderr': ''}

    def test_positive_completion(self):
        self.assertTrue(rtl_checks.successful(self.record, 'COMPLETED'))

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
