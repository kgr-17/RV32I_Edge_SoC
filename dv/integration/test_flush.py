#!/usr/bin/env python3
"""Directed control/age cases plus existing ISA and dependency stimuli."""
from collections import Counter
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from dv.integration import test_core_smoke as core
from dv.integration import test_load_use as loads

REQUIRED_BINS=core.REQUIRED_BINS+['branch_memory_hold','load_jalr','older_fault_store','stale_fetch_fault','wrongpath_store','wrongpath_illegal']
NEGATIVE_FULL_PROGRAM=True
NEGATIVE_DIAGNOSTIC='CONTROL_MISMATCH fault'


def generate(seed):
    rows=[];coverage=Counter()
    for generator,offset in ((core.generate,0),(loads.generate,11)):
        text,bins=generator(seed);coverage.update(bins)
        for line in text.splitlines():
            row=[int(v,16)for v in line.split()]
            if row[0]==0:row[5]+=offset
            rows.append(tuple(row))
    programs=[]
    def new():
        p=core.Program(16+len(programs),coverage);programs.append(p)
        p.constant(1,0x10000);p.access('LW',0,4,rd=10)
        return p
    for illegal in (False,True):
        p=new();p.access('LW',4,4,rd=5)
        p.emit('BEQ',core.b(0,0,0,8),next_pc=p.pc+8)
        p.code[p.pc]=0xffffffff if illegal else core.s(2,1,0,8);p.pc+=4
        p.emit('ADDI',core.i(0x13,7,0,0,7),7,7);p.fault('ECALL',0x73,8)
        coverage['branch_memory_hold']+=1
        coverage['wrongpath_illegal'if illegal else'wrongpath_store']+=1
    p=new()
    memory=bytearray(p.initial);memory[4:8]=(25).to_bytes(4,'little');p.initial=bytes(memory);p.memory=bytearray(memory)
    p.access('LW',4,4,rd=5)
    p.emit('JALR',core.i(0x67,6,0,5,0),6,20,next_pc=24)
    p.code[p.pc]=core.s(2,1,0,8);p.pc+=4
    p.emit('ADDI',core.i(0x13,7,0,6,1),7,21);p.fault('ECALL',0x73,8)
    coverage['load_jalr']+=1;coverage['wrongpath_store']+=1
    p=new();p.fault('ILLEGAL',0xffffffff,1,0xffffffff)
    p.code[p.pc+4]=core.s(2,1,0,8);p.code[p.pc+8]=core.i(0x13,7,0,0,99)
    coverage['older_fault_store']+=1
    p=core.Program(16+len(programs),coverage);programs.append(p)
    p.emit('JAL',core.j(0,0xfff8),next_pc=0xfff8);p.pc=0xfff8
    p.emit('ADDI',core.i(0x13,5,0,0,9),5,9)
    p.emit('JAL',core.j(0,0x20-0xfffc),next_pc=0x20);p.pc=0x20
    p.emit('ADDI',core.i(0x13,7,0,5,1),7,10);p.fault('ECALL',0x73,8)
    coverage['stale_fetch_fault']+=1
    rows += [row for p in programs for row in p.rows()]
    coverage['scenarios']=21
    coverage['expected_retirements']=sum(row[0]==3 for row in rows)
    assert all(coverage[key]>0 for key in REQUIRED_BINS)
    return ''.join(' '.join('%08x'%(v%2**32)for v in row)+'\n'for row in rows),dict(sorted(coverage.items()))


class ControlPrograms(unittest.TestCase):
    def test_unique_complete_scenario_ids(self):
        text,c=generate(1);ids=[int(line.split()[5],16)for line in text.splitlines()if int(line.split()[0],16)==0]
        self.assertEqual(ids,list(range(21)));self.assertEqual(c['scenarios'],21)
    def test_required_families_and_control_categories(self):
        self.assertTrue(all(generate(1)[1][key]>0 for key in REQUIRED_BINS))
    def test_top_rom_redirect_case_is_present(self):
        text,_=generate(1)
        self.assertTrue(any(line.split()[0]=='00000001'and line.split()[1]=='0000fffc'for line in text.splitlines()))
    def test_retirement_count_excludes_initialization(self):
        text,c=generate(1);self.assertEqual(c['expected_retirements'],sum(line.split()[0]=='00000003'for line in text.splitlines()))


if __name__=='__main__':unittest.main(verbosity=2)
