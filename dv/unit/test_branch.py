#!/usr/bin/env python3
"""Independent branch predicates and integer byte-address arithmetic oracle."""
from collections import Counter
import random
import unittest

MASK=(1<<32)-1
OPS=(3,4,5,6,7,8,9,10)
EDGES=(0,1,2,3,31,32,0x7ffffffe,0x7fffffff,0x80000000,0x80000001,
       0xfffffffe,MASK,0x55555555,0xaaaaaaaa,0xffff0000,0xffff)
PCS=(0,4,0x7ffffffc,0x80000000,0xfffffffc)
OFFSETS=(-4096,-2,0,2,4,4094)
REQUIRED_BINS=['op:'+str(op) for op in OPS]+['unsupported','jalr-odd-sum','target-wrap']
REQUIRED_BINS += ['condition:%d:%d'%(op,taken) for op in range(5,11) for taken in (0,1)]
REQUIRED_BINS += ['alignment:%d:%d'%(op,bad) for op in OPS for bad in (0,1)]


def signed(value):
    return int.from_bytes(value.to_bytes(4,'little'), 'little', signed=True)


def oracle(op,pc,a,b,imm):
    if op not in OPS: return 0,0,0,0
    predicates={5:a==b,6:a!=b,7:signed(a)<signed(b),8:signed(a)>=signed(b),9:a<b,10:a>=b}
    taken=op in (3,4) or predicates.get(op,False)
    if not taken: return 0,0,0,1
    target=((a if op==4 else pc)+imm)%(1<<32)
    if op==4: target=(target//2)*2
    return target,1,int(target%4!=0),1


def generate(seed):
    rng=random.Random(seed);rows=[];coverage=Counter()
    def add(op,pc,a,b,imm,group):
        imm=imm&MASK
        result=oracle(op,pc,a,b,imm)
        rows.append((op,pc,a,b,imm,*result));coverage['group:'+group]+=1
        if op not in OPS: coverage['unsupported']+=1;return
        coverage['op:'+str(op)]+=1
        target,taken,bad,_=result
        if op>=5:coverage['condition:%d:%d'%(op,taken)]+=1
        if taken:
            coverage['alignment:%d:%d'%(op,bad)]+=1
            total=(a if op==4 else pc)+imm
            if total>MASK:coverage['target-wrap']+=1
            if op==4 and total%2:coverage['jalr-odd-sum']+=1
    small=[x&MASK for x in range(-16,16)]
    for op in range(5,11):
        for index,a in enumerate(small):
            for b in small:add(op,PCS[index%5],a,b,OFFSETS[index%6],'exhaustive-small')
        for pc in PCS:
            for a in EDGES:
                for b in EDGES:
                    for imm in OFFSETS:add(op,pc,a,b,imm,'edge-cross')
    for a in EDGES:
        for imm in range(-2048,2048):add(4,PCS[a%5],a,rng.getrandbits(32),imm,'jalr-all-immediates')
    jumps=[0,2,-2,-1048576,1048574]+[1<<bit for bit in range(1,20)]
    for pc in PCS:
        for imm in jumps:add(3,pc,rng.getrandbits(32),rng.getrandbits(32),imm,'jal-walking-boundary')
    for op in OPS:
        for _ in range(1024):
            imm=rng.randrange(-2048,2048) if op==4 else rng.randrange(-2048,2048)*2
            add(op,rng.getrandbits(30)*4,rng.getrandbits(32),rng.getrandbits(32),imm,'random')
    for op in set(range(64))-set(OPS):
        for _ in range(16):add(op,rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),'unsupported')
    assert all(coverage[name]>0 for name in REQUIRED_BINS)
    rng.shuffle(rows)
    return ''.join('%02x %08x %08x %08x %08x %08x %x %x %x\n'%row for row in rows),dict(sorted(coverage.items()))


class BranchOracleTests(unittest.TestCase):
    def test_predicates_and_signedness(self):
        self.assertEqual(oracle(7,0,MASK,0,4),(4,1,0,1))
        self.assertEqual(oracle(9,0,MASK,0,4),(0,0,0,1))
        self.assertEqual(oracle(8,0,0x80000000,0x7fffffff,4),(0,0,0,1))
        self.assertEqual(oracle(10,0,0x80000000,0x7fffffff,4),(4,1,0,1))
    def test_not_taken_bad_target_does_not_fault(self):
        self.assertEqual(oracle(5,0,1,2,2),(0,0,0,1))
        self.assertEqual(oracle(6,0,7,7,2),(0,0,0,1))
    def test_taken_misalignment(self):
        self.assertEqual(oracle(5,0,1,1,2),(2,1,1,1))
        self.assertEqual(oracle(3,0,0,0,2),(2,1,1,1))
    def test_jalr_clears_bit_zero_before_alignment(self):
        self.assertEqual(oracle(4,0x100,1,0,0),(0,1,0,1))
        self.assertEqual(oracle(4,0x100,3,0,0),(2,1,1,1))
        self.assertEqual(oracle(4,0x100,0,0,MASK),(0xfffffffe,1,1,1))
    def test_wrapping_and_correct_base(self):
        self.assertEqual(oracle(3,0xfffffffc,0x100,0,4),(0,1,0,1))
        self.assertEqual(oracle(4,0x200,0xfffffffc,0,5),(0,1,0,1))
    def test_unsupported_metadata_zero(self):
        for op in set(range(64))-set(OPS):self.assertEqual(oracle(op,MASK,MASK,MASK,MASK),(0,0,0,0))


if __name__=='__main__':unittest.main(verbosity=2)
