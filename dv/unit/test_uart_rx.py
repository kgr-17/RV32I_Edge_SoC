"""Independent absolute-time receiver and transaction-queue oracle.

Sampling deadlines are timestamps, not a duplicate RTL divider/FSM. The async
driver chooses intra-cycle phases; this model covers digital sampling, not MTBF.
"""
import random
import unittest
from test_uart import Serial, lanes_valid, BASE


class Receiver:
    def __init__(self,divider):
        if not 2<=divider<=65536:raise ValueError('Unsupported divisor')
        self.d=divider;self.history=[1,1];self.armed=False;self.start=None;self.samples={}
        self.valid=0;self.error=0;self.data=0;self.events=[];self.false_starts=0;self.aborts=0

    @property
    def busy(self):return int(self.start is not None)

    def edge(self,n,reset,enabled,line):
        observed=self.history[0];self.history=[self.history[1],line]
        self.valid=0;self.error=0
        if reset or not enabled:
            if self.start is not None:self.aborts+=1
            self.armed=False;self.start=None;self.samples={}
            if reset:self.history=[1,1];self.data=0
            return
        if self.start is None:
            if not self.armed:
                if observed:self.armed=True
            elif not observed:self.start=n;self.samples={}
            return
        elapsed=n-self.start;half=self.d//2
        if elapsed==half and observed:
            self.false_starts+=1;self.start=None;return
        for bit in range(8):
            if elapsed==half+(bit+1)*self.d:self.samples[bit]=observed
        if elapsed==half+9*self.d:
            assert len(self.samples)==8
            if observed:
                self.valid=1;self.data=sum(self.samples[b]<<b for b in range(8))
            else:self.error=1;self.armed=False
            self.events.append({'cycle':n,'byte':sum(self.samples[b]<<b for b in range(8)),'error':int(not observed)})
            self.start=None


class Model:
    def __init__(self,divider):
        self.d=divider;self.cycle=0;self.rx=Receiver(divider);self.direct=Receiver(divider);self.tx=Serial(divider)
        self.ctrl=3;self.head=None;self.over=0;self.frame=0;self.pending=None
        self.requests=0;self.replies=0;self.errors=0;self.canceled=0;self.effects=[]

    def decode(self,addr,write,data,mask):
        result=0;error=not lanes_valid(addr,mask);op=None
        if not error:
            word=addr//4*4
            if word==BASE:
                if write:
                    error=not bool(self.ctrl&2)
                    if not error and mask&1:op=('tx',data%256)
            elif word==BASE+4:
                error=bool(write)
                if not write:result=int(bool(self.ctrl&2) and not self.tx.busy(self.cycle-1))|int(self.head is not None)*2|self.over*4|self.frame*8
            elif word==BASE+8:
                error=bool(write)
                if not write:result=self.head if self.head is not None else 0;op=('pop',bool(mask&1 and self.head is not None))
            elif word==BASE+12:
                if write:op=('ctrl',data%4,bool(mask&1),(data>>8)&3 if mask&2 else 0)
                else:result=self.ctrl
            else:error=True
        return {'data':result,'error':int(error),'op':op}

    def view(self,inputs,post=False):
        reset,line,phase,valid,addr,write,data,mask,ready,pe=inputs
        instant=self.cycle if post else self.cycle-1;decoded=self.decode(addr,write,data,mask)
        blocked=decoded['op'] is not None and decoded['op'][0]=='tx' and self.tx.busy(instant)
        rq=int(not reset and self.pending is None and not blocked);rv=int(not reset and self.pending is not None)
        return (rq,rv,self.pending['data'] if rv else 0,self.pending['error'] if rv else 0,self.tx.line(instant),
                self.direct.valid,self.direct.data,self.direct.error,self.direct.busy)

    def step(self,inputs):
        reset,line,phase,valid,addr,write,data,mask,ready,pe=inputs
        pre=self.view(inputs);accepted=bool(valid and pre[0]);reply=None;pop=False;clear=0;send=False;byte=0
        enabled=bool(self.ctrl&1);tx_enabled=bool(self.ctrl&2);n=self.cycle
        if reset:
            if self.pending is not None:self.canceled+=1
            self.pending=None;self.ctrl=3;self.head=None;self.over=0;self.frame=0
        else:
            if self.pending is not None:
                if ready:
                    reply=self.pending;self.replies+=1;self.errors+=reply['error'];self.pending=None
                    op=reply['op']
                    if not reply['error'] and op is not None:
                        if op[0]=='tx':send=True;byte=op[1]
                        elif op[0]=='pop':pop=op[1]
                        elif op[0]=='ctrl':
                            if op[2]:self.ctrl=op[1]
                            clear=op[3]
            elif accepted:self.pending=self.decode(addr,write,data,mask);self.requests+=1
            old=self.head
            if pop:self.head=None
            if clear&1:self.over=0
            if clear&2:self.frame=0
            if self.rx.valid:
                if self.head is None:self.head=self.rx.data;kind='replace' if pop else 'fill'
                else:self.over=1;kind='overrun'
                self.effects.append({'cycle':n,'kind':kind,'byte':self.rx.data,'old':old,'clear':clear})
            if self.rx.error:
                self.frame=1;self.effects.append({'cycle':n,'kind':'frame-error','clear':clear})
            if pop:self.effects.append({'cycle':n,'kind':'pop','byte':old})
        self.tx.edge(n,reset,tx_enabled,send,byte)
        self.rx.edge(n,reset,enabled,line);self.direct.edge(n,reset,pe,line)
        post=self.view(inputs,post=True);self.cycle+=1
        return (*inputs,*pre,*post),accepted,reply


class Agent:
    def __init__(self,seed,divider):
        self.rng=random.Random(seed);self.m=Model(divider);self.d=divider;self.rows=[];self.cases=[]
        self.transitions={};self.line=1;self.wave_end=0;self.pe=1

    def mark(self,name):self.cases.append({'name':name,'cycle':self.m.cycle})

    def tick(self,reset=0,valid=0,addr=0,write=0,data=0,mask=0,ready=0):
        n=self.m.cycle;self.line=self.transitions.get(n,self.line)
        row,accepted,reply=self.m.step((reset,self.line,self.rng.randrange(4),valid,addr,write,data,mask,ready,self.pe))
        self.rows.append(row);return accepted,reply

    def idle(self,count):
        for _ in range(count):self.tick(ready=1)

    def until(self,cycle):
        assert cycle>=self.m.cycle,(cycle,self.m.cycle)
        self.idle(cycle-self.m.cycle)

    def schedule(self,byte,stop=1,bit_cycles=None,gap=4,break_cycles=0):
        width=self.d if bit_cycles is None else bit_cycles
        first=max(self.m.cycle+gap,self.wave_end);assert first>=self.m.cycle
        bits=[0]+[(byte>>b)&1 for b in range(8)]+[stop]
        for bit,value in enumerate(bits):self.transitions[first+bit*width]=value
        self.wave_end=first+10*width+break_cycles;self.transitions[self.wave_end]=1
        # Exact expected MMIO event edge for a clean full-rate frame: two sync
        # stages, half-bit start validation, stop center, one event register.
        return first+2+self.d//2+9*self.d+1,self.wave_end

    def transact(self,addr,write=0,data=0,mask=15,stall=0,expect=None):
        for _ in range(12*self.d+100):
            accepted,_=self.tick(valid=1,addr=addr,write=write,data=data,mask=mask)
            if accepted:break
        else:raise AssertionError('Request bound')
        for _ in range(stall):self.tick()
        _,reply=self.tick(ready=1);assert reply is not None
        if expect is not None:assert (reply['error'],reply['data'])==expect,(addr,reply,expect)
        return reply

    def receive(self,byte,stop=1,**kwargs):
        arrival,end=self.schedule(byte,stop,**kwargs);self.until(max(arrival+2,end+4));return arrival

    def collision(self,arrival,addr,write=0,data=0,mask=15):
        self.until(arrival-1);accepted,_=self.tick(valid=1,addr=addr,write=write,data=data,mask=mask)
        assert accepted;_,reply=self.tick(ready=1);assert reply is not None
        return reply


def corpus(seed,divider):
    a=Agent(seed,divider);m=a.m;d=divider
    a.mark('reset-defaults');a.tick(reset=1);a.tick(reset=1);a.idle(6)
    a.transact(BASE+4,expect=(0,1));a.transact(BASE+12,expect=(0,3));a.transact(BASE+8,expect=(0,0))
    a.mark('all-payloads' if d==8 else 'production-or-odd-divider')
    payloads=list(range(256)) if d==8 else [0,255,0x55,0xa5]
    a.rng.shuffle(payloads)
    for byte in payloads:
        a.receive(byte);a.transact(BASE+8,mask=1,expect=(0,byte));assert m.head is None
    a.mark('false-start');n=m.cycle+3;a.transitions[n]=0;a.transitions[n+1]=1
    before=len(m.rx.events);a.idle(3*d+8);assert len(m.rx.events)==before and m.rx.false_starts>=1
    a.mark('bad-stop-break-and-recovery');before=len(m.rx.events)
    a.receive(0x33,stop=0,break_cycles=12*d);assert len(m.rx.events)==before+1 and m.frame==1 and m.head is None
    a.transact(BASE+13,1,0x200,2);assert m.frame==0 and m.ctrl==3
    a.mark('overrun-retains-old-and-high-lane-does-not-pop')
    a.receive(0x21);a.receive(0x43);assert m.over==1 and m.head==0x21
    a.transact(BASE+9,mask=2,expect=(0,0x21));a.transact(BASE+10,mask=12,expect=(0,0x21));assert m.head==0x21
    a.transact(BASE+8,mask=1,expect=(0,0x21));a.transact(BASE+13,1,0x100,2);assert m.over==0
    a.mark('read-snapshot-held-while-new-frame-overruns');a.receive(0x32)
    arrival,end=a.schedule(0x64);a.transact(BASE+8,mask=1,stall=end-m.cycle+3,expect=(0,0x32))
    assert m.head is None and m.over==1;a.transact(BASE+13,1,0x100,2)
    a.mark('empty-read-cannot-consume-later-byte');arrival,end=a.schedule(0x73)
    a.transact(BASE+8,mask=1,stall=end-m.cycle+3,expect=(0,0));assert m.head==0x73
    a.transact(BASE+8,mask=1,expect=(0,0x73))
    a.mark('consume-and-receive-keeps-new');a.receive(0x41);arrival,end=a.schedule(0x82)
    reply=a.collision(arrival,BASE+8,mask=1);assert reply['data']==0x41 and m.head==0x82 and m.over==0
    a.until(end+4);a.transact(BASE+8,mask=1,expect=(0,0x82))
    a.mark('new-overrun-wins-w1c');a.receive(0x51);arrival,end=a.schedule(0xa2)
    a.collision(arrival,BASE+13,1,0x100,2);assert m.over==1 and m.head==0x51
    a.until(end+4);a.transact(BASE+8,mask=1,expect=(0,0x51))
    a.mark('new-frame-error-wins-w1c');arrival,end=a.schedule(0x93,stop=0)
    a.collision(arrival,BASE+13,1,0x200,2);assert m.frame==1 and m.head is None
    a.transact(BASE+4,expect=(0,13))
    a.until(end+8);a.transact(BASE+12,1,0x300,1);assert m.over==1 and m.frame==1 and m.ctrl==0
    a.transact(BASE+13,1,0x300,2);assert m.over==m.frame==0 and m.ctrl==0
    a.transact(BASE+12,1,3,1);a.idle(4)
    a.mark('disable-aborts-partial');arrival,end=a.schedule(0x5a)
    a.until(arrival-5*d);a.transact(BASE+12,1,2,1);a.until(end+5);assert m.head is None
    a.transact(BASE+12,1,3,1);a.idle(4)
    a.mark('completed-byte-survives-disable');arrival,end=a.schedule(0x96)
    a.collision(arrival,BASE+12,1,2,1);assert m.ctrl==2 and m.head==0x96
    a.until(end+4);a.transact(BASE+8,mask=1,expect=(0,0x96));a.transact(BASE+12,1,3,1);a.idle(4)
    a.mark('status-snapshot-and-partial-error-accesses');arrival,end=a.schedule(0x17)
    a.transact(BASE+4,stall=end-m.cycle+4,expect=(0,1));assert m.head==0x17
    for addr,mask,write in [(BASE+8,15,1),(BASE+4,15,1),(BASE+16,15,0),(BASE+8,5,0),(BASE+9,15,0)]:
        a.transact(addr,write,0xdeadbeef,mask,expect=(1,0));assert m.head==0x17
    a.mark('reset-cancels-pending-read');accepted,_=a.tick(valid=1,addr=BASE+8,mask=1);assert accepted
    a.tick(reset=1,ready=1);a.idle(5);assert m.head is None and m.ctrl==3
    a.mark('reset-in-start-data-stop')
    for offset in [1]+[(b+1)*d for b in range(9)]:
        arrival,end=a.schedule(0xa5);first=end-10*d
        a.until(first+2+offset)
        # A mid-frame reset aborts its partial sample. Keep reset asserted until
        # the sender returns idle: releasing it inside payload can present a
        # fresh apparent start, as with any asynchronous untagged byte stream.
        while m.cycle<end+5:a.tick(reset=1)
        a.idle(5);assert m.head is None
    a.mark('direct-disable-and-rearm');arrival,end=a.schedule(0x7e);a.until(arrival-4*d);a.pe=0
    a.until(end+3);a.pe=1;a.idle(5);a.transact(BASE+8,mask=1,expect=(0,0x7e))
    a.mark('baud-skew-and-async-phase')
    if d==868:
        for width in (860,876):
            a.receive(0xa5,bit_cycles=width);a.transact(BASE+8,mask=1,expect=(0,0xa5))
    a.mark('seeded-full-duplex')
    for _ in range(24 if d==8 else 6):
        byte=a.rng.randrange(256);bad=a.rng.randrange(5)==0
        arrival,end=a.schedule(byte,stop=int(not bad))
        a.transact(BASE,1,a.rng.randrange(256),1,stall=a.rng.randrange(4))
        a.until(max(end+5,m.cycle));a.transact(BASE+4,stall=a.rng.randrange(4))
        if a.rng.randrange(3):a.transact(BASE+8,mask=1)
        if a.rng.randrange(2):a.transact(BASE+13,1,0x300,2)
    a.mark('final-drain');a.idle(12*d+8)
    if m.head is not None:a.transact(BASE+8,mask=1)
    a.transact(BASE+13,1,0x300,2);a.transact(BASE+12,expect=(0,3))
    assert m.pending is None and m.requests==m.replies+m.canceled
    good={event['byte'] for event in m.rx.events if not event['error']}
    if d==8:assert good==set(range(256))
    kinds={event['kind'] for event in m.effects};assert {'fill','replace','overrun','frame-error','pop'}<=kinds
    assert any(e['kind']=='overrun' and e['clear']&1 for e in m.effects)
    assert any(e['kind']=='frame-error' and e['clear']&2 for e in m.effects)
    summary={'divider':d,'cycles':len(a.rows),'requests':m.requests,'replies':m.replies,'errors':m.errors,'canceled':m.canceled,
        'cases':a.cases,'rx_events':m.rx.events,'direct_events':m.direct.events,'effects':m.effects,'tx_frames':m.tx.events,
        'completed_rx_bytes':sorted(good),'false_starts':m.rx.false_starts,'partial_aborts':m.rx.aborts,'phases':sorted({r[2] for r in a.rows})}
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in a.rows),summary


class ReceiverTests(unittest.TestCase):
    def test_manual_a5_centers_and_two_stage_delay(self):
        r=Receiver(8);r.edge(0,True,True,1)
        bits=[0,1,0,1,0,0,1,0,1,1];pulses=[]
        for n in range(1,100):
            raw=1 if n<5 or n>=85 else bits[(n-5)//8]
            r.edge(n,False,True,raw)
            if r.valid:pulses.append((n,r.data))
        self.assertEqual(pulses,[(83,0xa5)]);self.assertFalse(r.error)

    def test_break_one_error_until_high(self):
        r=Receiver(8)
        for n in range(200):r.edge(n,n==0,True,int(n<5))
        self.assertEqual(len(r.events),1);self.assertEqual(r.events[0]['error'],1);self.assertFalse(r.busy)

    def test_event_wins_clear_and_consume_keeps_new(self):
        m=Model(8);m.head=0x11;m.over=1;m.frame=1;m.rx.valid=1;m.rx.data=0x22
        m.pending={'data':0x11,'error':0,'op':('pop',True)}
        m.step((0,1,0,0,0,0,0,0,1,1));self.assertEqual(m.head,0x22)
        m.pending={'data':0,'error':0,'op':('ctrl',3,False,3)};m.rx.valid=1;m.rx.error=1;m.rx.data=0x33
        m.step((0,1,0,0,0,0,0,0,1,1));self.assertEqual((m.head,m.over,m.frame),(0x22,1,1))

    def test_empty_snapshot_cannot_pop_future_head(self):
        a=Agent(1,8);a.tick(reset=1);a.idle(5);end=a.schedule(0x61)[1]
        a.transact(BASE+8,mask=1,stall=end-a.m.cycle+4,expect=(0,0));self.assertEqual(a.m.head,0x61)

    def test_replay_all_bytes_and_seed_difference(self):
        text,summary=corpus(1,8);self.assertEqual((text,summary),corpus(1,8))
        self.assertNotEqual(text,corpus(20261106,8)[0]);self.assertEqual(summary['completed_rx_bytes'],list(range(256)))

    def test_production_odd_bounds_and_producer_stability(self):
        for d in (7,868):
            text,summary=corpus(1,d);self.assertGreater(summary['false_starts'],0);prior=None
            for line in text.splitlines():
                row=[int(v,16) for v in line.split()]
                if prior is not None and not row[0] and not prior[0] and prior[3] and not prior[10]:
                    self.assertEqual((row[3],row[4:8]),(1,prior[4:8]))
                prior=row
        for d in (0,1,65537):
            with self.assertRaises(ValueError):Receiver(d)


if __name__=='__main__':unittest.main(verbosity=2)
