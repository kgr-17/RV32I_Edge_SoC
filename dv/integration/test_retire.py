#!/usr/bin/env python3
"""Anchored independent ISS and trace rejection tests; no RTL expression imports."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dv.reference.rv32_iss import RV32ISS, Fault, Retirement
from dv.reference.retire import TraceMismatch, compare_trace, expected_trace, observed_trace, stimulus_images


def image_of(words):
    return {index * 4 + n: byte for index, word in enumerate(words) for n, byte in enumerate(word.to_bytes(4, 'little'))}


class IssTests(unittest.TestCase):
    def test_literal_arithmetic_and_signed_shift(self):
        iss = RV32ISS(image_of([0x800000b7, 0xfff00113, 0x0020a1b3, 0x4020d233, 0x0020d2b3, 0x73]))
        events, fault = iss.run()
        self.assertEqual([event.rd_data for event in events], [0x80000000, 0xffffffff, 1, 0xffffffff, 1])
        self.assertEqual(fault, Fault(20, 0x73, 8, 0))
        self.assertEqual(iss.regs[:6], [0, 0x80000000, 0xffffffff, 1, 0xffffffff, 1])

    def test_byte_store_extension_full_word_and_load_x0_effect(self):
        iss = RV32ISS(image_of([0x000100b7, 0xf8000113, 0x002081a3, 0x00308183, 0x0000a003, 0x73]))
        events, _ = iss.run()
        self.assertEqual(events[2].fields()[7:], (1, 1, 0x10003, 8, 0x80000000, 0))
        self.assertEqual(events[3].rd_data, 0xffffff80)
        self.assertEqual(events[4].mem_rdata, 0x80000000)
        self.assertEqual((events[4].rd_write, events[4].rd_data), (0, 0))
        self.assertEqual(len(iss.memory_events), 3)
        self.assertEqual(iss.memory[0x10003], 0x80)

    def test_bad_target_is_fault_before_link_and_jalr_clear(self):
        iss = RV32ISS(image_of([0x002000ef]))
        self.assertEqual(iss.step(), Fault(0, 0x002000ef, 2, 2))
        self.assertEqual(iss.regs, [0] * 32)
        iss = RV32ISS(image_of([0x00900093, 0x00008167, 0x73]))
        events, fault = iss.run()
        self.assertEqual((events[1].next_pc, events[1].rd_data), (8, 8))
        self.assertEqual(fault.pc, 8)

    def test_fault_priority_error_effects_and_x0_access_fault(self):
        iss = RV32ISS(image_of([0x0000a023]))  # SW x0,0(x1)
        iss.regs[1] = 0x20001
        before = dict(iss.memory)
        self.assertEqual(iss.step().code, 6)  # alignment before unmapped check
        self.assertEqual(iss.memory, before)
        iss = RV32ISS(image_of([0x0000a003]))  # LW x0,0(x1)
        iss.regs[1] = 0x20000
        self.assertEqual(iss.step(), Fault(0, 0x0000a003, 5, 0x20000))
        self.assertEqual(iss.order, 0)
        iss = RV32ISS(image_of([0x0000a023]), error_words=(0x10000,))
        iss.regs[1] = 0x10000
        self.assertEqual(iss.step().code, 7)
        self.assertNotIn(0x10000, iss.memory)

    def test_reserved_extensions_and_fence_fields(self):
        for word in (0x02000033, 0x30001073, 0x0000100f, 0x02001013, 0xffffffff, 0):
            with self.subTest(word=word):
                iss = RV32ISS(image_of([word]))
                self.assertEqual(iss.step(), Fault(0, word, 1, word))
        iss = RV32ISS(image_of([0xffff8f8f, 0x00100073]))
        events, fault = iss.run()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].rd_write, 0)
        self.assertEqual(fault.code, 9)

    def test_reset_retains_committed_memory_and_sticky_fault(self):
        iss = RV32ISS(image_of([0x000100b7, 0x00100113, 0x0020a023, 0x73]))
        iss.run()
        frozen = iss.step()
        self.assertIs(iss.step(), frozen)
        self.assertEqual(iss.memory[0x10000], 1)
        iss.reset()
        self.assertEqual((iss.pc, iss.order, iss.regs), (0, 0, [0] * 32))
        self.assertEqual(iss.memory[0x10000], 1)

    def test_instruction_access_error_and_bound(self):
        iss = RV32ISS(error_words=(0,))
        self.assertEqual(iss.step(), Fault(0, 0, 3, 0))
        iss = RV32ISS(image_of([0x0000006f]))  # JAL x0,0
        with self.assertRaises(RuntimeError):
            iss.run(limit=10)


class ComparisonTests(unittest.TestCase):
    def test_stimulus_ignores_hand_expected_fields(self):
        header = [0] * 13
        word = [1, 0, 0x73] + [0] * 10
        expected = [3] + [0xdeadbeef] * 12
        end = [4] + [0] * 12
        content = '\n'.join(' '.join('%x' % n for n in row) for row in (header, word, expected, end))
        cases = stimulus_images(content)
        trace, coverage, summary = expected_trace(cases)
        self.assertEqual(trace[0], ('F', 0, 0, 0x73, 8, 0))
        self.assertEqual(coverage['op:ECALL'], 1)
        self.assertEqual(summary[0]['retirements'], 0)

    def test_observed_parser_and_real_mismatch_rejection(self):
        text = 'CORE_RETIRE 0 0000000000000000 0 00100093 4 1 1 1 0 0 0 0 0 0\n'
        events = observed_trace(text)
        compare_trace(events, events)
        corrupted = [tuple(list(events[0][:-1]) + [1])]
        with self.assertRaises(TraceMismatch):
            compare_trace(corrupted, events)
        for actual in ([], events + events):
            with self.assertRaises(TraceMismatch):
                compare_trace(actual, events)
        for text in ('', 'CORE_RETIRE 0 00', 'CORE_GPR 0 1 xxxxxxxx'):
            with self.assertRaises(TraceMismatch):
                observed_trace(text)

    def test_reordering_fault_and_terminal_state_mutation_rejected(self):
        events = [('F', 0, 0, 0x73, 8, 0), ('G', 0, 1, 0), ('M', 0, 0, 0)]
        for changed in ([events[1], events[0], events[2]], [events[0], events[1], ('M', 0, 0, 1)]):
            with self.assertRaises(TraceMismatch):
                compare_trace(changed, events)


if __name__ == '__main__':
    unittest.main(verbosity=2)
