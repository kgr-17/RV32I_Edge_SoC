#!/usr/bin/env python3
"""Prevent false acceptance of disabled, wrong, vacuous or interrupted assertions."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from assertion_checks import accept_injection, property_hits, HITS, NEGATIVES


class AssertionPolicyTests(unittest.TestCase):
    def record(self,text='Fatal: CORE_ASSERT_FAIL P_X0_A',status='PASS',exit_code=0):
        return dict(stdout=text,stderr='',status=status,exit_code=exit_code)

    def test_real_fatal_can_exit_zero_or_one(self):
        for code,status in ((0,'PASS'),(1,'FAIL')):
            self.assertTrue(accept_injection(self.record(status=status,exit_code=code),'P_X0_A'))

    def test_wrong_missing_or_multiple_property_rejected(self):
        for text in ('','Fatal: something else','CORE_ASSERT_FAIL P_X0_B',
                     'CORE_ASSERT_FAIL P_X0_A\nCORE_ASSERT_FAIL P_X0_A',
                     'CORE_ASSERT_FAIL P_X0_A\nCORE_ASSERT_FAIL P_RESET_STATE'):
            self.assertFalse(accept_injection(self.record(text),'P_X0_A'))

    def test_timeout_crash_and_false_control_rejected(self):
        for row in (self.record(status='TIMEOUT',exit_code=124), self.record(status='NOT RUN',exit_code=125),
                    self.record(status='FAIL',exit_code=4294967295),
                    self.record('CORE_ASSERT_FAIL P_X0_A\nPROPERTY_CONTROL_PASS'),
                    self.record('CORE_ASSERT_FAIL P_X0_A\nInjection was not detected'),
                    self.record('CORE_ASSERT_FAIL P_X0_A\nERROR: unrelated compilation error')):
            self.assertFalse(accept_injection(row,'P_X0_A'))

    def test_witnesses_are_seed_bound_positive_and_exact_retire_count(self):
        text='ASSERTIONS_PROPERTY_HITS seed=7'+''.join(' '+key+'='+('42' if key=='retires' else '1') for key in HITS)
        self.assertEqual(property_hits(text,7,42)['retires'],42)
        for changed,seed,count in ((text,1,42),(text,7,43),(text+'\n'+text,7,42),
                                   (text.replace('i_holds=1','i_holds=0'),7,42),('',7,42)):
            with self.assertRaises(ValueError):property_hits(changed,seed,count)

    def test_each_property_family_has_attributable_negative(self):
        self.assertEqual(set(NEGATIVES.values()),{'P_X0_A','P_X0_B','P_RETIRE_ORDER','P_RETIRE_DEST',
            'P_RESET_QUIET','P_RESET_STATE','P_I_STABLE','P_D_STABLE','P_I_SINGLE','P_D_SINGLE',
            'P_I_RESPONSE','P_D_RESPONSE','P_FAULT_STICKY'})

    def test_instrumented_bench_preserves_every_original_guard(self):
        root=Path(__file__).resolve().parents[2]
        old=(root/'dv/random/tb_random.sv').read_text().replace('RANDOM_','ASSERTIONS_')
        new=(root/'dv/assertions/tb_assertions.sv').read_text()
        guards=[line.strip() for line in old.splitlines() if 'fail(' in line or '$fatal(' in line]
        self.assertTrue(all(line in new for line in guards))


if __name__=='__main__':unittest.main(verbosity=2)
