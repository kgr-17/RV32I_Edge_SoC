#!/usr/bin/env python3
"""Replayable constrained programs; the independent ISS supplies expectations."""
from collections import Counter
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dv.integration import test_backpressure as baseline
from dv.integration.test_core_smoke import NAMES, MASK, i, r, s, b, j
from dv.reference.rv32_iss import RV32ISS

KINDS = ('reg', 'imm', 'memory', 'branch', 'jal', 'jalr', 'loop', 'fence', 'raw', 'upper')
REQUIRED_BINS = baseline.REQUIRED_BINS + ['random_programs']
REQUIRED_BINS += ['random_op:'+name for name in NAMES] + ['template:'+kind for kind in KINDS]
NEGATIVE_FULL_PROGRAM = True
NEGATIVE_DIAGNOSTIC = 'RANDOM_MISMATCH fault'
REGISTER_OPS = [('ADD',0,0),('SUB',0,32),('SLL',1,0),('SLT',2,0),('SLTU',3,0),
                ('XOR',4,0),('SRL',5,0),('SRA',5,32),('OR',6,0),('AND',7,0)]
IMMEDIATES = [('ADDI',0,0),('SLTI',2,0),('SLTIU',3,0),('XORI',4,0),('ORI',6,0),
              ('ANDI',7,0),('SLLI',1,0),('SRLI',5,0),('SRAI',5,0x400)]


class ImageBuilder:
    def __init__(self):
        self.pc, self.code = 0, {}

    def emit(self, word):
        if not 0<=self.pc<65536 or self.pc in self.code:
            raise ValueError('invalid/duplicate generated PC')
        self.code[self.pc] = word & MASK
        self.pc += 4

    def constant(self, rd, value):
        low = value%4096
        low = low if low<2048 else low-4096
        self.emit((((value+2048)//4096)%(1<<20))*4096+rd*128+0x37)
        self.emit(i(0x13,rd,0,rd,low))


def random_image(seed, number):
    rng = random.Random((seed<<8) ^ number ^ 0x190019)
    p = ImageBuilder(); templates = Counter()
    dest = lambda: rng.choice([0]+list(range(2,29)))
    src = lambda: rng.randrange(29)
    p.emit(0x000100b7)  # x1 is an invariant RAM base; x30/31 reserved for control.
    for rd in range(2,29):
        p.constant(rd, rng.getrandbits(32))
    # Ensure every ALU operation executes on independently randomized operands.
    for _, f3, f7 in REGISTER_OPS:
        p.emit(r(dest(),f3,src(),src(),f7))
    for _, f3, upper in IMMEDIATES:
        imm = rng.randrange(32)+upper if f3 in (1,5) else rng.randrange(-2048,2048)
        p.emit(i(0x13,dest(),f3,src(),imm))
    p.emit(rng.getrandbits(20)*4096+dest()*128+0x17)  # AUIPC
    # Force all load/store widths and lanes before the shuffled template bag.
    for f3, size in ((0,1),(1,2),(2,4)):
        offset = rng.randrange(128//size)*size
        p.emit(s(f3,1,src(),offset))
    for f3, size in ((0,1),(1,2),(2,4),(4,1),(5,2)):
        p.emit(i(0x03,dest(),f3,1,rng.randrange(128//size)*size))
    for f3 in (0,1,4,5,6,7):
        p.emit(b(f3,src(),src(),8)); p.emit(i(0x13,dest(),0,src(),rng.randrange(-2048,2048)))
    bag = list(KINDS)*6
    rng.shuffle(bag)
    for kind in bag:
        templates['template:'+kind] += 1
        if kind=='reg':
            _, f3, f7 = rng.choice(REGISTER_OPS)
            p.emit(r(dest(),f3,src(),src(),f7))
        elif kind=='imm':
            _, f3, upper = rng.choice(IMMEDIATES)
            imm = rng.randrange(32)+upper if f3 in (1,5) else rng.randrange(-2048,2048)
            p.emit(i(0x13,dest(),f3,src(),imm))
        elif kind=='memory':
            sf3, size = rng.choice([(0,1),(1,2),(2,4)])
            offset = rng.randrange(128//size)*size
            p.emit(s(sf3,1,src(),offset))
            lf3 = rng.choice({1:[0,4],2:[1,5],4:[2]}[size])
            rd = rng.randrange(2,29)
            p.emit(i(0x03,rd,lf3,1,offset))
            p.emit(r(dest(),0,rd,rd))  # immediate two-source load dependency
        elif kind=='branch':
            p.emit(b(rng.choice([0,1,4,5,6,7]),src(),src(),8))
            p.emit(s(2,1,src(),rng.randrange(32)*4))  # legal fallthrough effect
        elif kind=='jal':
            rd = dest(); p.emit(j(rd,8))
            p.emit(0xffffffff if rng.randrange(2) else s(2,1,src(),rng.randrange(32)*4))
            p.emit(i(0x13,dest(),0,rd,0))  # link readback
        elif kind=='jalr':
            target = p.pc+16
            p.constant(30,target|1)
            rd = dest(); p.emit(i(0x67,rd,0,30,0)); p.emit(0xffffffff)
            assert p.pc==target
            p.emit(i(0x13,dest(),0,rd,0))
        elif kind=='loop':
            p.constant(31,rng.randrange(1,5))
            p.emit(i(0x13,31,0,31,-1)); p.emit(b(1,31,0,-4))
        elif kind=='fence':
            p.emit((rng.getrandbits(32)&~0x707f)|0xf)
        elif kind=='raw':
            rd = rng.randrange(2,29)
            p.emit(r(rd,0,src(),src()))
            p.emit(r(dest(),4,rd,rd))
            p.emit(s(2,1,rd,rng.randrange(32)*4))
        elif kind=='upper':
            p.emit(rng.getrandbits(20)*4096+dest()*128+rng.choice([0x17,0x37]))
    p.emit(0x73 if number%2==0 else 0x100073)
    initial = bytes(rng.getrandbits(8) for _ in range(128))
    image = {addr+n: byte for addr,word in p.code.items() for n,byte in enumerate(word.to_bytes(4,'little'))}
    image.update({0x10000+n: byte for n,byte in enumerate(initial)})
    return p.code, initial, image, templates


def generate(seed):
    prefix, old = baseline.generate(seed)
    rows, coverage = [], Counter(old)
    for number in range(8):
        ident = 42+number
        code, initial, image, templates = random_image(seed,number)
        iss = RV32ISS(image); events, fault = iss.run(limit=10000)
        if fault.code!=(8 if number%2==0 else 9) or len(events)>=2048:
            raise ValueError('random generator violated progress/EEI/scoreboard bound')
        rows.append((0,fault.pc,fault.insn,fault.code,len(events),ident,0,0,0,0,0,0,fault.tval))
        rows += [(1,addr,word,*([0]*10)) for addr,word in sorted(code.items())]
        rows += [(2,0x10000+off,int.from_bytes(initial[off:off+4],'little'),*([0]*10)) for off in range(0,128,4)]
        rows += [(3,*event.fields()[1:]) for event in events]
        rows.append((4,*([0]*12)))
        coverage.update(templates)
        coverage.update('random_op:'+op for op in iss.operations)
        coverage['random_programs'] += 1
        coverage['random_retirements'] += len(events)
    coverage['scenarios'] = 50
    coverage['expected_retirements'] = old['expected_retirements']+coverage['random_retirements']
    if not all(coverage.get(key,0)>0 for key in REQUIRED_BINS):
        raise ValueError('missing random instruction/template coverage')
    return prefix+''.join(' '.join('%08x'%(value&MASK) for value in row)+'\n' for row in rows), dict(sorted(coverage.items()))


class RandomProgramTests(unittest.TestCase):
    def test_exact_replay_and_seed_variation(self):
        self.assertEqual(generate(7),generate(7))
        self.assertNotEqual(generate(7)[0],generate(101)[0])

    def test_original_collision_prefix_preserved(self):
        self.assertTrue(generate(1)[0].startswith(baseline.generate(1)[0]))

    def test_complete_random_only_family_and_template_coverage(self):
        for seed in (1,7,101,20261102,314159,271828):
            _, c = generate(seed)
            self.assertTrue(all(c[name]>0 for name in REQUIRED_BINS))
            self.assertEqual(c['random_programs'],8)
            self.assertGreater(c['random_retirements'],1000)

    def test_unique_cases_and_bounded_random_termination(self):
        from dv.reference.retire import stimulus_images
        cases = stimulus_images(generate(1)[0])
        self.assertEqual([case['id'] for case in cases],list(range(50)))
        for case in cases[42:]:
            events, fault = RV32ISS(case['image']).run(limit=10000)
            self.assertLess(len(events),2048); self.assertIn(fault.code,(8,9))

    def test_initialization_is_not_mutated_by_execution(self):
        _, _, image, _ = random_image(1,0)
        before = dict(image); RV32ISS(image).run()
        self.assertEqual(image,before)


if __name__=='__main__': unittest.main(verbosity=2)
