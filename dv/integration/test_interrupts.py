"""Independent literal ISA/CSR tests and timer IRQ stimulus for approved v0.3."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'unit'))
from interrupt_model import InterruptISS,IrqPeripheral,check_trace
from rv32_iss import Retirement,Fault
from test_mmio import Agent,IDLE,TIMER


class IrqAgent(Agent):
    def __init__(self,seed):super().__init__(seed);self.m=IrqPeripheral()
    def tick(self,reset=0,g=IDLE,t=IDLE):
        raw=self.rng.getrandbits(16);pre=int(not reset and self.m.flag and self.m.irq_enable)
        row,accepted,replies=self.m.edge(reset,raw,g,t);post=int(not reset and self.m.flag and self.m.irq_enable)
        self.rows.append((*row,pre,post));return accepted,replies


def timer_corpus(seed):
    a=IrqAgent(seed);a.tick(reset=1);a.tick(reset=1);a.idle(3)
    a.configure(compare=4,ctrl=7);a.idle(9)
    a.transact(1,TIMER+8,1,4,1) # counter disabled, pending IRQ must remain high
    a.transact(1,TIMER+12,expect=(0,1));a.idle(4)
    a.transact(1,TIMER+8,1,0,1);a.transact(1,TIMER+12,expect=(0,1))
    a.transact(1,TIMER+8,1,4,1);a.transact(1,TIMER+12,1,1,1);a.transact(1,TIMER+12,expect=(0,0))
    a.configure(compare=16,ctrl=7);a.match_collision(TIMER+12,1,1);a.transact(1,TIMER+12,expect=(0,1))
    for offset in range(4):
        for mask in range(16):
            a.transact(1,TIMER+8+offset,1,a.rng.getrandbits(32),mask,stall=3)
            a.transact(1,TIMER+8)
    # An accepted IRQ-enable write is canceled before response effect.
    a.transact(1,TIMER+8,1,0,1);a.tick(t=(1,TIMER+8,1,7,1,0));a.tick(reset=1)
    a.transact(1,TIMER+8,expect=(0,0));a.transact(1,TIMER+12,expect=(0,0))
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in a.rows)


class InterruptOracleTests(unittest.TestCase):
    def test_ram_cannot_execute_csr_or_return_encoding(self):
        for word in (0x30200073,0x340fd2f3):
            iss=InterruptISS({0x10000+b:v for b,v in enumerate(word.to_bytes(4,'little'))});iss.pc=0x10000
            fault=iss.step_extended([],0);self.assertIsInstance(fault,Fault);self.assertEqual(fault.code,3)
    def test_literal_csr_access_and_mret(self):
        # csrrwi x5,mscratch,31; csrrs x6,mscratch,x0; mret
        words=[0x340fd2f3,0x34002373,0x30200073]
        iss=InterruptISS({i*4+b:v for i,w in enumerate(words) for b,v in enumerate(w.to_bytes(4,'little'))})
        e=iss.step_extended([],0);self.assertEqual((e.rd_data,iss.csr.state[0x340]),(0,31))
        self.assertEqual(iss.step_extended([],0).rd_data,31)
        iss.csr.state[0x341]=0x100;iss.csr.state[0x300]=0x1880
        self.assertEqual(iss.step_extended([],0).next_pc,0x100);self.assertEqual(iss.csr.state[0x300],0x1888)
    def test_zero_valued_nonzero_source_still_faults_on_id_write(self):
        word=(0xf11<<20)|(5<<15)|(2<<12)|(6<<7)|0x73
        iss=InterruptISS(dict(enumerate(word.to_bytes(4,'little'))));self.assertIsInstance(iss.step_extended([],0),Fault)
    def test_irq_pc_and_nested_frame(self):
        iss=InterruptISS({});iss.pc=0x240;iss.order=7;iss.csr.state.update({0x300:0x1888,0x304:0x800,0x305:0x400})
        self.assertEqual(iss.trap(True,[],1),(7,0x240,0,0x8000000b,0,0x400));self.assertEqual(iss.csr.state[0x300],0x1880)
        with self.assertRaisesRegex(ValueError,'MASK_OR_LEVEL'):iss.trap(True,[],1)
    def test_malformed_trace_is_not_success(self):
        for text in ('','0 1 2\n'):
            with self.assertRaisesRegex(ValueError,'SHAPE'):check_trace(text,bytes(65536),{},8)
    def test_timer_irq_persists_when_count_disabled_and_uses_bit2(self):
        a=IrqAgent(1);a.tick(reset=1);a.configure(4,ctrl=7);a.idle(8)
        self.assertTrue(a.m.flag);a.transact(1,TIMER+8,1,4,1)
        self.assertFalse(a.m.clock.ctrl&1);self.assertTrue(a.m.irq_enable and a.m.flag)
        a.transact(1,TIMER+12,1,1,1);self.assertFalse(a.m.flag)
    def test_timer_stimulus_replays(self):
        self.assertEqual(timer_corpus(1),timer_corpus(1));self.assertNotEqual(timer_corpus(1),timer_corpus(20261107))


if __name__=='__main__':unittest.main(verbosity=2)
