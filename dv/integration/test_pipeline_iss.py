#!/usr/bin/env python3
"""Independent pipeline trace checks, including hand-expectation independence."""
from collections import Counter
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from dv.reference.retire import TraceMismatch, compare_trace, expected_trace, observed_trace, stimulus_images
from dv.integration.test_backpressure import generate
from retire_checks import profile_for
import json


class PipelineIssTests(unittest.TestCase):
    def test_backend_identity_cannot_be_relabelled(self):
        self.assertEqual(profile_for('core'), ('retire', 'T011', 'CORE', 'reference core'))
        self.assertEqual(profile_for('backpressure'), ('pipeline-iss', 'T018', 'BACKPRESSURE', 'executable pipeline'))
        for name in ('pipeline', '', '../core'):
            with self.assertRaises(ValueError):
                profile_for(name)

    def test_literal_pipeline_events_normalize_to_reference_format(self):
        text = ('BACKPRESSURE_RETIRE 7 0000000000000000 0 00100093 4 1 1 1 0 0 0 0 0 0\n'
                'BACKPRESSURE_FAULT 7 4 00000073 8 0\n'
                'BACKPRESSURE_GPR 7 1 00000001\nBACKPRESSURE_RAM 7 0 00000000\n')
        events = observed_trace(text, 'BACKPRESSURE')
        self.assertEqual(events, [('R', 7, 0, 0, 0x00100093, 4, 1, 1, 1, 0, 0, 0, 0, 0, 0),
                                  ('F', 7, 4, 0x73, 8, 0), ('G', 7, 1, 1), ('M', 7, 0, 0)])
        self.assertEqual(events, observed_trace(text.replace('BACKPRESSURE_', 'CORE_')))

    def test_wrong_or_unregistered_prefix_is_rejected(self):
        with self.assertRaises(TraceMismatch):
            observed_trace('CORE_FAULT 0 0 73 8 0', 'BACKPRESSURE')
        with self.assertRaises(ValueError):
            observed_trace('BACKPRESSURE_FAULT 0 0 73 8 0', 'BACK')

    def test_malformed_and_unknown_actual_bits_are_rejected(self):
        for text in ('', 'BACKPRESSURE_RETIRE 0 0', 'BACKPRESSURE_FAULT 0 0 73 x 0',
                     'BACKPRESSURE_RAM 0 1 xxxxxxxx', 'BACKPRESSURE_GPR 0 x 0'):
            with self.assertRaises(TraceMismatch):
                observed_trace(text, 'BACKPRESSURE')

    def test_fault_state_reorder_and_retirement_mutations_rejected(self):
        original = [('R', 1, *([0] * 13)), ('F', 1, 4, 0x73, 8, 0), ('G', 1, 1, 0), ('M', 1, 0, 0)]
        for index in range(len(original)):
            changed = list(original)
            changed[index] = tuple(list(changed[index][:-1]) + [changed[index][-1] ^ 1])
            with self.assertRaises(TraceMismatch):
                compare_trace(changed, original)
        for changed in ([], original + original[:1], original[::-1]):
            with self.assertRaises(TraceMismatch):
                compare_trace(changed, original)

    def test_all_configured_programs_have_independent_isa_and_fault_coverage(self):
        manifest = json.loads((ROOT / 'config/rtl_checks.json').read_text())
        required = {'op:' + name for name in json.loads((ROOT / 'docs/ARCH_CONTRACT.json').read_text())['isa']['instructions']}
        required.update('fault:%d' % n for n in range(1, 10))
        for seed in manifest['unit_sims']['backpressure']['seeds']:
            trace, coverage, cases = expected_trace(stimulus_images(generate(seed)[0]))
            self.assertEqual(len(cases), 42)
            self.assertEqual(Counter(event[0] for event in trace), {'R': 502, 'F': 42, 'G': 1302, 'M': 1344})
            self.assertTrue(all(coverage.get(key, 0) > 0 for key in required))

    def test_all_hand_authored_expected_rows_are_ignored_by_iss(self):
        text = generate(7)[0]
        mutated = []
        for line in text.splitlines():
            words = line.split()
            if int(words[0], 16) == 3:
                words[1:] = ['deadbeef'] * 12
            mutated.append(' '.join(words))
        before = expected_trace(stimulus_images(text))
        after = expected_trace(stimulus_images('\n'.join(mutated)))
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
