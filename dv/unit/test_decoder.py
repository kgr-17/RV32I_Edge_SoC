#!/usr/bin/env python3
"""Independent mask-table oracle and replayable encoder-driven decoder vectors.

No RTL import/parsing: operation numbers and packed wire layout are the public
unit interface. Expected legal immediates come from original encoder inputs.
"""
from collections import Counter, namedtuple
import random
from pathlib import Path
import sys
import unittest

MASK32 = (1 << 32) - 1
Rule = namedtuple('Rule', 'name op mask value fmt read1 read2 write')

# Flat mask/value specification, deliberately different from the RTL case tree.
# name, mask, encoding, immediate format, rs1-use, rs2-use, destination
ENCODINGS = [
    ('LUI', 0x7f, 0x37, 'U', 0, 0, 1),
    ('AUIPC', 0x7f, 0x17, 'U', 0, 0, 1),
    ('JAL', 0x7f, 0x6f, 'J', 0, 0, 1),
    ('JALR', 0x707f, 0x67, 'I', 1, 0, 1),
    ('BEQ', 0x707f, 0x0063, 'B', 1, 1, 0),
    ('BNE', 0x707f, 0x1063, 'B', 1, 1, 0),
    ('BLT', 0x707f, 0x4063, 'B', 1, 1, 0),
    ('BGE', 0x707f, 0x5063, 'B', 1, 1, 0),
    ('BLTU', 0x707f, 0x6063, 'B', 1, 1, 0),
    ('BGEU', 0x707f, 0x7063, 'B', 1, 1, 0),
    ('LB', 0x707f, 0x0003, 'I', 1, 0, 1),
    ('LH', 0x707f, 0x1003, 'I', 1, 0, 1),
    ('LW', 0x707f, 0x2003, 'I', 1, 0, 1),
    ('LBU', 0x707f, 0x4003, 'I', 1, 0, 1),
    ('LHU', 0x707f, 0x5003, 'I', 1, 0, 1),
    ('SB', 0x707f, 0x0023, 'S', 1, 1, 0),
    ('SH', 0x707f, 0x1023, 'S', 1, 1, 0),
    ('SW', 0x707f, 0x2023, 'S', 1, 1, 0),
    ('ADDI', 0x707f, 0x0013, 'I', 1, 0, 1),
    ('SLTI', 0x707f, 0x2013, 'I', 1, 0, 1),
    ('SLTIU', 0x707f, 0x3013, 'I', 1, 0, 1),
    ('XORI', 0x707f, 0x4013, 'I', 1, 0, 1),
    ('ORI', 0x707f, 0x6013, 'I', 1, 0, 1),
    ('ANDI', 0x707f, 0x7013, 'I', 1, 0, 1),
    ('SLLI', 0xfe00707f, 0x00001013, 'H', 1, 0, 1),
    ('SRLI', 0xfe00707f, 0x00005013, 'H', 1, 0, 1),
    ('SRAI', 0xfe00707f, 0x40005013, 'H', 1, 0, 1),
    ('ADD', 0xfe00707f, 0x00000033, 'R', 1, 1, 1),
    ('SUB', 0xfe00707f, 0x40000033, 'R', 1, 1, 1),
    ('SLL', 0xfe00707f, 0x00001033, 'R', 1, 1, 1),
    ('SLT', 0xfe00707f, 0x00002033, 'R', 1, 1, 1),
    ('SLTU', 0xfe00707f, 0x00003033, 'R', 1, 1, 1),
    ('XOR', 0xfe00707f, 0x00004033, 'R', 1, 1, 1),
    ('SRL', 0xfe00707f, 0x00005033, 'R', 1, 1, 1),
    ('SRA', 0xfe00707f, 0x40005033, 'R', 1, 1, 1),
    ('OR', 0xfe00707f, 0x00006033, 'R', 1, 1, 1),
    ('AND', 0xfe00707f, 0x00007033, 'R', 1, 1, 1),
    ('FENCE', 0x707f, 0x000f, 'N', 0, 0, 0),
    ('ECALL', MASK32, 0x00000073, 'N', 0, 0, 0),
    ('EBREAK', MASK32, 0x00100073, 'N', 0, 0, 0),
]
RULES = [Rule(name, index, mask, value, fmt, r1, r2, wr)
         for index, (name, mask, value, fmt, r1, r2, wr) in enumerate(ENCODINGS, 1)]
BY_NAME = {rule.name: rule for rule in RULES}
# Immediate bit -> instruction bit. Used for arbitrary-word classification;
# legal-vector expectations below use original input values instead.
POSITIONS = {
    'I': list(range(20, 32)),
    'S': list(range(7, 12)) + list(range(25, 32)),
    'B': [None] + list(range(8, 12)) + list(range(25, 31)) + [7, 31],
    'J': [None] + list(range(21, 31)) + [20] + list(range(12, 20)) + [31],
    'U': [None] * 12 + list(range(12, 32)),
    'H': list(range(20, 25)),
    'R': [], 'N': []
}


def pack(rule=None, imm=0, rs1=0, rs2=0, rd=0):
    if rule is None:
        return 1  # illegal=1; all operation/effect/operand metadata zero
    wr = bool(rule.write and rd)
    return ((rule.op << 51) | ((imm & MASK32) << 19) |
            ((rs1 if rule.read1 else 0) << 14) |
            ((rs2 if rule.read2 else 0) << 9) | ((rd if wr else 0) << 4) |
            (rule.read1 << 3) | (rule.read2 << 2) | (int(wr) << 1))


def classify(insn):
    matches = [rule for rule in RULES if insn & rule.mask == rule.value]
    if len(matches) > 1:
        raise AssertionError('Overlapping independent rules')
    return matches[0] if matches else None


def oracle(insn):
    rule = classify(insn)
    if rule is None:
        return pack()
    positions = POSITIONS[rule.fmt]
    imm = sum(((insn >> bit) & 1) << index for index, bit in enumerate(positions) if bit is not None)
    if rule.fmt in ('I', 'S', 'B', 'J') and imm & (1 << (len(positions) - 1)):
        imm -= 1 << len(positions)
    return pack(rule, imm, (insn >> 15) & 31, (insn >> 20) & 31, (insn >> 7) & 31)


def encode(rule, imm=0, rs1=0, rs2=0, rd=0):
    """Separate instruction builder; caller retains the expected XLEN value."""
    word = rule.value | ((rs1 if rule.read1 else 0) << 15) | ((rs2 if rule.read2 else 0) << 20)
    word |= (rd if rule.write else 0) << 7
    for index, bit in enumerate(POSITIONS[rule.fmt]):
        if bit is not None:
            word |= ((imm >> index) & 1) << bit
    return word


def generate(seed):
    rng = random.Random(seed)
    rows, coverage = [], Counter()

    def add(word, expected=None, group='arbitrary'):
        result = oracle(word)
        if expected is not None and result != expected:
            raise AssertionError('Encoder/oracle disagreement for %08x' % word)
        rows.append((word, result if expected is None else expected))
        rule = classify(word)
        coverage[rule.name if rule else 'ILLEGAL'] += 1
        coverage['group:' + group] += 1

    def legal(rule, imm, rs1, rs2, rd, group):
        add(encode(rule, imm, rs1, rs2, rd), pack(rule, imm, rs1, rs2, rd), group)

    for rule in RULES:
        # Full I/S and B immediate spaces, every shift amount, walking U/J bits.
        if rule.fmt in ('I', 'S'):
            immediates = range(-2048, 2048)
        elif rule.fmt == 'B':
            immediates = range(-4096, 4096, 2)
        elif rule.fmt == 'H':
            immediates = range(32)
        elif rule.fmt in ('U', 'J'):
            low, high = (12, 32) if rule.fmt == 'U' else (1, 21)
            immediates = [0] + [1 << bit for bit in range(low, high)]
            immediates += [MASK32 & ~((1 << low) - 1)] if rule.fmt == 'U' else [-1048576, -2, 1048574]
            if rule.fmt == 'J':
                immediates = [value - (1 << 21) if value >= 1 << 20 else value for value in immediates]
        else:
            immediates = [0]
        for imm in immediates:
            legal(rule, imm, rng.randrange(32), rng.randrange(32), rng.randrange(32), 'immediate:' + rule.fmt)
        # Each register index, x0 HINT/destination and both source-zero forms.
        for reg in range(32):
            for rs1, rs2, rd in ((reg, 31 - reg, reg), (0, reg, 0), (reg, 0, 31)):
                legal(rule, 0, rs1, rs2, rd, 'registers')
        for _ in range(64):
            fmt = rule.fmt
            imm = {'I': lambda: rng.randrange(-2048, 2048), 'S': lambda: rng.randrange(-2048, 2048),
                   'B': lambda: rng.randrange(-2048, 2048) * 2,
                   'J': lambda: rng.randrange(-524288, 524288) * 2,
                   'U': lambda: rng.getrandbits(20) << 12, 'H': lambda: rng.randrange(32)}.get(fmt, lambda: 0)()
            legal(rule, imm, rng.randrange(32), rng.randrange(32), rng.randrange(32), 'random-legal')

    # Exhaust all funct7/funct3 pairs for OP/OP-IMM, with operand edge shapes.
    for major in (0x13, 0x33):
        for f7 in range(128):
            for f3 in range(8):
                for reg in (0, 1, 16, 31):
                    add((f7 << 25) | (reg << 20) | ((31-reg) << 15) | (f3 << 12) | (reg << 7) | major,
                        group='funct7-funct3')
    for f7 in range(128):
        for amount in range(32):
            for f3 in (1, 5):
                add((f7 << 25) | (amount << 20) | (31 << 15) | (f3 << 12) | (31 << 7) | 0x13,
                    group='shift-reserved')
    for major in range(128):
        for f3 in range(8):
            for upper in (0, 0xffff8000):
                add(upper | (f3 << 12) | 0xf80 | major, group='major-funct3')
    for immediate in range(4096):
        add((immediate << 20) | 0x73, group='system-immediate')
        # All fm/pred/succ bits, with rd/rs1 nonzero and ignored.
        add((immediate << 20) | (31 << 15) | (31 << 7) | 0xf, group='fence-ignored')
    for f3 in range(8):
        for rs1 in range(32):
            for rd in range(32):
                for immediate in (0, 1):
                    add((immediate << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x73,
                        group='system-reserved')
    for _ in range(8192):
        add(rng.getrandbits(32), group='random-word')
    for word in (0, MASK32, 0x02000033, 0x02005033, 0x0000100f, 0x00001073,
                 0x30200073, 0x10500073, 0x02001013, 0x40001013, 0x00003003,
                 0x00003023, 0x00002063, 0x00001067, 0x0000002f, 0x00000053):
        add(word, pack(), 'explicit-illegal')
    required = {rule.name for rule in RULES} | {'ILLEGAL'}
    if not all(coverage[name] > 0 for name in required):
        raise AssertionError('Unhit operation coverage')
    rng.shuffle(rows)  # Exercise defaults after unrelated legal/illegal operations.
    return ''.join('%08x %015x\n' % row for row in rows), dict(sorted(coverage.items()))


class OracleTests(unittest.TestCase):
    def test_fixed_instruction_words(self):
        examples = [(0x00000013, 'ADDI', 0), (0xfff10093, 'ADDI', -1),
                    (0xfe112e23, 'SW', -4), (0xfe000ee3, 'BEQ', -4),
                    (0xffdff06f, 'JAL', -4), (0x800000b7, 'LUI', 0x80000000),
                    (0x41f15093, 'SRAI', 31), (0x00000073, 'ECALL', 0),
                    (0x00100073, 'EBREAK', 0)]
        for word, name, imm in examples:
            with self.subTest(name=name):
                self.assertEqual(classify(word).name, name)
                self.assertEqual((oracle(word) >> 19) & MASK32, imm & MASK32)

    def test_rules_disjoint(self):
        for index, left in enumerate(RULES):
            for right in RULES[index+1:]:
                self.assertNotEqual((left.value ^ right.value) & left.mask & right.mask, 0)

    def test_all_approved_mnemonics(self):
        import json
        root = Path(__file__).resolve().parents[2]
        contract = json.loads((root / 'docs/ARCH_CONTRACT.json').read_text(encoding='utf-8'))
        # Exact list is read only to check inventory, never to compute outcomes.
        self.assertEqual(set(contract['isa']['instructions']), set(BY_NAME))
        self.assertEqual(len(RULES), 40)

    def test_illegal_has_no_effects(self):
        for word in (0, MASK32, 0x02000033, 0x0000100f, 0x00001073, 0x00200073):
            self.assertEqual(oracle(word), 1)

    def test_x0_load_is_still_load(self):
        word = 0x00002003
        self.assertEqual(classify(word).name, 'LW')
        self.assertEqual(oracle(word) & 15, 8)  # uses rs1, no GPR write, legal

    def test_fence_ignored_fields(self):
        self.assertEqual(oracle(0xffff8f8f), BY_NAME['FENCE'].op << 51)


if __name__ == '__main__':
    unittest.main(verbosity=2)
