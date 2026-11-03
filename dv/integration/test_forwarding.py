#!/usr/bin/env python3
"""Select the newest architectural producer, then check its availability."""
from collections import Counter
import random
import unittest

MASK=2**32-1
REQUIRED_BINS=['%s:%s'%(port,tag)for port in ('a','b')for tag in
               ('invalid','unused','x0','captured','ex','wb','blocked','newest_wins','load_shadows_wb')]
REQUIRED_BINS+=['dual_ex_wb','dual_wb_ex','dual_blocked']


def oracle(flags,ra,rb,ex_rd,wb_rd,a,b,ex_value,wb_value):
    producers=[]
    if flags&64 and flags&128 and wb_rd:
        producers.append({'age':0,'rd':wb_rd,'value':wb_value,'ready':True,'selector':2})
    if flags&8 and flags&16 and ex_rd:
        producers.append({'age':1,'rd':ex_rd,'value':ex_value,'ready':not bool(flags&32),'selector':1})
    values=[];selectors=[];blocked=[];tags=[]
    for used,rs,captured in ((flags&2,ra,a),(flags&4,rb,b)):
        if not flags&1:result=(0,0,0,'invalid')
        elif not used:result=(0,0,0,'unused')
        elif rs==0:result=(0,0,0,'x0')
        else:
            candidates=[p for p in producers if p['rd']==rs]
            if not candidates:result=(captured,0,0,'captured')
            else:
                newest=max(candidates,key=lambda p:p['age'])
                if not newest['ready']:result=(0,3,1,'blocked')
                else:result=(newest['value'],newest['selector'],0,'ex'if newest['age']==1 else'wb')
        value,selector,wait,tag=result
        values.append(value);selectors.append(selector);blocked.append(wait);tags.append(tag)
    return (*values,*selectors,*blocked),tags


def generate(seed):
    rng=random.Random(seed);rows=[];coverage=Counter()
    def add(flags,ra,rb,ex_rd,wb_rd,group,values=None):
        values=values if values is not None else [rng.getrandbits(32)for _ in range(4)]
        inputs=(flags,ra,rb,ex_rd,wb_rd,*values)
        expected,tags=oracle(*inputs)
        rows.append((*inputs,*expected));coverage['group:'+group]+=1
        for port,rs,tag in zip(('a','b'),(ra,rb),tags):
            coverage[port+':'+tag]+=1
            if rs and flags&1 and flags&(2 if port=='a' else 4) and flags&8 and flags&16 and ex_rd==rs and flags&64 and flags&128 and wb_rd==rs:
                coverage[port+':'+('load_shadows_wb'if flags&32 else'newest_wins')]+=1
        pair=expected[2:4]
        if pair==(1,2):coverage['dual_ex_wb']+=1
        if pair==(2,1):coverage['dual_wb_ex']+=1
        if pair==(3,3):coverage['dual_blocked']+=1
    add(0xdf,1,2,3,4,'anchors',[1,2,3,4])
    add(0xff,5,5,5,5,'anchors',[1,2,3,4])
    add(0xdf,1,2,1,2,'anchors')
    add(0xdf,2,1,1,2,'anchors')
    for ra in range(32):
        for ex_rd in range(32):
            for wb_rd in range(32):
                for flags in (0xdf,0xff):add(flags,ra,31-ra,ex_rd,wb_rd,'id-cross')
    identities=((0,0,0,0),(1,1,1,1),(1,2,1,2),(2,1,1,2),(31,31,31,31),(3,7,0,7),(3,7,3,0),(3,7,9,10))
    for flags in range(256):
        for ids in identities:add(flags,*ids,'qualifier-cross')
    for value in [0,MASK]+[n for bit in range(32)for n in (2**bit,MASK^2**bit)]:
        for ids in identities:add(0xdf,*ids,'walking-data',[value,MASK^value,value,MASK^value])
    for _ in range(4096):add(rng.randrange(256),*(rng.randrange(32)for _ in range(4)),'random')
    assert all(coverage[name]>0 for name in REQUIRED_BINS),coverage
    return ''.join(' '.join('%x'%v for v in row)+'\n'for row in rows),dict(sorted(coverage.items()))


class ForwardingOracleTests(unittest.TestCase):
    def test_newest_producer_wins_each_operand(self):
        expected,_=oracle(0xdf,5,5,5,5,1,2,3,4)
        self.assertEqual(expected,(3,3,1,1,0,0))

    def test_unavailable_newest_load_cannot_fall_back_to_older_wb(self):
        expected,_=oracle(0xff,5,5,5,5,1,2,3,4)
        self.assertEqual(expected,(0,0,3,3,1,1))

    def test_x0_unused_and_invalid_zero_every_effect(self):
        for flags,ra,rb in ((0xdf,0,0),(0xd9,1,2),(0xde,1,2)):
            self.assertEqual(oracle(flags,ra,rb,ra,rb,MASK,MASK,MASK,MASK)[0],(0,0,0,0,0,0))

    def test_independent_operands_and_write_qualification(self):
        self.assertEqual(oracle(0xdf,5,6,5,6,1,2,3,4)[0],(3,4,1,2,0,0))
        self.assertEqual(oracle(0xcf,5,6,5,6,1,2,3,4)[0],(1,4,0,2,0,0))


if __name__=='__main__':unittest.main(verbosity=2)
