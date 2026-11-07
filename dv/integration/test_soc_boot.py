"""Independent fabric stimulus, architectural/serial oracle tests for T031."""
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'firmware'))
from memory_model import pattern_words
from soc_model import BusModel, SocISS, decode_uart, check_trace, LANES


def pattern_rom():
    return b''.join(w.to_bytes(4,'little') for w in pattern_words())


def fabric_vectors(seed):
    rng=random.Random(seed);m=BusModel(pattern_rom(),8);rows=[]
    def tick(reset=0,iv=0,ia=0,iready=0,dv=0,da=0,dw=0,dd=0,db=15,dready=0):
        x=(reset,1,rng.getrandbits(16),iv,ia,iready,dv,da,dw,dd,db,dready)
        pre,post,accepted=m.edge(x);rows.append((*x,*pre,*post));return pre,accepted
    def transfer(ia,da,write=0,data=0,mask=15,stall=0):
        accepted=[False,False]
        for _ in range(200):
            _,got=tick(iv=int(not accepted[0]),ia=ia,dv=int(not accepted[1]),da=da,dw=write,dd=data,db=mask)
            accepted=[a or b for a,b in zip(accepted,got)]
            if all(accepted):break
        else:raise ValueError('SOC_STIMULUS_REQUEST_TIMEOUT')
        for _ in range(stall):tick(ia=ia,da=da)
        for _ in range(4):
            tick(ia=ia,da=da,iready=1,dready=1)
            if m.ip is None and m.dp is None:break
        else:raise ValueError('SOC_STIMULUS_RESPONSE_TIMEOUT')
        m.completed.clear()
    tick(reset=1);tick(reset=1)
    # Accepted RAM store and ROM fetch are canceled by reset before response.
    tick(iv=1,ia=4,dv=1,da=0x10000,dw=1,dd=0xdeadbeef)
    for _ in range(3):tick()
    tick(reset=1)
    transfer(0,0x10000)
    if m.word(0x10000):raise ValueError('SOC_ORACLE_EARLY_WRITE')
    # Distinct simultaneous dual-ROM reads, all address bits plus random pairs.
    addresses=sorted({0,1,16383,*[1<<b for b in range(14)],*[rng.randrange(16384) for _ in range(256)]})
    for word in addresses:transfer(word*4,(16383-word)*4,stall=rng.randrange(4))
    # Write all selected locations BEFORE reading any, exposing address aliasing.
    for word in addresses:transfer(word*4,0x10000+word*4,1,((word+1)*0x10203041^seed)&0xffffffff)
    for word in reversed(addresses):transfer(word*4,0x10000+word*4,stall=rng.randrange(4))
    # Every offset/mask combination, ROM protection, MMIO holes/RO accesses.
    for base in (0x40,0x10040,0x10000000,0x10000020,0x10000100):
        for offset in range(4):
            for mask in range(16):
                transfer(0,base+offset,int((mask+offset)%2==0),rng.getrandbits(32),mask,2)
    for addr in (0xffff,0x20000,0x10000010,0x1000001c,0x10000030,0x1000003c,0x10000040,0x10000110,0xffffffff):
        transfer(addr,addr,stall=4)
    for bit in range(16,32):transfer(1<<bit,(1<<bit)|0x10040,1,0x87654321)
    for addr in (1,2,3,0x10000,0x1fffc,0x10000000):transfer(addr,0,1,0xffffffff)
    # Known UART configuration then busy request held until frame finishes.
    tick(reset=1)
    transfer(0,0x10000000,1,0x41,1,4)
    transfer(4,0x10000000,1,0x42,1,4)
    for _ in range(100):tick(iready=1,dready=1)
    # Reset-canceled GPIO side effect and RAM persistent write already committed.
    transfer(8,0x10000,1,0x12345678)
    tick(dv=1,da=0x10000020,dw=1,dd=0xffff,db=3)
    tick(reset=1);transfer(0,0x10000)
    summary={'cycles':len(rows),'requests':m.requests,'replies':m.replies,'canceled':m.canceled,
             'ram_write_effects':len(m.effects),'ram_words':len(addresses),'seed':seed}
    assert all(m.requests[ch]==m.replies[ch]+m.canceled[ch] for ch in (0,1))
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in rows),summary


class SocOracleTests(unittest.TestCase):
    def test_reset_cancels_uncommitted_store_but_preserves_committed_ram(self):
        m=BusModel(bytes(65536),8)
        idle=(0,1,0,0,0,0,0,0,0,0,15,0)
        store=(0,1,0,0,0,0,1,0x10000,1,0x12345678,15,0)
        m.edge(store);self.assertEqual(m.word(0x10000),0)
        m.edge((1,*idle[1:]));self.assertEqual(m.word(0x10000),0)
        m.edge(store);m.edge((*idle[:-1],1));self.assertEqual(m.word(0x10000),0x12345678)
        m.edge((1,*idle[1:]));self.assertEqual(m.word(0x10000),0x12345678)
    def test_full_address_and_lane_decoding(self):
        for offset in range(4):
            for mask in range(16):
                self.assertEqual(BusModel.target(0x10000+offset,0,mask),'ram' if (offset,mask) in LANES else 'bad')
        for addr in (0x20000,0x10010000,0x20000020,0x10000110,0xffffffff):
            self.assertEqual(BusModel.target(addr,0,15),'bad')
        self.assertEqual(BusModel.target(0,1,15),'bad')
    def test_mmio_signed_byte_and_unsigned_half_independent(self):
        # LB x5,1(x1), then LHU x6,2(x1).
        raw=(0x00108283).to_bytes(4,'little')+(0x0020d303).to_bytes(4,'little')
        iss=SocISS(dict(enumerate(raw)));iss.regs[1]=0x10000000
        packet={'addr':0x10000001,'write':0,'be':2,'data':0,'read':0x8000,'error':0}
        self.assertEqual(iss.step_for_bus([packet]).rd_data,0xffffff80)
        packet.update(addr=0x10000002,be=12,read=0xfedc0000)
        self.assertEqual(iss.step_for_bus([packet]).rd_data,0xfedc)
    def test_mmio_retirement_requires_ordered_successful_bus_response(self):
        iss=SocISS(dict(enumerate((0x0000a283).to_bytes(4,'little'))));iss.regs[1]=0x10000000
        with self.assertRaisesRegex(ValueError,'WITHOUT_RESPONSE'):iss.step_for_bus([])
        bad={'addr':0x10000004,'write':0,'be':15,'data':0,'read':0,'error':0}
        with self.assertRaisesRegex(ValueError,'REQUEST_ORDER'):iss.step_for_bus([bad])
    def test_uart_actual_bit_width_framing_and_truncation_rejected(self):
        bits=[0]+[(0x41>>b)&1 for b in range(8)]+[1]
        line=[1]*8+[b for bit in bits for b in [bit]*8]+[1]*8
        self.assertEqual(decode_uart(line,8),b'A')
        for bad in (line[:50],line[:20]+[1-line[20]]+line[21:]):
            with self.assertRaises(ValueError):decode_uart(bad,8)
    def test_trace_missing_and_malformed_cannot_pass(self):
        for text in ('','0 1\n'):
            with self.assertRaisesRegex(ValueError,'SHAPE'):check_trace(text,bytes(65536),{},8)
    def test_replayable_fabric_stimulus_and_accounting(self):
        text,a=fabric_vectors(1);self.assertEqual((text,a),fabric_vectors(1))
        other,b=fabric_vectors(20261107);self.assertNotEqual(text,other)
        self.assertGreater(a['ram_words'],250);self.assertGreater(a['canceled'][1],0)


if __name__=='__main__':unittest.main(verbosity=2)
