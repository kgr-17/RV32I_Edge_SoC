#!/usr/bin/env python3
"""Reject zero-test, missing-tool, crash and witness-free formal claims."""
import unittest
from formal_checks import accepted,has_properties


class FormalAcceptanceTests(unittest.TestCase):
    def test_empty_or_wrong_kind_property_model_cannot_satisfy_gate(self):
        self.assertFalse(has_properties([]));self.assertFalse(has_properties(['; empty model']))
        self.assertFalse(has_properties(['; yosys-smt2-cover 0 witness']))
        self.assertTrue(has_properties(['; yosys-smt2-assert 0 property']))
        self.assertTrue(has_properties(['; yosys-smt2-cover 0 witness'],cover=True))

    def test_positive_requires_actual_process_and_status(self):
        good=dict(status='PASS',exit_code=0)
        self.assertTrue(accepted(good,'PASS','PASS',[]))
        for rec,status in ((dict(status='NOT RUN',exit_code=125),'PASS'),(dict(status='FAIL',exit_code=4294967295),'PASS'),
                           (good,None),(good,'FAIL'),(dict(status='TIMEOUT',exit_code=124),'PASS')):
            self.assertFalse(accepted(rec,status,'PASS',[]))

    def test_cover_requires_nonempty_witness(self):
        good=dict(status='PASS',exit_code=0)
        self.assertFalse(accepted(good,'PASS','PASS',[],cover=True))
        self.assertTrue(accepted(good,'PASS','PASS',['trace.vcd'],cover=True))

    def test_negative_requires_counterexample_not_native_failure(self):
        self.assertTrue(accepted(dict(status='FAIL',exit_code=2),'FAIL','FAIL',['trace.vcd']))
        for rec,status,witness in ((dict(status='FAIL',exit_code=2),'FAIL',[]),
                                   (dict(status='FAIL',exit_code=4294967295),'FAIL',['trace.vcd']),
                                   (dict(status='PASS',exit_code=0),'PASS',['trace.vcd']),
                                   (dict(status='NOT RUN',exit_code=125),'FAIL',['trace.vcd'])):
            self.assertFalse(accepted(rec,status,'FAIL',witness))


if __name__=='__main__':unittest.main(verbosity=2)
