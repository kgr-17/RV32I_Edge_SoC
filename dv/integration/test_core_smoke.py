#!/usr/bin/env python3
"""Hand-assembled directed programs and explicit retirement expectations.

This does not decode or execute arbitrary binaries; T011 supplies that oracle.
"""
from collections import Counter
import random
import unittest

MASK = (1 << 32) - 1
NAMES = ('LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU '
         'SB SH SW ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL '
         'SLT SLTU XOR SRL SRA OR AND FENCE ECALL EBREAK').split()
REQUIRED_BINS = ['op:' + name for name in NAMES] + ['fault:%d' % n for n in range(1, 10)]
REQUIRED_BINS += ['branch:taken:' + name for name in NAMES[4:10]]
REQUIRED_BINS += ['branch:false:' + name for name in NAMES[4:10]] + ['load_x0', 'reset_gprs', 'jalr_clear_bit0']
NEGATIVE_FULL_PROGRAM = True
NEGATIVE_DIAGNOSTIC = 'CORE_MISMATCH fault'


def i(opcode, rd, funct3, rs1, imm):
    return (imm % 4096) * 2**20 + rs1 * 2**15 + funct3 * 2**12 + rd * 128 + opcode


def r(rd, funct3, rs1, rs2, funct7=0):
    return funct7 * 2**25 + rs2 * 2**20 + rs1 * 2**15 + funct3 * 2**12 + rd * 128 + 0x33


def s(funct3, rs1, rs2, imm):
    value = imm % 4096
    return (value // 32) * 2**25 + rs2 * 2**20 + rs1 * 2**15 + funct3 * 2**12 + (value % 32) * 128 + 0x23


def b(funct3, rs1, rs2, imm):
    assert imm % 2 == 0 and -4096 <= imm < 4096
    value = imm % 8192
    return ((value >> 12) << 31) + (((value >> 5) & 63) << 25) + (rs2 << 20) + (rs1 << 15) + (funct3 << 12) + (((value >> 1) & 15) << 8) + (((value >> 11) & 1) << 7) + 0x63


def j(rd, imm):
    assert imm % 2 == 0 and -(1 << 20) <= imm < (1 << 20)
    value = imm % (1 << 21)
    return ((value >> 20) << 31) + (((value >> 1) & 1023) << 21) + (((value >> 11) & 1) << 20) + (((value >> 12) & 255) << 12) + rd * 128 + 0x6f


class Program:
    def __init__(self, ident, coverage):
        self.ident, self.coverage = ident, coverage
        self.pc = 0
        self.code = {}
        self.expected = []
        self.initial = bytes.fromhex('007fff8011223344aabbccdd000080ff') + bytes(112)
        self.memory = bytearray(self.initial)
        self.termination = None

    def emit(self, name, word, rd=0, value=0, next_pc=None, memory=None):
        self.coverage['op:' + name] += 1
        self.code[self.pc] = word
        mem = memory or (0, 0, 0, 0, 0, 0)
        self.expected.append((self.pc, word, self.pc + 4 if next_pc is None else next_pc,
                              int(rd != 0), rd, value & MASK if rd else 0, *mem))
        self.pc += 4

    def constant(self, rd, value):
        upper = ((value + 2048) // 4096) % (1 << 20)
        low = value % 4096
        low = low if low < 2048 else low - 4096
        self.emit('LUI', upper * 4096 + rd * 128 + 0x37, rd, upper * 4096)
        self.emit('ADDI', i(0x13, rd, 0, rd, low), rd, value)

    def skip_illegal(self):
        self.code[self.pc] = MASK
        self.pc += 4

    def fault(self, name, word, code, tval=0):
        self.coverage['op:' + name] += 1
        self.code[self.pc] = word
        self.termination = (self.pc, word, code, tval)
        self.coverage['fault:%d' % code] += 1

    def access(self, name, offset, size, write=False, rd=7, value=0):
        lane = offset % 4
        mask = sum(2**n for n in range(lane, lane + size))
        addr = 0x10000 + offset
        if write:
            f3 = {1: 0, 2: 1, 4: 2}[size]
            data = value % (256**size) * (256**lane)
            self.emit(name, s(f3, 1, 2, offset), memory=(1, 1, addr, mask, data, 0))
            self.memory[offset:offset + size] = value.to_bytes(4, 'little')[:size]
        else:
            f3 = {'LB': 0, 'LH': 1, 'LW': 2, 'LBU': 4, 'LHU': 5}[name]
            data = int.from_bytes(self.memory[offset:offset + size], 'little', signed=name in ('LB', 'LH')) & MASK
            raw = int.from_bytes(self.memory[offset // 4 * 4:offset // 4 * 4 + 4], 'little')
            self.emit(name, i(0x03, rd, f3, 1, offset), rd, data, memory=(1, 0, addr, mask, 0, raw))
            if rd == 0:
                self.coverage['load_x0'] += 1

    def rows(self):
        assert self.termination is not None
        pc, insn, code, tval = self.termination
        rows = [(0, pc, insn, code, len(self.expected), self.ident, 0, 0, 0, 0, 0, 0, tval)]
        rows += [(1, addr, word, *([0] * 10)) for addr, word in sorted(self.code.items())]
        rows += [(2, 0x10000 + off, int.from_bytes(self.initial[off:off + 4], 'little'), *([0] * 10)) for off in range(0, 128, 4)]
        rows += [(3, *record) for record in self.expected]
        rows += [(4, *([0] * 12))]
        return rows


def generate(seed):
    rng = random.Random(seed)
    coverage = Counter()
    programs = []
    def new():
        p = Program(len(programs), coverage)
        programs.append(p)
        return p
    p = new()
    for source in range(32):
        p.emit('ADDI', i(0x13, 30, 0, source, 0), 30, 0)
    coverage['reset_gprs'] += 32
    p.emit('ADDI', i(0x13, 0, 0, 0, -1))
    p.emit('ADDI', i(0x13, 31, 0, 0, 0), 31, 0)
    p.constant(1, MASK)
    p.constant(2, 1)
    p.constant(3, 0x80000000)
    p.constant(4, 32)
    p.constant(5, 0x7fffffff)
    cases = [('ADD', 0, 0, 1, 2, 0), ('SUB', 0, 32, 2, 1, 2),
             ('SLL', 1, 0, 2, 4, 1), ('SLT', 2, 0, 3, 2, 1),
             ('SLTU', 3, 0, 3, 2, 0), ('XOR', 4, 0, 1, 3, 0x7fffffff),
             ('SRL', 5, 0, 3, 2, 0x40000000), ('SRA', 5, 32, 3, 2, 0xc0000000),
             ('OR', 6, 0, 3, 2, 0x80000001), ('AND', 7, 0, 5, 3, 0)]
    for name, f3, f7, ra, rb, value in cases:
        p.emit(name, r(8, f3, ra, rb, f7), 8, value)
        p.emit('ADDI', i(0x13, 9, 0, 8, 0), 9, value)
    immediate = [('ADDI', 0, 1, 1, 0), ('SLTI', 2, 3, 0, 1), ('SLTIU', 3, 2, -1, 1),
                 ('XORI', 4, 3, -1, 0x7fffffff), ('ORI', 6, 3, 1, 0x80000001),
                 ('ANDI', 7, 1, 255, 255), ('SLLI', 1, 2, 31, 0x80000000),
                 ('SRLI', 5, 3, 31, 1), ('SRAI', 5, 3, 0x41f, MASK)]
    for name, f3, ra, imm, value in immediate:
        p.emit(name, i(0x13, 8, f3, ra, imm), 8, value)
        p.emit('ADDI', i(0x13, 9, 0, 8, 0), 9, value)
    p.emit('AUIPC', 0x12345017 + 10 * 128, 10, 0x12345000 + p.pc)
    # Ignored future FENCE fields: rd/rs1/fm/pred/succ are all nonzero.
    p.emit('FENCE', 0xffff8f8f)
    p.fault('ECALL', 0x73, 8)

    p = new()
    p.constant(1, MASK)
    p.constant(2, 1)
    branch_pairs = [('BEQ', 0, 1, 1, 1, 2), ('BNE', 1, 1, 2, 1, 1),
                    ('BLT', 4, 1, 2, 2, 1), ('BGE', 5, 2, 1, 1, 2),
                    ('BLTU', 6, 2, 1, 1, 2), ('BGEU', 7, 1, 2, 2, 1)]
    for name, f3, ta, tb, fa, fb in branch_pairs:
        p.emit(name, b(f3, ta, tb, 8), next_pc=p.pc + 8)
        coverage['branch:taken:' + name] += 1
        p.skip_illegal()
        # A false branch must ignore the hypothetical misaligned target.
        p.emit(name, b(f3, fa, fb, 2))
        coverage['branch:false:' + name] += 1
    jal_link = p.pc + 4
    p.emit('JAL', j(5, 8), 5, jal_link, next_pc=p.pc + 8)
    p.skip_illegal()
    target = p.pc + 12
    p.emit('ADDI', i(0x13, 10, 0, 0, target | 1), 10, target | 1)
    jalr_link = p.pc + 4
    p.emit('JALR', i(0x67, 6, 0, 10, 0), 6, jalr_link, next_pc=target)
    p.skip_illegal()
    coverage['jalr_clear_bit0'] += 1
    p.emit('ADDI', i(0x13, 7, 0, 5, 0), 7, jal_link)
    p.emit('ADDI', i(0x13, 7, 0, 6, 0), 7, jalr_link)
    p.fault('EBREAK', 0x100073, 9)

    p = new()
    p.constant(1, 0x10000)
    for offset in range(4):
        p.access('LB', offset, 1)
        p.access('LBU', offset, 1)
    for offset in (0, 2):
        p.access('LH', offset, 2)
        p.access('LHU', offset, 2)
    p.access('LW', 0, 4, rd=0)
    for value in (0x89abcdef, rng.getrandbits(32)):
        p.constant(2, value)
        for offset in range(4):
            p.access('SB', offset, 1, write=True, value=value)
            p.access('LB', offset, 1)
        for offset in (0, 2):
            p.access('SH', offset, 2, write=True, value=value)
            p.access('LH', offset, 2)
        p.access('SW', 4, 4, write=True, value=value)
        p.access('LW', 4, 4)
    p.emit('LW', i(0x03, 11, 2, 0, 0), 11, p.code[0], memory=(1, 0, 0, 15, 0, p.code[0]))
    p.fault('ECALL', 0x73, 8)

    for code, name, word, tval, setup in (
        (1, 'ILLEGAL', MASK, MASK, None),
        (2, 'JAL', j(7, 2), 2, None),
        (2, 'JALR', i(0x67, 7, 0, 1, 0), 2, 3),
        (4, 'LH', i(0x03, 7, 1, 1, 1), 0x10001, 0x10000),
        (6, 'SW', s(2, 1, 0, 2), 0x10002, 0x10000),
        (5, 'LW', i(0x03, 0, 2, 1, 0), 0x20000, 0x20000),
        (7, 'SW', s(2, 0, 0, 0), 0, None)):
        p = new()
        if setup is not None:
            p.constant(1, setup)
        p.fault(name, word, code, tval)
    p = new()
    p.emit('JAL', j(0, 0x10000), next_pc=0x10000)
    p.termination = (0x10000, 0, 3, 0x10000)
    coverage['fault:3'] += 1
    rows = [row for program in programs for row in program.rows()]
    assert all(len(row) == 13 for row in rows)
    coverage['scenarios'] = len(programs)
    coverage['expected_retirements'] = sum(len(program.expected) for program in programs)
    assert all(coverage[name] > 0 for name in REQUIRED_BINS), coverage
    return ''.join(' '.join('%08x' % (value & MASK) for value in row) + '\n' for row in rows), dict(sorted(coverage.items()))


class CoreProgramTests(unittest.TestCase):
    def test_known_machine_encodings(self):
        self.assertEqual(i(0x13, 1, 0, 0, -1), 0xfff00093)
        self.assertEqual(r(3, 0, 1, 2), 0x002081b3)
        self.assertEqual(s(2, 1, 2, 0), 0x0020a023)
        self.assertEqual(b(0, 1, 2, 8), 0x00208463)
        self.assertEqual(j(1, 8), 0x008000ef)

    def test_replay_and_nonempty_full_family_coverage(self):
        first, coverage = generate(1)
        self.assertEqual(first, generate(1)[0])
        self.assertNotEqual(first, generate(20261026)[0])
        self.assertTrue(all(coverage[key] for key in REQUIRED_BINS))
        self.assertEqual(coverage['scenarios'], 11)
        self.assertGreater(coverage['expected_retirements'], 100)

    def test_first_row_corruption_targets_checked_fault_value(self):
        first = generate(1)[0].splitlines()[0].split()
        self.assertEqual(len(first), 13)
        self.assertEqual(int(first[0], 16), 0)
        self.assertEqual(int(first[-1], 16), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
