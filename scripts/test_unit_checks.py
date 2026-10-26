#!/usr/bin/env python3
"""Unit-driver configuration guards, distinct from DUT correctness tests."""
import copy
import unittest
import unit_checks as u


class UnitPolicyTests(unittest.TestCase):
    def setUp(self):
        self.manifest = u.rtl_checks.load_manifest()

    def test_actual_spec(self):
        self.assertEqual(u.unit_spec(self.manifest, 'alu')['task'], 'T005')

    def test_corrupt_expected_keeps_program_for_core_and_row_for_units(self):
        content = '00 00000000\n01 12345678\n04 00000000\n'
        self.assertEqual(u.corrupt_expected(content), '00 1\n')
        self.assertEqual(u.corrupt_expected(content, True), '00 1\n01 12345678\n04 00000000\n')

    def test_corrupt_empty_input_rejected(self):
        with self.assertRaises(ValueError): u.corrupt_expected('')

    def test_missing_unit_not_run(self):
        with self.assertRaises(u.rtl_checks.NotRun): u.unit_spec(self.manifest, 'absent')

    def test_invalid_seeds(self):
        for seeds in ([], [1, 1], [0], [True], [2**31]):
            changed = copy.deepcopy(self.manifest); changed['unit_sims']['alu']['seeds'] = seeds
            with self.assertRaises(ValueError): u.unit_spec(changed, 'alu')

    def test_missing_reference_not_run(self):
        changed = copy.deepcopy(self.manifest); changed['unit_sims']['alu']['reference'] = 'dv/missing.py'
        with self.assertRaises(u.rtl_checks.NotRun): u.unit_spec(changed, 'alu')

    def test_wave_and_identifier_injection_rejected(self):
        changed = copy.deepcopy(self.manifest); changed['unit_sims']['alu']['waves'] = ['/tb_alu/a;exit']
        with self.assertRaises(ValueError): u.unit_spec(changed, 'alu')
        for value in ('../escape', 'alu;exit', 'alu name'):
            with self.assertRaises(ValueError): u.identifier(value)


if __name__ == '__main__': unittest.main(verbosity=2)
