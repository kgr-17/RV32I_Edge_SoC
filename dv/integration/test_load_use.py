#!/usr/bin/env python3
"""Hand-assembled actual pipeline dependencies, long waits and WB refresh."""
from collections import Counter
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from dv.integration.test_core_smoke import Program,i,r,s

REQUIRED_BINS=['dependent_a','dependent_b','store_payload','held_wb_refresh','load_x0','variable_data']
NEGATIVE_FULL_PROGRAM=True
NEGATIVE_DIAGNOSTIC='LOAD_USE_MISMATCH fault'


def generate(seed):
    rng=random.Random(seed);coverage=Counter();programs=[]
    def new():
        p=Program(len(programs),coverage);programs.append(p)
        p.constant(1,0x10000);p.access('LW',0,4,rd=10)
        return p
    def store(p,rd,offset,value):
        p.emit('SW',s(2,1,rd,offset),memory=(1,1,0x10000+offset,15,value,0))
        p.memory[offset:offset+4]=value.to_bytes(4,'little')
    p=new();p.access('LW',4,4,rd=5)
    value=(0x44332211*2)%2**32
    p.emit('ADD',r(7,0,5,5),7,value);coverage['dependent_a']+=1;coverage['dependent_b']+=1
    p.emit('ADDI',i(0x13,8,0,7,-1),8,(value-1)%2**32)
    store(p,7,8,value);p.access('LW',8,4,rd=9);p.fault('ECALL',0x73,8)
    p=new();p.emit('ADDI',i(0x13,5,0,0,85),5,85);p.access('LW',4,4,rd=6)
    p.emit('ADDI',i(0x13,7,0,5,3),7,88);coverage['held_wb_refresh']+=1
    store(p,7,8,88);p.access('LW',8,4,rd=8);p.fault('ECALL',0x73,8)
    p=new();p.access('LW',4,4,rd=2);p.access('SB',0,1,write=True,value=0x44332211)
    coverage['store_payload']+=1;p.access('LW',0,4,rd=3);p.access('LW',4,4,rd=4)
    p.emit('ADD',r(6,0,3,4),6,(0x80ff7f11+0x44332211)%2**32);p.fault('ECALL',0x73,8)
    p=new();p.access('LW',4,4,rd=0);p.emit('ADDI',i(0x13,7,0,0,17),7,17)
    coverage['load_x0']+=1;p.fault('ECALL',0x73,8)
    p=new()
    # Reinitialize only test data, then regenerate the already-encoded priming
    # load expectation from its known first word (unchanged).
    memory=bytearray(p.initial)
    for offset in range(4,36,4):memory[offset:offset+4]=rng.getrandbits(32).to_bytes(4,'little')
    p.initial=bytes(memory);p.memory=bytearray(memory)
    for offset in range(4,36,4):
        p.access('LW',offset,4,rd=5)
        expected=(int.from_bytes(p.memory[offset:offset+4],'little')*2)%2**32
        p.emit('ADD',r(7,0,5,5),7,expected);store(p,7,60+offset,expected)
        p.access('LW',60+offset,4,rd=8);coverage['variable_data']+=1
    p.fault('ECALL',0x73,8)
    rows=[row for p in programs for row in p.rows()]
    coverage['scenarios']=len(programs);coverage['expected_retirements']=sum(len(p.expected)for p in programs)
    assert all(coverage[name]>0 for name in REQUIRED_BINS)
    return ''.join(' '.join('%08x'%(v%2**32)for v in row)+'\n'for row in rows),dict(sorted(coverage.items()))


class LoadUsePrograms(unittest.TestCase):
    def test_nonempty_replayable_scenarios(self):
        text,coverage=generate(1);self.assertEqual(text,generate(1)[0]);self.assertEqual(coverage['scenarios'],5)
    def test_data_seed_changes_without_reducing_scenarios(self):
        self.assertNotEqual(generate(1)[0],generate(20261102)[0])
        self.assertEqual(generate(1)[1],generate(20261102)[1])
    def test_expected_rows_are_real_retirements(self):
        text,c=generate(1);self.assertEqual(sum(line.split()[0]=='00000003'for line in text.splitlines()),c['expected_retirements'])
    def test_all_dependency_categories_present(self):
        self.assertTrue(all(generate(1)[1][name] for name in REQUIRED_BINS))


if __name__=='__main__':unittest.main(verbosity=2)
