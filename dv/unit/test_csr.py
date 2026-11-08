"""Independent integer-state CSR and interrupt-admission models, v0.3."""
import random
import unittest

MASKS={0x300:0x88,0x301:0,0x304:0x800,0x305:0xfffffffc,0x310:0,
       0x340:0xffffffff,0x341:0xfffffffc,0x342:0xffffffff,0x343:0xffffffff,0x344:0}
IDS=set(range(0xf11,0xf15))


class Model:
    def __init__(self):self.reset();self.continuation=0;self.draining=False
    def reset(self):self.state={a:0 for a in MASKS};self.state.update({0x300:0x1800,0x301:0x40000100})
    def raw(self,addr,irq,reset):return (int(bool(irq) and not reset)*0x800) if addr==0x344 else self.state.get(addr,0)
    def view(self,x):
        reset,irq,addr,op,data,sz,rz,commit,trap,mret,pc,cause,tval,eligible,empty,synchronous,retire,npc,target=x
        valid=op in (1,2,3,5,6,7);read=valid and not(op in (1,5) and rz)
        write=valid and (op in (1,5) or not sz);error=bool(op and (not valid or addr not in MASKS and addr not in IDS or addr in IDS and write))
        old=self.raw(addr,irq,reset);candidate=data if op in (1,5) else old|data if op in (2,6) else old&(~data&0xffffffff)
        mask=MASKS.get(addr,0);new=(candidate&mask)|(old&(~mask&0xffffffff))
        if reset or error:read=write=False
        boundary=not reset and self.draining and empty and not synchronous
        return (int(read),int(write),int(error),old if read else 0,new if write else 0,self.state[0x305],self.state[0x341],
                int(not reset and irq and self.state[0x304]&0x800 and self.state[0x300]&8),
                int(not reset and self.draining),int(not reset and (self.draining or eligible)),int(boundary and eligible),int(boundary),self.continuation)
    def edge(self,x):
        pre=self.view(x);reset,irq,addr,op,data,sz,rz,commit,trap,mret,pc,cause,tval,eligible,empty,synchronous,retire,npc,target=x
        if reset:self.reset();self.continuation=0;self.draining=False
        else:
            if trap:
                self.state[0x300]=0x1800+(0x80 if self.state[0x300]&8 else 0)
                self.state.update({0x341:pc&0xfffffffc,0x342:cause,0x343:tval})
            elif mret:self.state[0x300]=0x1880+(8 if self.state[0x300]&0x80 else 0)
            elif commit and pre[1] and addr in self.state and addr!=0x344:self.state[addr]=pre[4]
            if retire:self.continuation=npc
            if synchronous:self.draining=False;self.continuation=target
            elif self.draining:
                if empty:self.draining=False
            elif eligible:self.draining=True
        return pre,self.view(x)


def corpus(seed):
    rng=random.Random(seed);m=Model();rows=[]
    def tick(reset=0,irq=0,addr=0x300,op=2,data=0,sz=1,rz=0,commit=1,trap=0,mret=0,pc=0,cause=0,tval=0,eligible=0,empty=0,synchronous=0,retire=0,npc=0,target=0):
        x=(reset,irq,addr,op,data,sz,rz,commit,trap,mret,pc,cause,tval,eligible,empty,synchronous,retire,npc,target)
        pre,post=m.edge(x);rows.append((*x,*pre,*post))
    tick(reset=1);tick(reset=1,trap=1,mret=1)
    for addr in [*MASKS,*IDS,0,0xfff,0xc00,0x7b0]:
        for op in range(8):
            for sz in (0,1):
                for rz in (0,1):
                    for data in (0,0xffffffff,0x800,0x1234567b):tick(addr=addr,op=op,sz=sz,rz=rz,data=data,irq=1)
    # Immediate observation of trap/MRET effects and mask eligibility.
    tick(addr=0x300,op=1,data=8);tick(addr=0x304,op=1,data=0x800,irq=1)
    tick(irq=1,trap=1,pc=0x1237,cause=0x8000000b,tval=0x99887766)
    for addr in MASKS:tick(addr=addr,irq=1)
    tick(mret=1,irq=1);tick(addr=0x300,irq=1)
    tick(retire=1,npc=0x88);tick(eligible=1);tick(eligible=0,empty=0);tick(eligible=0,empty=1)
    tick(eligible=1);tick(eligible=1,empty=1);tick(synchronous=1,target=0x400)
    for n in range(4096):
        empty=rng.randrange(2);synchronous=int(n%97==0)
        tick(reset=int(n%211==0),irq=rng.randrange(2),addr=rng.choice([*MASKS,*IDS,0xfff]),op=rng.randrange(8),data=rng.getrandbits(32),
            sz=rng.randrange(2),rz=rng.randrange(2),commit=rng.randrange(2),trap=int(n%101==0),mret=int(n%59==0),pc=rng.getrandbits(32),cause=rng.getrandbits(32),tval=rng.getrandbits(32),
            eligible=rng.randrange(2),empty=empty,synchronous=synchronous,retire=int(not empty and not synchronous and rng.randrange(2)),npc=rng.getrandbits(30)*4,target=0x400)
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in rows)


class CsrTests(unittest.TestCase):
    def test_zero_value_is_not_zero_index(self):
        m=Model();base=[0,0,0xf11,2,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0]
        self.assertEqual(m.view(base)[:3],(1,0,0));base[5]=0;self.assertEqual(m.view(base)[:3],(0,0,1))
    def test_masks_and_return(self):
        m=Model();x=[0,0,0x300,1,0xffffffff,0,0,1,0,0,0,0,0,0,0,0,0,0,0]
        m.edge(x);self.assertEqual(m.state[0x300],0x1888)
        x[8]=1;x[10]=0x107;m.edge(x);self.assertEqual((m.state[0x300],m.state[0x341]),(0x1880,0x104))
        x[8]=0;x[9]=1;m.edge(x);self.assertEqual(m.state[0x300],0x1888)
    def test_canceled_drain_rechecks_level_and_uses_retired_pc(self):
        m=Model();x=[0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,1,0x200,0]
        m.edge(x);x[16]=0;x[13]=1;m.edge(x);x[13]=0;x[14]=1
        self.assertEqual(m.view(x)[10:13],(0,1,0x200));m.edge(x);self.assertFalse(m.draining)
    def test_replay(self):
        self.assertEqual(corpus(1),corpus(1));self.assertNotEqual(corpus(1),corpus(20261107))


if __name__=='__main__':unittest.main(verbosity=2)
