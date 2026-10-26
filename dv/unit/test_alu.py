#!/usr/bin/env python3
"""Independent integer-arithmetic ALU oracle; no RTL imports or expression parsing."""
from collections import Counter
import random
import unittest

MASK = (1 << 32) - 1
# Stable public operation IDs from the package interface, specified independently.
OPERATIONS = {19: 'ADD', 20: 'SLT', 21: 'SLTU', 22: 'XOR', 23: 'OR', 24: 'AND',
              25: 'SLL', 26: 'SRL', 27: 'SRA', 28: 'ADD', 29: 'SUB', 30: 'SLL',
              31: 'SLT', 32: 'SLTU', 33: 'XOR', 34: 'SRL', 35: 'SRA', 36: 'OR', 37: 'AND'}
REQUIRED_BINS = ['op:' + str(op) for op in OPERATIONS] + ['unsupported']
EDGES = [0, 1, 2, 15, 31, 32, 33, 0x7ffffffe, 0x7fffffff, 0x80000000,
         0x80000001, 0xfffffffe, MASK, 0x55555555, 0xaaaaaaaa, 0xffff0000, 0xffff]


def signed(value):
    return value if value < 1 << 31 else value - (1 << 32)


def oracle(op, a, b):
    if op not in OPERATIONS:
        return 0, 0
    operation = OPERATIONS[op]
    # Multiplication/floor division avoid copying RTL shift operators. Python's
    # unbounded values are reduced modulo XLEN only at the result boundary.
    amount = b % 32
    if operation == 'ADD': value = a + b
    elif operation == 'SUB': value = a - b
    elif operation == 'SLT': value = int(signed(a) < signed(b))
    elif operation == 'SLTU': value = int(a < b)
    elif operation == 'SLL': value = a * (2 ** amount)
    elif operation == 'SRL': value = a // (2 ** amount)
    elif operation == 'SRA': value = signed(a) // (2 ** amount)
    elif operation == 'XOR': value = a ^ b
    elif operation == 'OR': value = a | b
    elif operation == 'AND': value = a & b
    else: raise AssertionError('Missing independent operation')
    return value % (1 << 32), 1


def generate(seed):
    rng = random.Random(seed)
    rows, coverage = [], Counter()

    def add(op, a, b, group):
        result, supported = oracle(op, a, b)
        rows.append((op, a, b, result, supported))
        coverage['op:' + str(op) if supported else 'unsupported'] += 1
        coverage['group:' + group] += 1

    small = [value & MASK for value in range(-32, 32)]
    for op in OPERATIONS:
        for a in small:
            for b in small:
                add(op, a, b, 'exhaustive-small')
        for a in EDGES:
            for b in EDGES:
                add(op, a, b, 'edge-cross')
        if OPERATIONS[op] in ('SLL', 'SRL', 'SRA'):
            for a in EDGES:
                for amount in range(32):
                    for upper in (0, 32, 0x80000000, 0xffffffe0):
                        add(op, a, upper + amount, 'shift-mask')
        for _ in range(1024):
            add(op, rng.getrandbits(32), rng.getrandbits(32), 'random-legal')
    for op in set(range(64)) - OPERATIONS.keys():
        for a, b in ((0, 0), (MASK, MASK), (0x80000000, 31)):
            add(op, a, b, 'unsupported-directed')
        for _ in range(32):
            add(op, rng.getrandbits(32), rng.getrandbits(32), 'unsupported-random')
    assert all(coverage[name] > 0 for name in REQUIRED_BINS)
    rng.shuffle(rows)
    return ''.join('%02x %08x %08x %08x %x\n' % row for row in rows), dict(sorted(coverage.items()))


class AluOracleTests(unittest.TestCase):
    def test_add_sub_wraparound(self):
        self.assertEqual(oracle(28, MASK, 1), (0, 1))
        self.assertEqual(oracle(29, 0, 1), (MASK, 1))
        self.assertEqual(oracle(19, 0x7fffffff, 1), (0x80000000, 1))

    def test_signed_and_unsigned_comparisons(self):
        for op in (20, 31): self.assertEqual(oracle(op, MASK, 0), (1, 1))
        for op in (21, 32): self.assertEqual(oracle(op, MASK, 0), (0, 1))
        self.assertEqual(oracle(31, 0x80000000, 0x7fffffff), (1, 1))

    def test_shift_mask_and_floor_sign_fill(self):
        self.assertEqual(oracle(30, 1, 32), (1, 1))
        self.assertEqual(oracle(25, 1, MASK), (0x80000000, 1))
        self.assertEqual(oracle(35, 0x80000001, 1), (0xc0000000, 1))
        self.assertEqual(oracle(34, 0x80000001, 1), (0x40000000, 1))
        self.assertEqual(oracle(27, MASK, 31), (MASK, 1))

    def test_bitwise_truths(self):
        self.assertEqual(oracle(33, 0x55555555, 0xaaaaaaaa), (MASK, 1))
        self.assertEqual(oracle(36, 0xf0, 0x0f), (0xff, 1))
        self.assertEqual(oracle(37, 0xf0, 0x0f), (0, 1))

    def test_unused_selectors_are_explicitly_unsupported(self):
        for op in set(range(64)) - OPERATIONS.keys():
            self.assertEqual(oracle(op, MASK, MASK), (0, 0))

    def test_register_and_immediate_aliases(self):
        for immediate, register in ((19,28), (20,31), (21,32), (22,33), (23,36),
                                     (24,37), (25,30), (26,34), (27,35)):
            for a in EDGES:
                for b in EDGES:
                    self.assertEqual(oracle(immediate,a,b), oracle(register,a,b))


if __name__ == '__main__':
    unittest.main(verbosity=2)
