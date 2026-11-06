"""Independent timestamp-based UART/transaction model, stimulus and policy tests."""
import random
import unittest

BASE=0x10000000


class Serial:
    def __init__(self,divider):
        if not 2<=divider<=65536:raise ValueError('Unsupported divisor')
        self.divider=divider;self.live=None;self.events=[]

    def busy(self,cycle):
        return self.live is not None and 0<=cycle-self.live[0]<10*self.divider

    def line(self,cycle):
        if not self.busy(cycle):return 1
        bit=(cycle-self.live[0])//self.divider
        return 0 if bit==0 else 1 if bit==9 else (self.live[1]>>(bit-1))&1

    def edge(self,cycle,reset,enabled,send,byte):
        accepted=False
        if reset:
            if self.live and cycle-self.live[0]<10*self.divider:self.events[-1]['aborted']=True
            self.live=None
        elif send and enabled and not self.busy(cycle-1):
            self.live=(cycle,byte);self.events.append({'cycle':cycle,'byte':byte,'aborted':False});accepted=True
        return accepted

    def completed_bytes(self,cycle):
        return {e['byte'] for e in self.events if not e['aborted'] and cycle-e['cycle']>=10*self.divider}


def lanes_valid(addr,mask):
    return mask in {0:{1,3,15},1:{2},2:{4,12},3:{8}}[addr%4]


class Model:
    def __init__(self,divider):
        self.serial=Serial(divider);self.phy=Serial(divider);self.cycle=0
        self.ctrl=3;self.pending=None;self.requests=0;self.replies=0;self.errors=0;self.canceled=0

    def decode(self,addr,write,data,mask):
        error=not lanes_valid(addr,mask);op=None;result=0
        word=addr//4*4
        if not error:
            if word==BASE:
                if write:
                    error=not bool(self.ctrl&2)
                    if not error and mask&1:op=('tx',data%256)
            elif word==BASE+4:
                error=bool(write)
                if not write:result=int(bool(self.ctrl&2) and not self.serial.busy(self.cycle-1))
            elif word==BASE+8:error=bool(write) # Empty RX until T042.
            elif word==BASE+12:
                if write:op=('ctrl',data%4,bool(mask&1))
                else:result=self.ctrl
            else:error=True
        return dict(error=int(error),data=result,op=op)

    def view(self,inputs,post=False):
        reset,valid,addr,write,data,mask,ready,pe,pv,pdata=inputs
        instant=self.cycle if post else self.cycle-1
        decoded=self.decode(addr,write,data,mask)
        can_tx=not self.serial.busy(instant) and bool(self.ctrl&2)
        blocked=decoded['op'] is not None and decoded['op'][0]=='tx' and not can_tx
        rq=int(not reset and self.pending is None and not blocked)
        rv=int(not reset and self.pending is not None)
        rd=self.pending['data'] if rv else 0;err=self.pending['error'] if rv else 0
        return (rq,rv,rd,err,self.serial.line(instant),int(not reset and pe and not self.phy.busy(instant)),int(self.phy.busy(instant)),self.phy.line(instant))

    def step(self,inputs):
        reset,valid,addr,write,data,mask,ready,pe,pv,pdata=inputs
        pre=self.view(inputs);accepted=bool(valid and pre[0]);reply=None;send=False;byte=0;old_enable=bool(self.ctrl&2)
        if reset:
            if self.pending is not None:self.canceled+=1
            self.pending=None;self.ctrl=3
        elif self.pending is not None:
            if ready:
                reply=self.pending;self.replies+=1;self.errors+=reply['error']
                if not reply['error'] and reply['op'] is not None:
                    if reply['op'][0]=='tx':send=True;byte=reply['op'][1]
                    elif reply['op'][2]:self.ctrl=reply['op'][1]
                self.pending=None
        elif accepted:
            self.pending=self.decode(addr,write,data,mask);self.requests+=1
        if send and not (old_enable and not self.serial.busy(self.cycle-1)):
            raise AssertionError('TX commit without ready')
        self.serial.edge(self.cycle,reset,old_enable,send,byte)
        phy_accept=self.phy.edge(self.cycle,reset,pe,pv,pdata)
        post=self.view(inputs,post=True)
        row=(*inputs,*pre,*post);self.cycle+=1
        return row,accepted,reply,phy_accept


class Agent:
    def __init__(self,seed,divider):
        self.rng=random.Random(seed);self.model=Model(divider);self.rows=[];self.cases=[]
        self.phy_byte=0;self.phy_enabled=True;self.phy_stop_requested=False;self.divider=divider

    def mark(self,name):self.cases.append({'name':name,'cycle':self.model.cycle})

    def tick(self,reset=0,valid=0,addr=0,write=0,data=0,mask=0,ready=0):
        n=self.model.cycle
        # A legal held-valid PHY producer; next payload changes only after an
        # acceptance. Disable once during live traffic, without canceling it.
        pe=int(not 50*self.divider<=n<70*self.divider)
        inputs=(reset,valid,addr,write,data,mask,ready,pe,int(self.phy_enabled),self.phy_byte)
        row,accepted,reply,phy_accepted=self.model.step(inputs);self.rows.append(row)
        if phy_accepted:
            self.phy_byte=(self.phy_byte+1)%256
            if self.phy_stop_requested:self.phy_enabled=False
        return accepted,reply

    def idle(self,count):
        for _ in range(count):self.tick(ready=1)

    def transact(self,addr,write=0,data=0,mask=15,stall=0,accept_ready=0,expect=None):
        for _ in range(12*self.divider+100):
            accepted,_=self.tick(valid=1,addr=addr,write=write,data=data,mask=mask,ready=accept_ready)
            if accepted:break
        else:raise AssertionError('Bounded request acceptance failed')
        for _ in range(stall):self.tick()
        for _ in range(4):
            _,reply=self.tick(ready=1)
            if reply is not None:
                if expect is not None:assert (reply['error'],reply['data'])==expect,(addr,reply,expect)
                return reply
        raise AssertionError('Bounded response failed')


def corpus(seed,divider):
    a=Agent(seed,divider);d=divider
    a.mark('reset-and-register-defaults');a.tick(reset=1);a.tick(reset=1);a.idle(2)
    a.transact(BASE+12,expect=(0,3),accept_ready=1)
    a.transact(BASE+4,expect=(0,1));a.transact(BASE+8,expect=(0,0))
    a.mark('all-payloads' if d==4 else 'production-divider')
    for byte in (list(range(256)) if d==4 else [0,255,0x55,0xa5]):
        a.transact(BASE,1,byte,1,stall=a.rng.randrange(4))
    a.idle(11*d)
    a.mark('effect-after-stalled-response');before=len(a.model.serial.events)
    accepted,_=a.tick(valid=1,addr=BASE,write=1,data=0x96,mask=1);assert accepted
    for _ in range(12*d):a.tick()
    assert len(a.model.serial.events)==before
    a.tick(ready=1);assert len(a.model.serial.events)==before+1
    a.mark('status-snapshot-across-frame-finish')
    a.transact(BASE+4,stall=12*d,expect=(0,0));a.transact(BASE+4,expect=(0,1))
    a.mark('disable-active-frame')
    a.transact(BASE,1,0x5a,1);a.transact(BASE+12,1,0,1)
    a.transact(BASE,1,0x33,1,expect=(1,0));a.transact(BASE+1,1,0x5500,2,expect=(1,0))
    a.idle(11*d);a.transact(BASE+4,expect=(0,0));a.transact(BASE+12,1,3,1)
    a.mark('lanes-reserved-readonly-and-unmapped')
    a.transact(BASE+12,1,2,1);a.transact(BASE+13,1,0xffff0300,2);a.transact(BASE+12,expect=(0,2))
    a.transact(BASE+12,1,0xffffffff,15);a.transact(BASE+12,expect=(0,3))
    before=len(a.model.serial.events);a.transact(BASE+1,1,0x7e00,2);assert len(a.model.serial.events)==before
    a.transact(BASE+1,mask=2,expect=(0,0))
    for offset in (4,8,16,28,32):a.transact(BASE+offset,1,0x12345678,15,expect=(1,0))
    for offset in (16,28,32):a.transact(BASE+offset,expect=(1,0))
    for addr,mask in [(BASE,0),(BASE,5),(BASE,10),(BASE,2),(BASE+1,15),(BASE+2,3)]:
        a.transact(addr,1,0xabcdef01,mask,expect=(1,0))
    a.mark('no-consume-edge-replacement')
    accepted,_=a.tick(valid=1,addr=BASE+8,mask=15,ready=1);assert accepted
    accepted,reply=a.tick(valid=1,addr=BASE,write=1,data=0xc3,mask=1,ready=1)
    assert not accepted and reply is not None
    accepted,_=a.tick(valid=1,addr=BASE,write=1,data=0xc3,mask=1,ready=1);assert accepted
    a.tick(ready=1);a.idle(11*d)
    a.mark('reset-cancels-pending-tx');before=len(a.model.serial.events)
    accepted,_=a.tick(valid=1,addr=BASE,write=1,data=0x69,mask=1);assert accepted
    a.idle(0);a.tick(reset=1,ready=1);a.idle(2);assert len(a.model.serial.events)==before
    a.mark('reset-active-and-offered-traffic')
    a.transact(BASE,1,0x00,1)
    for _ in range(2):
        accepted,_=a.tick(valid=1,addr=BASE,write=1,data=0xff,mask=1);assert not accepted
    a.tick(reset=1,valid=1,addr=BASE,write=1,data=0xff,mask=1,ready=1);a.idle(2)
    a.transact(BASE+12,expect=(0,3))
    a.mark('seeded-transactions')
    for _ in range(64 if d==4 else 12):
        choice=a.rng.randrange(6)
        if choice==0:a.transact(BASE,1,a.rng.randrange(256),1,stall=a.rng.randrange(5))
        elif choice==1:a.transact(BASE+4,stall=a.rng.randrange(5))
        elif choice==2:a.transact(BASE+12,1,a.rng.randrange(4),1)
        elif choice==3:a.transact(BASE+8,expect=(0,0))
        elif choice==4:a.transact(BASE+16,1,a.rng.getrandbits(32),15,expect=(1,0))
        else:a.transact(BASE+13,1,a.rng.getrandbits(32),2)
    a.transact(BASE+12,1,3,1);a.transact(BASE,1,0xa5,1)
    # Finish an already offered PHY transfer before withdrawing valid, then
    # allow the last accepted frame to complete too.
    a.mark('final-drain');a.phy_stop_requested=True;a.idle(22*d+4)
    assert a.model.pending is None and a.model.requests==a.model.replies+a.model.canceled
    if d==4:
        assert a.model.serial.completed_bytes(a.model.cycle)==set(range(256))
        assert a.model.phy.completed_bytes(a.model.cycle)==set(range(256))
    summary={'divider':d,'cycles':len(a.rows),'requests':a.model.requests,'replies':a.model.replies,'errors':a.model.errors,'canceled':a.model.canceled,
        'mmio_frames':a.model.serial.events,'phy_frames':a.model.phy.events,'mmio_completed_bytes':sorted(a.model.serial.completed_bytes(a.model.cycle)),
        'phy_completed_bytes':sorted(a.model.phy.completed_bytes(a.model.cycle)),'cases':a.cases}
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in a.rows),summary


class UartReferenceTests(unittest.TestCase):
    def test_manual_lsb_first_8n1_frame(self):
        s=Serial(4);self.assertTrue(s.edge(5,False,True,True,0xa5))
        expected=[0,1,0,1,0,0,1,0,1,1]
        self.assertEqual([s.line(5+4*i) for i in range(10)],expected)
        self.assertTrue(s.busy(44));self.assertFalse(s.busy(45));self.assertEqual(s.line(45),1)

    def test_disable_does_not_cancel_frame_and_reset_does(self):
        s=Serial(4);s.edge(0,False,True,True,0)
        for n in range(1,20):s.edge(n,False,False,True,255)
        self.assertEqual(len(s.events),1);self.assertTrue(s.busy(19));self.assertEqual(s.line(19),0)
        s.edge(20,True,False,True,255);self.assertFalse(s.busy(20));self.assertEqual(s.line(20),1);self.assertTrue(s.events[0]['aborted'])

    def test_no_zero_latency_response_and_no_replacement(self):
        a=Agent(1,4);a.tick(reset=1)
        accepted,reply=a.tick(valid=1,addr=BASE+12,mask=15,ready=1)
        self.assertTrue(accepted);self.assertIsNone(reply);self.assertEqual(a.rows[-1][11],0);self.assertEqual(a.rows[-1][19],1)
        accepted,reply=a.tick(valid=1,addr=BASE,write=1,data=7,mask=1,ready=1)
        self.assertFalse(accepted);self.assertEqual(reply['data'],3)

    def test_tx_effect_waits_for_response(self):
        a=Agent(1,4);a.tick(reset=1);a.tick(valid=1,addr=BASE,write=1,data=0x55,mask=1)
        for _ in range(50):a.tick()
        self.assertFalse(a.model.serial.events);a.tick(ready=1);self.assertEqual(len(a.model.serial.events),1)
        for _ in range(10):a.tick(ready=1)
        self.assertEqual(len(a.model.serial.events),1)

    def test_byte_lanes_and_disabled_error(self):
        a=Agent(1,4);a.tick(reset=1);a.transact(BASE+13,1,0,2);self.assertEqual(a.model.ctrl,3)
        a.transact(BASE+12,1,0,1);a.transact(BASE,1,7,1,expect=(1,0));a.transact(BASE+12,expect=(0,0))
        for addr,mask in [(BASE,0),(BASE,2),(BASE+1,15)]:a.transact(addr,1,7,mask,expect=(1,0))
        self.assertFalse(a.model.serial.events)

    def test_reset_cancels_response_and_sticky_old_data(self):
        a=Agent(1,4);a.tick(reset=1);a.tick(valid=1,addr=BASE+12,mask=15);a.tick(reset=1,ready=1)
        self.assertIsNone(a.model.pending);self.assertEqual(a.model.canceled,1);self.assertEqual(a.rows[-1][19:22],(0,0,0))

    def test_complete_fast_corpus_seed_replay(self):
        text,report=corpus(1,4);self.assertEqual((text,report),corpus(1,4))
        self.assertNotEqual(text,corpus(20261106,4)[0]);self.assertEqual(len(report['mmio_completed_bytes']),256)
        self.assertEqual(len(report['phy_completed_bytes']),256);self.assertGreater(report['cycles'],10000)

    def test_production_divisor_and_bounds(self):
        self.assertLess(abs(100000000/868-115200)/115200,0.0001)
        for divisor in (0,1,65537):
            with self.assertRaises(ValueError):Serial(divisor)

    def test_peer_valid_and_payload_hold_until_acceptance(self):
        for divider in (4,868):
            text,_=corpus(1,divider);prior=None
            for line in text.splitlines():
                row=[int(word,16) for word in line.split()]
                if prior is not None and not row[0]:
                    if prior[8] and not prior[15] and not prior[0]:
                        self.assertEqual((row[8],row[9]),(1,prior[9]))
                    if prior[1] and not prior[10] and not prior[0]:
                        self.assertEqual((row[1],row[2:6]),(1,prior[2:6]))
                prior=row


if __name__=='__main__':unittest.main(verbosity=2)
