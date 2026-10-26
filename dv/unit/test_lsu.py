#!/usr/bin/env python3
"""Little-endian byte-array oracle for load/store formatting and memory preservation."""
from collections import Counter
import random
import unittest

MASK=(1<<32)-1
# ID -> byte count, store, signed-load
OPS={11:(1,False,True),12:(2,False,True),13:(4,False,False),14:(1,False,False),
     15:(2,False,False),16:(1,True,False),17:(2,True,False),18:(4,True,False)}
REQUIRED_BINS=['unsupported']
for op,(size,_,_) in OPS.items():
    for lane in range(4): REQUIRED_BINS.append('%s:%d:%d'%('bad' if lane%size else 'lane',op,lane))
EDGES=[0,1,0x7f,0x80,0xff,0x100,0x7fff,0x8000,0xffff,0x7fffffff,0x80000000,MASK,0x55555555,0xaaaaaaaa]


def oracle(op,addr,data,word):
    memory=bytearray(word.to_bytes(4,'little'))
    if op not in OPS:return 0,0,0,0,0,0,word
    size,store,sign=OPS[op];lane=addr%4
    if addr%size:return 0,0,0,0,1,1,word
    enable=sum(2**index for index in range(lane,lane+size))
    if store:
        payload=data.to_bytes(4,'little')[:size]
        bus=bytearray(4);bus[lane:lane+size]=payload
        memory[lane:lane+size]=payload
        return 0,int.from_bytes(bus,'little'),enable,1,0,1,int.from_bytes(memory,'little')
    value=int.from_bytes(memory[lane:lane+size],'little',signed=sign)&MASK
    return value,0,enable,0,0,1,word


def generate(seed):
    rng=random.Random(seed);rows=[];coverage=Counter()
    def add(op,addr,data,word,group):
        result=oracle(op,addr,data,word);rows.append((op,addr,data,word,*result));coverage['group:'+group]+=1
        if op in OPS:coverage['%s:%d:%d'%('bad' if addr%OPS[op][0] else 'lane',op,addr%4)]+=1
        else:coverage['unsupported']+=1
    for op in OPS:
        for lane in range(4):
            for data in EDGES:
                for word in EDGES:add(op,0xfffffffc+lane,data,word,'edge-cross')
        for _ in range(4096):add(op,rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),'random')
    for op in (11,14,16):
        for lane in range(4):
            for value in range(256):
                memory=bytearray(rng.getrandbits(32).to_bytes(4,'little'));memory[lane]=value
                data=(rng.getrandbits(24)*256)+value
                add(op,0x10000000+lane,data,int.from_bytes(memory,'little'),'all-byte-values')
    halves=sorted(set([x&0xffff for x in EDGES]+[1<<bit for bit in range(16)]+[0xffff^(1<<bit) for bit in range(16)]))
    for op in (12,15,17):
        for lane in range(4):
            for value in halves:
                memory=bytearray(rng.getrandbits(32).to_bytes(4,'little'))
                if lane%2==0:memory[lane:lane+2]=value.to_bytes(2,'little')
                add(op,0x10000+lane,(rng.getrandbits(16)<<16)+value,int.from_bytes(memory,'little'),'halfword-walking-sign')
    for op in (13,18):
        for lane in range(4):
            for bit in range(32):
                for value in (1<<bit,MASK^(1<<bit)):add(op,lane,value,rng.getrandbits(32),'word-walking')
    for op in set(range(64))-OPS.keys():
        for _ in range(32):add(op,rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),'unsupported')
    assert all(coverage[name]>0 for name in REQUIRED_BINS)
    rng.shuffle(rows)
    return ''.join('%02x %08x %08x %08x %08x %08x %x %x %x %x %08x\n'%row for row in rows),dict(sorted(coverage.items()))


class LsuOracleTests(unittest.TestCase):
    def test_byte_sign_and_zero_extension_all_lanes(self):
        for lane in range(4):
            word=int.from_bytes(bytes([0x80]*4),'little')
            self.assertEqual(oracle(11,lane,0,word)[0],0xffffff80)
            self.assertEqual(oracle(14,lane,0,word)[0],0x80)
    def test_halfword_sign(self):
        self.assertEqual(oracle(12,2,0,0x80001122)[0],0xffff8000)
        self.assertEqual(oracle(15,2,0,0x80001122)[0],0x8000)
    def test_read_strobes(self):
        self.assertEqual(oracle(14,3,0,MASK)[2],8)
        self.assertEqual(oracle(15,2,0,MASK)[2],12)
        self.assertEqual(oracle(13,0,0,MASK)[2],15)
    def test_store_neighbor_preservation_and_unused_lanes(self):
        self.assertEqual(oracle(16,1,0x123456aa,0x44332211),(0,0x0000aa00,2,1,0,1,0x4433aa11))
        self.assertEqual(oracle(17,2,0x1234aabb,0x44332211),(0,0xaabb0000,12,1,0,1,0xaabb2211))
    def test_bad_alignment_suppresses_effect_metadata(self):
        for op in (12,13,15,17,18):
            for lane in range(4):
                if lane%OPS[op][0]:self.assertEqual(oracle(op,lane,MASK,0x12345678),(0,0,0,0,1,1,0x12345678))
    def test_unsupported_and_word(self):
        self.assertEqual(oracle(18,0,0xaabbccdd,0x12345678),(0,0xaabbccdd,15,1,0,1,0xaabbccdd))
        for op in set(range(64))-OPS.keys():self.assertEqual(oracle(op,3,MASK,0x12345678),(0,0,0,0,0,0,0x12345678))


if __name__=='__main__':unittest.main(verbosity=2)
