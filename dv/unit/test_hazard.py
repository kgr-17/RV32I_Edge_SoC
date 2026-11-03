#!/usr/bin/env python3
"""Unresolved producer set vs actually consumed architectural register IDs."""
from collections import Counter
import random
import unittest

REQUIRED_BINS=['a_only','b_only','both','none','disabled_consumer','disabled_producer','x0_ignored']


def oracle(flags,a,b,dest):
    pending={dest} if (flags&8 and flags&16 and flags&32 and dest!=0) else set()
    sources={}
    if flags&1:
        if flags&2:sources['a']=a
        if flags&4:sources['b']=b
    waiting={name for name,reg in sources.items() if reg in pending}
    return int('a'in waiting),int('b'in waiting),int(bool(waiting))


def generate(seed):
    rng=random.Random(seed);rows=[];coverage=Counter()
    def add(flags,a,b,dest):
        expected=oracle(flags,a,b,dest);rows.append((flags,a,b,dest,*expected))
        coverage[{(0,0):'none',(1,0):'a_only',(0,1):'b_only',(1,1):'both'}[expected[:2]]]+=1
        if not flags&1:coverage['disabled_consumer']+=1
        if not flags&8 or not flags&16 or not flags&32:coverage['disabled_producer']+=1
        if dest==0:coverage['x0_ignored']+=1
    for a in range(32):
        for b in range(32):
            for dest in range(32):add(63,a,b,dest)
    for flags in range(64):
        for ids in ((0,0,0),(1,1,1),(1,2,1),(2,1,1),(31,31,31),(3,7,0),(3,7,9)):add(flags,*ids)
    for _ in range(4096):add(rng.randrange(64),*(rng.randrange(32)for _ in range(3)))
    assert all(coverage[k]>0 for k in REQUIRED_BINS)
    return ''.join(' '.join('%x'%v for v in row)+'\n'for row in rows),dict(sorted(coverage.items()))


class HazardOracleTests(unittest.TestCase):
    def test_both_sources_and_exact_identity(self):
        self.assertEqual(oracle(63,5,5,5),(1,1,1))
        self.assertEqual(oracle(63,5,6,7),(0,0,0))
    def test_no_zero_dependency(self):self.assertEqual(oracle(63,0,0,0),(0,0,0))
    def test_every_enable_qualifies(self):
        for bit in (0,3,4,5):self.assertEqual(oracle(63^(1<<bit),5,5,5),(0,0,0))
    def test_unused_sources_are_not_dependencies(self):
        self.assertEqual(oracle(63^2,5,5,5),(0,1,1))
        self.assertEqual(oracle(63^4,5,5,5),(1,0,1))


if __name__=='__main__':unittest.main(verbosity=2)
