#!/usr/bin/env python3
"""Literal-state anchors and negative observed-effect scoreboard checks."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dv.reference.retire import expected_trace
from dv.reference.scoreboard import ArchitecturalScoreboard, ScoreboardMismatch, check_trace, inject_actual_errors


class ScoreboardTests(unittest.TestCase):
    def setUp(self):
        # LUI x1,0x10; ADDI x2,x0,-1; SW x2,0(x1); LB x3,3(x1); ECALL.
        words = [0x000100b7, 0xfff00113, 0x0020a023, 0x00308183, 0x73]
        image = {4*n+k: byte for n, word in enumerate(words) for k, byte in enumerate(word.to_bytes(4,'little'))}
        self.cases = [{'id': 42, 'image': image}]
        self.trace = expected_trace(self.cases)[0]

    def test_literal_committed_register_and_memory_state(self):
        result = check_trace(self.cases, self.trace)
        self.assertEqual((result['retirements'], result['stores'], result['loads'], result['faults']), (4, 1, 1, 1))
        self.assertIn(('G', 42, 3, 0xffffffff), self.trace)
        self.assertIn(('M', 42, 0, 0xffffffff), self.trace)

    def test_all_six_observed_error_injections_rejected(self):
        rejected = inject_actual_errors(self.cases, self.trace)
        self.assertEqual(len(rejected), 6)
        self.assertTrue(all(row['diagnostic'] for row in rejected))

    def test_fault_payload_and_event_reorder_rejected(self):
        for index in (4, 5):
            changed = list(self.trace); row = list(changed[index]); row[-1] ^= 1; changed[index] = row
            with self.assertRaises(ScoreboardMismatch): check_trace(self.cases, changed)
        with self.assertRaises(ScoreboardMismatch): check_trace(self.cases, self.trace[::-1])

    def test_failure_cannot_be_resumed_as_a_pass(self):
        scoreboard = ArchitecturalScoreboard(self.cases)
        with self.assertRaises(ScoreboardMismatch): scoreboard.observe(('F', 42, 0, 0, 8, 0))
        with self.assertRaises(ScoreboardMismatch): scoreboard.observe(self.trace[0])
        with self.assertRaises(ScoreboardMismatch): scoreboard.finish()

    def test_missing_dump_or_duplicate_word_rejected(self):
        for changed in (self.trace[:-1], self.trace[:6]+self.trace[5:]):
            with self.assertRaises(ScoreboardMismatch): check_trace(self.cases, changed)

    def test_empty_duplicate_scenarios_and_extra_events_rejected(self):
        for cases in ([], self.cases+self.cases):
            with self.assertRaises(ValueError): ArchitecturalScoreboard(cases)
        with self.assertRaises(ScoreboardMismatch): check_trace(self.cases, [])
        with self.assertRaises(ScoreboardMismatch): check_trace(self.cases, self.trace+self.trace[:1])


if __name__=='__main__': unittest.main(verbosity=2)
