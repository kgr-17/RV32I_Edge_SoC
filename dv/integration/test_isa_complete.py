#!/usr/bin/env python3
"""Directed v0.2 ISA/EEI cases with hand expectations, independent of the ISS."""
from collections import Counter
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dv.integration import test_backpressure as baseline
from dv.integration.test_core_smoke import Program, MASK, i, r, s, b, j

REQUIREMENTS = ['fence_drain', 'fence_ignored_fields', 'hints', 'alu_edges',
                'illegal_m', 'illegal_csr', 'illegal_system', 'illegal_fence_i',
                'illegal_fields', 'illegal_extensions', 'alignment_before_map',
                'load_x0_fault', 'branch_alignment', 'backward_branch',
                'jalr_wrap', 'jalr_negative', 'jal_wrap', 'auipc_wrap',
                'address_wrap', 'memory_boundaries', 'precise_ecall', 'precise_ebreak']
REQUIREMENTS += ['bus_error_response']
ERROR_WORDS = {46: [0], 47: [0x10000], 48: [0x10000]}
REQUIRED_BINS = baseline.REQUIRED_BINS + ['eei:' + name for name in REQUIREMENTS]
NEGATIVE_FULL_PROGRAM = True
NEGATIVE_DIAGNOSTIC = 'ISA_COMPLETE_MISMATCH fault'


def signed(value):
    return value if value < 2**31 else value - 2**32


def directed(seed):
    coverage, programs, plan = Counter(), [], []

    def new(requirement, detail):
        p = Program(42 + len(programs), coverage)
        programs.append(p)
        plan.append({'scenario': p.ident, 'requirement': requirement, 'detail': detail})
        coverage['eei:' + requirement] += 1
        return p

    # IDs42..45 are used by the runtime FENCE/effect/nonvacuity monitor.
    for word in (0x0000000f, 0x0ff0000f, 0x8330000f, 0xffff8f8f):
        p = new('fence_drain', 'priming LW -> older SW -> FENCE %08x -> younger LW/SW' % word)
        coverage['eei:fence_ignored_fields'] += 1
        p.constant(1, 0x10000)
        p.constant(2, (0x89abcdef ^ seed) & MASK)
        p.constant(31, 0x12345678)
        p.access('LW', 0, 4, rd=4)  # fill answered-fetch queue before SW/FENCE
        p.access('SW', 0, 4, write=True, value=(0x89abcdef ^ seed) & MASK)
        p.emit('FENCE', word)
        p.access('LW', 0, 4, rd=3)
        p.emit('ADDI', i(0x13, 5, 0, 31, 0), 5, 0x12345678)
        p.access('SW', 4, 4, write=True, value=(0x89abcdef ^ seed) & MASK)
        p.fault('ECALL', 0x73, 8)

    p = new('bus_error_response', 'instruction error at valid ROM address0, insn reported0')
    p.code[0] = 0x73
    p.termination = (0, 0, 3, 0); coverage['fault:3'] += 1
    p = new('bus_error_response', 'load x0 receives error at valid RAM address')
    p.constant(1, 0x10000); p.fault('LW', i(0x03, 0, 2, 1, 0), 5, 0x10000)
    p = new('bus_error_response', 'store error at valid RAM address has no byte effects')
    p.constant(1, 0x10000); p.constant(2, 0x76543210)
    p.fault('SW', s(2, 1, 2, 0), 7, 0x10000)

    p = new('hints', 'x0 destinations preserve normal no-write behavior')
    p.constant(1, MASK)
    p.constant(2, 0x80000000)
    p.emit('LUI', 0xfffff037)
    p.emit('AUIPC', 0xfffff017)
    for name, f3, f7 in [('ADD', 0, 0), ('SUB', 0, 32), ('SLL', 1, 0), ('SLT', 2, 0),
                         ('SLTU', 3, 0), ('XOR', 4, 0), ('SRL', 5, 0), ('SRA', 5, 32), ('OR', 6, 0), ('AND', 7, 0)]:
        p.emit(name, r(0, f3, 1, 2, f7))
    for name, f3, imm in [('ADDI', 0, 0), ('SLTI', 2, -1), ('SLTIU', 3, -1), ('XORI', 4, -1),
                          ('ORI', 6, 1), ('ANDI', 7, 255), ('SLLI', 1, 31), ('SRLI', 5, 31), ('SRAI', 5, 0x41f)]:
        p.emit(name, i(0x13, 0, f3, 1, imm))
    p.emit('ADDI', 0x00000013)  # canonical NOP
    p.emit('ADDI', i(0x13, 3, 0, 1, 0), 3, MASK)
    p.emit('ADDI', i(0x13, 4, 0, 2, 0), 4, 0x80000000)
    p.fault('ECALL', 0x73, 8)

    p = new('alu_edges', 'six-value cross, all register ALU, immediate extremes and shifts')
    values = (0, 1, MASK, 0x80000000, 0x7fffffff, 32)
    for a in values:
        for c in values:
            p.constant(3, a); p.constant(4, c)
            for name, f3, f7, result in (
                ('ADD', 0, 0, a+c), ('SUB', 0, 32, a-c), ('SLL', 1, 0, a << (c & 31)),
                ('SLT', 2, 0, int(signed(a)<signed(c))), ('SLTU', 3, 0, int(a<c)),
                ('XOR', 4, 0, a^c), ('SRL', 5, 0, a >> (c & 31)),
                ('SRA', 5, 32, signed(a) >> (c & 31)), ('OR', 6, 0, a|c), ('AND', 7, 0, a&c)):
                p.emit(name, r(8, f3, 3, 4, f7), 8, result)
        for imm in (-2048, -1, 0, 1, 2047):
            for name, f3, result in [('ADDI', 0, a+imm), ('SLTI', 2, int(signed(a)<imm)),
                                     ('SLTIU', 3, int(a<imm % 2**32)), ('XORI', 4, a^imm),
                                     ('ORI', 6, a|imm), ('ANDI', 7, a&imm)]:
                p.emit(name, i(0x13, 8, f3, 3, imm), 8, result)
        for amount in (0, 1, 31):
            for name, imm, result in [('SLLI', amount, a << amount), ('SRLI', amount, a >> amount),
                                       ('SRAI', 0x400+amount, signed(a) >> amount)]:
                p.emit(name, i(0x13, 8, 1 if name=='SLLI' else 5, 3, imm), 8, result)
    p.fault('ECALL', 0x73, 8)

    illegal = []
    illegal += [('illegal_m', r(5, f3, 1, 2, 1)) for f3 in range(8)]
    illegal += [('illegal_csr', i(0x73, 5, f3, 1, 0x300)) for f3 in (1, 2, 3, 5, 6, 7)]
    illegal += [('illegal_system', word) for word in (0x30200073, 0x10500073, 0x12000073, 0x000000f3, 0x00008073, 0x001000f3)]
    illegal += [('illegal_fence_i', 0x0000100f)]
    illegal += [('illegal_extensions', word) for word in (0x00000000, 0x00000001, 0x00010001, 0xffffffff,
                                                         0x0020a2af, 0x0000a287, 0x0020a027, 0x002082d3)]
    illegal += [('illegal_fields', i(0x67, 5, f3, 1, 0)) for f3 in range(1, 8)]
    illegal += [('illegal_fields', i(0x03, 5, f3, 1, 0)) for f3 in (3, 6, 7)]
    illegal += [('illegal_fields', s(f3, 1, 2, 0)) for f3 in range(3, 8)]
    illegal += [('illegal_fields', b(f3, 1, 2, 4)) for f3 in (2, 3)]
    illegal += [('illegal_fields', i(0x13, 5, f3, 1, imm)) for f3, imm in ((1, 0x400), (1, 0x020), (5, 0x020), (5, 0x420))]
    illegal += [('illegal_fields', r(5, f3, 1, 2, 32)) for f3 in (1, 2, 3, 4, 6, 7)]
    illegal += [('illegal_fields', i(0x0f, 0, f3, 0, 0)) for f3 in range(2, 8)]
    for requirement, word in illegal:
        p = new(requirement, 'illegal encoding %08x' % word)
        p.constant(6, 0x76543210)
        p.fault('ILLEGAL', word, 1, word)
        p.code[p.pc+4] = s(2, 1, 2, 0)  # younger store must never issue

    for base in (0x10000, 0x20000):
        for name, f3, offset in [('LH', 1, 1), ('LHU', 5, 1), ('LW', 2, 1), ('LW', 2, 2), ('LW', 2, 3)]:
            p = new('alignment_before_map', name+' base=%x offset=%d' % (base, offset))
            p.constant(1, base); p.fault(name, i(0x03, 0, f3, 1, offset), 4, base+offset)
        for name, f3, offset in [('SH', 1, 1), ('SW', 2, 1), ('SW', 2, 2), ('SW', 2, 3)]:
            p = new('alignment_before_map', name+' base=%x offset=%d' % (base, offset))
            p.constant(1, base); p.fault(name, s(f3, 1, 0, offset), 6, base+offset)

    for name, f3 in [('LB', 0), ('LH', 1), ('LW', 2), ('LBU', 4), ('LHU', 5)]:
        p = new('load_x0_fault', name+' x0 still requests inaccessible memory')
        p.constant(1, 0x20000); p.fault(name, i(0x03, 0, f3, 1, 0), 5, 0x20000)

    predicates = [('BEQ', 0, 7, 7, 7, 8), ('BNE', 1, 7, 8, 7, 7), ('BLT', 4, MASK, 1, 1, MASK),
                  ('BGE', 5, 1, MASK, MASK, 1), ('BLTU', 6, 1, MASK, MASK, 1), ('BGEU', 7, MASK, 1, 1, MASK)]
    for name, f3, ta, tc, fa, fc in predicates:
        for taken, a, c in ((True, ta, tc), (False, fa, fc)):
            p = new('branch_alignment', name+' misaligned hypothetical target, taken='+str(taken))
            p.constant(1, a); p.constant(2, c)
            word = b(f3, 1, 2, 2)
            if taken: p.fault(name, word, 2, p.pc+2)
            else: p.emit(name, word); p.fault('ECALL', 0x73, 8)

    p = new('backward_branch', 'bounded decrement loop takes negative displacement twice')
    p.constant(1, 3)
    for value in (2, 1, 0):
        p.pc = 8
        p.emit('ADDI', i(0x13, 1, 0, 1, -1), 1, value)
        p.emit('BNE', b(1, 1, 0, -4), next_pc=8 if value else 16)
    p.fault('ECALL', 0x73, 8)

    for requirement, base, imm in [('jalr_wrap', MASK, 21), ('jalr_negative', 22, -1)]:
        p = new(requirement, 'JALR arithmetic then bit0 clear targets20')
        p.constant(1, base)
        p.emit('JALR', i(0x67, 5, 0, 1, imm), 5, 12, next_pc=20)
        p.skip_illegal(); p.skip_illegal()
        p.fault('ECALL', 0x73, 8)
    p = new('jal_wrap', 'JAL negative displacement wraps to inaccessible fffffffc')
    p.emit('JAL', j(5, -4), 5, 4, next_pc=0xfffffffc)
    p.termination = (0xfffffffc, 0, 3, 0xfffffffc); coverage['fault:3'] += 1
    p = new('auipc_wrap', 'AUIPC at last ROM word wraps result32')
    p.emit('JAL', j(0, 0xfffc), next_pc=0xfffc); p.pc = 0xfffc
    p.emit('AUIPC', 0xfffff117, 2, 0xeffc, next_pc=0x10000)
    p.termination = (0x10000, 0, 3, 0x10000); coverage['fault:3'] += 1

    p = new('address_wrap', 'LW fffffffc+4 reads ROM address0')
    p.constant(1, 0xfffffffc)
    p.emit('LW', i(0x03, 3, 2, 1, 4), 3, p.code[0], memory=(1, 0, 0, 15, 0, p.code[0]))
    p.fault('ECALL', 0x73, 8)
    p = new('address_wrap', 'wrapped SW address0 faults ROM write without effect')
    p.constant(1, 0xfffffffc); p.fault('SW', s(2, 1, 0, 4), 7, 0)
    p = new('memory_boundaries', 'ROM last word load and last RAM word byte/half/word effects')
    p.code[0xfffc] = 0x89abcdef
    p.constant(1, 0xfffc)
    p.emit('LW', i(0x03, 3, 2, 1, 0), 3, 0x89abcdef, memory=(1, 0, 0xfffc, 15, 0, 0x89abcdef))
    p.constant(1, 0x1fffc); p.constant(2, 0x89abcdef)
    p.emit('SW', s(2, 1, 2, 0), memory=(1, 1, 0x1fffc, 15, 0x89abcdef, 0))
    for name, f3, offset, mask, value in [('LW', 2, 0, 15, 0x89abcdef), ('LB', 0, 3, 8, 0xffffff89),
                                        ('LBU', 4, 3, 8, 0x89), ('LH', 1, 2, 12, 0xffff89ab), ('LHU', 5, 2, 12, 0x89ab)]:
        p.emit(name, i(0x03, 3, f3, 1, offset), 3, value, memory=(1, 0, 0x1fffc+offset, mask, 0, 0x89abcdef))
    p.fault('ECALL', 0x73, 8)
    for requirement, word, code in [('precise_ecall', 0x73, 8), ('precise_ebreak', 0x100073, 9)]:
        p = new(requirement, 'older delayed SW commits; fault and younger SW never retire/issue')
        p.constant(1, 0x10000); p.constant(2, 0x87654321)
        p.access('SW', 0, 4, write=True, value=0x87654321)
        p.fault('ECALL' if code==8 else 'EBREAK', word, code)
        p.code[p.pc+4] = s(2, 1, 2, 4)
    return programs, coverage, plan


def generate(seed):
    prefix, old = baseline.generate(seed)
    programs, coverage, _ = directed(seed)
    rows = [row for p in programs for row in p.rows()]
    coverage.update(old)
    coverage['scenarios'] = old['scenarios'] + len(programs)
    coverage['expected_retirements'] = old['expected_retirements'] + sum(len(p.expected) for p in programs)
    assert all(coverage.get(name, 0) > 0 for name in REQUIRED_BINS)
    return prefix + ''.join(' '.join('%08x' % (v & MASK) for v in row)+'\n' for row in rows), dict(sorted(coverage.items()))


class IsaCompletePrograms(unittest.TestCase):
    def test_legacy_prefix_and_all_runtime_collision_cases_retained(self):
        self.assertTrue(generate(1)[0].startswith(baseline.generate(1)[0]))

    def test_replay_and_seed_dependent_fence_data(self):
        self.assertEqual(generate(7), generate(7))
        self.assertNotEqual(generate(7)[0], generate(101)[0])

    def test_complete_unique_case_and_semantic_inventory(self):
        from dv.reference.retire import stimulus_images
        text, coverage = generate(1)
        cases = stimulus_images(text)
        self.assertEqual([case['id'] for case in cases], list(range(len(cases))))
        self.assertTrue(all(coverage[key]>0 for key in REQUIRED_BINS))
        self.assertEqual(coverage['scenarios'], len(cases))

    def test_literal_fence_encodings_have_funct3_zero(self):
        programs, _, plan = directed(1)
        self.assertEqual([row['scenario'] for row in plan[:4]], [42, 43, 44, 45])
        self.assertEqual([p.code[32] for p in programs[:4]], [0xf, 0xff0000f, 0x8330000f, 0xffff8f8f])

    def test_hand_expectations_match_independent_iss_for_every_case(self):
        from dv.reference.retire import expected_trace, stimulus_images
        for seed in (1, 7, 101, 20261102):
            text, _ = generate(seed)
            actual, _, cases = expected_trace(stimulus_images(text), ERROR_WORDS)
            expected, ident, order = [], None, 0
            for line in text.splitlines():
                row = [int(v, 16) for v in line.split()]
                if row[0]==0:
                    ident, order = row[5], 0
                    fault = ('F', ident, row[1], row[2], row[3], row[12])
                elif row[0]==3:
                    expected.append(('R', ident, order, *row[1:])); order+=1
                elif row[0]==4: expected.append(fault)
            self.assertEqual([event for event in actual if event[0] in ('R', 'F')], expected)
            self.assertEqual(len(cases), len(stimulus_images(text)))

    def test_case_size_fits_existing_real_scoreboard_bound(self):
        programs, _, _ = directed(1)
        self.assertTrue(all(len(p.expected)<2048 and max(p.code)<65536 for p in programs))

    def test_fault_injection_is_explicit_and_scenario_bound(self):
        from dv.reference.retire import expected_trace, stimulus_images
        cases = stimulus_images(generate(1)[0])
        injected, _, _ = expected_trace(cases, ERROR_WORDS)
        plain, _, _ = expected_trace(cases)
        self.assertNotEqual(injected, plain)
        for ident, code in ((46, 3), (47, 5), (48, 7)):
            self.assertEqual(next(e for e in injected if e[:2]==('F', ident))[4], code)
        with self.assertRaises(ValueError):
            expected_trace(cases, {99999: [0]})
        with self.assertRaises(ValueError):
            expected_trace(cases, {46: [1]})

    def test_configured_bus_errors_match_explicit_stimulus(self):
        import json
        root = Path(__file__).resolve().parents[2]
        spec = json.loads((root/'config/rtl_checks.json').read_text())['unit_sims']['isa_complete']
        self.assertEqual({int(key): value for key, value in spec['error_words_by_scenario'].items()}, ERROR_WORDS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
