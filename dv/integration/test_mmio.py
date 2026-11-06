"""Independent bit-set GPIO and closed-form timer/transaction reference."""
import random
import unittest

GPIO=0x10000020
TIMER=0x10000100
MOD=2**32
LANES={(0,1),(0,3),(0,15),(1,2),(2,4),(2,12),(3,8)}


def merge(old,data,mask):
    return sum(((data if mask&(1<<b) else old)>>(8*b)&255)<<(8*b) for b in range(4))


class TimerClock:
    """Evaluate elapsed enabled cycles from an epoch; no cycle counter model."""
    def __init__(self):self.rebase(0,0,0,0)
    def rebase(self,edge,value,ctrl,compare):
        self.epoch=edge;self.base=value;self.ctrl=ctrl;self.compare=compare
    def distance(self):return (self.compare-self.base)%MOD or MOD
    def value(self,edge):
        elapsed=edge-self.epoch
        if not self.ctrl&1:return self.base
        assert elapsed>=0
        if self.ctrl&2 and elapsed>=self.distance():return (elapsed-self.distance())%(self.compare or MOD)
        return (self.base+elapsed)%MOD
    def event(self,edge):
        elapsed=edge-self.epoch
        if not self.ctrl&1 or elapsed<self.distance():return False
        return (elapsed-self.distance())%((self.compare or MOD) if self.ctrl&2 else MOD)==0


class Model:
    def __init__(self):
        self.n=0;self.clock=TimerClock();self.flag=0;self.bits=set();self.history=[0,0]
        self.pending=[None,None];self.requests=[0,0];self.replies=[0,0];self.errors=[0,0];self.canceled=[0,0]
        self.effects=[]
    def led(self):return sum(1<<bit for bit in self.bits)
    def decode(self,ch,packet):
        valid,addr,write,data,mask,ready=packet;word=addr&~3;value=0;op=None
        base=GPIO if ch==0 else TIMER
        error=(addr%4,mask) not in LANES or word not in {base+4*k for k in range(4)}
        if not error:
            index=(word-base)//4
            if ch==0:
                if index==1 and write:error=True
                elif write:op=(index,data,mask)
                elif index==0:value=self.led()
                elif index==1:value=self.history[0]
            else:
                if write:op=(index,data,mask)
                else:value=[self.clock.value(self.n-1),self.clock.compare,self.clock.ctrl,self.flag][index]
        return {'read':value,'error':int(error),'op':op}
    def view(self,reset):
        result=[]
        for ch,p in enumerate(self.pending):
            result.extend((int(not reset and p is None),int(not reset and p is not None),p['read'] if p is not None and not reset else 0,p['error'] if p is not None and not reset else 0))
            if ch==0:result.append(self.led())
        return tuple(result)
    def edge(self,reset,raw,g,t):
        pre=self.view(reset);accepted=[False,False];replies=[None,None];actions=[None,None];n=self.n
        if reset:
            for ch in range(2):
                if self.pending[ch] is not None:self.canceled[ch]+=1
            self.pending=[None,None];self.bits=set();self.history=[0,0];self.flag=0;self.clock.rebase(n,0,0,0)
        else:
            for ch,packet in enumerate((g,t)):
                valid,addr,write,data,mask,ready=packet;p=self.pending[ch]
                if p is not None:
                    if ready:
                        replies[ch]=p;actions[ch]=p['op'] if not p['error'] else None;self.replies[ch]+=1;self.errors[ch]+=p['error'];self.pending[ch]=None
                elif valid:
                    self.pending[ch]=self.decode(ch,packet);self.requests[ch]+=1;accepted[ch]=True
            self.history=[self.history[1],raw]
            if actions[0] is not None:
                index,data,mask=actions[0];selected={bit for bit in range(16) if mask&(1<<(bit//8))};ones={bit for bit in selected if data&(1<<bit)}
                before=self.led()
                if index==0:self.bits=(self.bits-selected)|ones
                elif index==2:self.bits|=ones
                elif index==3:self.bits-=ones
                self.effects.append({'cycle':n,'kind':'gpio-write','register':index,'mask':mask,'before':before,'after':self.led()})
            old_count=self.clock.value(n-1);normal=self.clock.value(n);event=self.clock.event(n)
            count_write=actions[1] is not None and actions[1][0]==0
            if actions[1] is not None:
                index,data,mask=actions[1]
                if index==3 and mask&1 and data&1:self.flag=0
                if index==0:
                    written=merge(old_count,data,mask);self.clock.rebase(n,written,self.clock.ctrl,self.clock.compare)
                elif index==1:self.clock.rebase(n,normal,self.clock.ctrl,merge(self.clock.compare,data,mask))
                elif index==2 and mask&1:self.clock.rebase(n,normal,data%4,self.clock.compare)
                self.effects.append({'cycle':n,'kind':'timer-write','register':index,'mask':mask,'before':old_count,'normal':normal,'after':self.clock.value(n),'would_match':int(event),'count_priority':int(count_write)})
            if event and not count_write:
                self.flag=1;self.effects.append({'cycle':n,'kind':'match','clear_collision':bool(actions[1] is not None and actions[1][0]==3 and actions[1][2]&1 and actions[1][1]&1)})
        post=self.view(reset);self.n+=1
        return (reset,raw,*g,*t,*pre,*post),accepted,replies


IDLE=(0,0,0,0,0,0)
class Agent:
    def __init__(self,seed):self.rng=random.Random(seed);self.m=Model();self.rows=[];self.cases=[];self.fixed_switches=None
    def mark(self,name):self.cases.append({'name':name,'cycle':self.m.n})
    def tick(self,reset=0,g=IDLE,t=IDLE):
        raw=self.rng.getrandbits(16) if self.fixed_switches is None else self.fixed_switches
        row,accepted,replies=self.m.edge(reset,raw,g,t);self.rows.append(row);return accepted,replies
    def idle(self,count):
        for _ in range(count):self.tick(g=(0,0,0,0,0,1),t=(0,0,0,0,0,1))
    def until(self,n):assert n>=self.m.n;self.idle(n-self.m.n)
    def transact(self,ch,addr,write=0,data=0,mask=15,stall=0,expect=None):
        packet=(1,addr,write,data,mask,0)
        accepted,_=self.tick(**{'g' if ch==0 else 't':packet});assert accepted[ch]
        for _ in range(stall):self.tick()
        _,replies=self.tick(**{'g' if ch==0 else 't':(0,0,0,0,0,1)});reply=replies[ch];assert reply is not None
        if expect is not None:assert (reply['error'],reply['read'])==expect,(ch,addr,reply,expect)
        return reply
    def configure(self,compare,count=0,ctrl=1):
        self.transact(1,TIMER+8,1,0,1);self.transact(1,TIMER,1,count)
        self.transact(1,TIMER+4,1,compare);self.transact(1,TIMER+12,1,1,1);self.transact(1,TIMER+8,1,ctrl,1)
    def next_match(self):
        return next(n for n in range(self.m.n,self.m.n+100) if self.m.clock.event(n))
    def match_collision(self,addr,data,mask=15):
        edge=self.next_match();self.until(edge-1);self.transact(1,addr,1,data,mask);assert self.m.n==edge+1


def corpus(seed):
    a=Agent(seed);m=a.m
    a.mark('reset-defaults');a.tick(reset=1);a.tick(reset=1);a.idle(3)
    for address in (GPIO,GPIO+8,GPIO+12):a.transact(0,address,expect=(0,0))
    for address in (TIMER,TIMER+4,TIMER+8,TIMER+12):a.transact(1,address,expect=(0,0))
    a.mark('gpio-all-bits-set-clear-idempotence')
    for bit in range(16):
        a.transact(0,GPIO,1,0);a.transact(0,GPIO+8,1,1<<bit);a.transact(0,GPIO+8,1,1<<bit)
        a.transact(0,GPIO,expect=(0,1<<bit));a.transact(0,GPIO+12,1,1<<bit);a.transact(0,GPIO,expect=(0,0))
    a.mark('all-natural-lanes-and-invalid-masks')
    for offset,mask in sorted(LANES):
        a.transact(0,GPIO+offset,1,a.rng.getrandbits(32),mask)
        for register in (TIMER,TIMER+4):a.transact(1,register+offset,1,a.rng.getrandbits(32),mask)
    for mask in range(16):
        if (0,mask) in LANES:continue
        a.transact(0,GPIO,1,0xffffffff,mask,expect=(1,0));a.transact(1,TIMER,1,0xffffffff,mask,expect=(1,0))
    a.mark('gpio-effects-wait-for-response-and-stable-input-snapshot');a.transact(0,GPIO,1,0x1234)
    accepted,_=a.tick(g=(1,GPIO,1,0xabcd,15,0));assert accepted[0]
    a.idle(0)
    for _ in range(24):a.tick();assert m.led()==0x1234
    a.tick(g=(0,0,0,0,0,1));assert m.led()==0xabcd
    a.fixed_switches=0xa55a;a.idle(4)
    accepted,_=a.tick(g=(1,GPIO+4,0,0,15,0));assert accepted[0]
    a.fixed_switches=0x5aa5
    for _ in range(16):a.tick()
    _,replies=a.tick(g=(0,0,0,0,0,1));assert replies[0]['read']==0xa55a
    a.transact(0,GPIO+4,expect=(0,0x5aa5));a.fixed_switches=None
    a.mark('reserved-high-lanes-and-readonly-unmapped-errors')
    old=m.led();a.transact(0,GPIO+2,1,0xffff0000,12);assert m.led()==old
    a.transact(1,TIMER+8,1,0,1);a.transact(1,TIMER+9,1,0xffffffff,2);a.transact(1,TIMER+8,expect=(0,0))
    for ch,addr in [(0,GPIO+4),(0,GPIO+16),(0,GPIO+0x10000),(1,TIMER+16),(1,TIMER+0x10000)]:a.transact(ch,addr,1,0xdeadbeef,expect=(1,0))
    a.mark('rollover-and-counter-snapshot-during-response-stall');a.configure(0,count=0xfffffff8)
    before=m.clock.value(m.n-1);a.transact(1,TIMER,stall=32,expect=(0,before));assert m.flag==1 and m.clock.value(m.n-1)<100
    a.transact(1,TIMER+12,1,1,1);assert m.flag==0
    a.mark('auto-reload-and-match-wins-status-clear');a.configure(1,ctrl=3)
    a.transact(1,TIMER+12,1,1,1);assert m.flag==1 and m.clock.value(m.n-1)==0
    a.transact(1,TIMER+12,expect=(0,1))
    a.transact(1,TIMER+13,1,0xffffffff,2);assert m.flag==1
    a.mark('single-match-wins-w1c');a.configure(9)
    a.match_collision(TIMER+12,1,1);a.transact(1,TIMER+12,expect=(0,1))
    a.mark('count-write-suppresses-increment-and-match');a.configure(13)
    a.match_collision(TIMER,0x42,1);assert m.clock.value(m.n-1)==0x42 and m.flag==0
    a.transact(1,TIMER+12,expect=(0,0))
    a.mark('compare-and-control-new-values-apply-next-edge');a.configure(12)
    a.match_collision(TIMER+4,19);assert m.flag==1 and m.clock.value(m.n-1)==12 and m.clock.compare==19
    a.configure(12);a.match_collision(TIMER+8,0,1);assert m.flag==1 and m.clock.value(m.n-1)==12 and m.clock.ctrl==0
    a.mark('partial-count-write-merges-pre-increment-value');a.configure(0,count=0x0000fffc)
    a.transact(1,TIMER+3,1,0x55000000,8);assert m.clock.value(m.n-1)==0x5500fffd
    a.mark('shared-reset-cancels-both-pending-effects')
    accepted,_=a.tick(g=(1,GPIO,1,0xffff,15,0),t=(1,TIMER,1,0xffffffff,15,0));assert all(accepted)
    a.tick(reset=1,g=(0,0,0,0,0,1),t=(0,0,0,0,0,1));a.idle(4)
    assert m.led()==0 and m.clock.value(m.n-1)==0 and m.clock.ctrl==0
    a.mark('no-response-consume-edge-replacement')
    a.tick(g=(1,GPIO,0,0,15,1),t=(1,TIMER,0,0,15,1))
    packets=[(1,GPIO+8,1,0x80,15,1),(1,TIMER+4,1,7,15,1)]
    accepted,replies=a.tick(g=packets[0],t=packets[1]);assert not any(accepted) and all(r is not None for r in replies)
    accepted,_=a.tick(g=packets[0],t=packets[1]);assert all(accepted);a.idle(2)
    a.mark('seeded-parallel-held-requests-and-errors');offered=[None,None]
    for cycle in range(4096):
        inputs=[]
        for ch in range(2):
            base=GPIO if ch==0 else TIMER
            if offered[ch] is None and a.rng.randrange(4)!=0:
                offset,mask=a.rng.choice(sorted(LANES));index=a.rng.randrange(5)
                offered[ch]=(1,base+4*index+offset,a.rng.randrange(2),a.rng.getrandbits(32),mask)
            inputs.append((offered[ch] or (0,0,0,0,0))+(int(a.rng.randrange(4)!=0),))
        accepted,_=a.tick(g=inputs[0],t=inputs[1])
        for ch in range(2):
            if accepted[ch]:offered[ch]=None
    a.mark('final-drain')
    for _ in range(12):
        inputs=[(offered[ch] or (0,0,0,0,0))+(1,) for ch in range(2)]
        accepted,_=a.tick(g=inputs[0],t=inputs[1])
        for ch in range(2):
            if accepted[ch]:offered[ch]=None
        if not any(offered) and not any(m.pending):break
    assert not any(offered) and not any(m.pending)
    assert all(m.requests[ch]==m.replies[ch]+m.canceled[ch] for ch in range(2))
    assert any(e['kind']=='timer-write' and e['would_match'] and e['count_priority'] for e in m.effects)
    assert any(e['kind']=='match' and e['clear_collision'] for e in m.effects)
    summary={'cycles':len(a.rows),'requests':m.requests,'replies':m.replies,'errors':m.errors,'canceled':m.canceled,'cases':a.cases,'effects':m.effects,
        'final_leds':m.led(),'final_count':m.clock.value(m.n-1),'final_compare':m.clock.compare,'final_ctrl':m.clock.ctrl,'final_flag':m.flag}
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in a.rows),summary


class MmioReferenceTests(unittest.TestCase):
    def test_closed_form_wrap_auto_and_zero_compare(self):
        c=TimerClock();c.rebase(7,0xfffffffe,1,0)
        self.assertEqual([c.value(n) for n in range(7,11)],[0xfffffffe,0xffffffff,0,1]);self.assertTrue(c.event(9))
        c.rebase(0,0,3,3);self.assertEqual([c.value(n) for n in range(8)],[0,1,2,0,1,2,0,1])
        self.assertEqual([n for n in range(8) if c.event(n)],[3,6]);c.rebase(0,0,3,0)
        self.assertFalse(c.event(0));self.assertEqual(c.value(MOD),0);self.assertTrue(c.event(MOD))
    def test_partial_merge(self):
        self.assertEqual(merge(0x11223344,0xaabbccdd,5),0x11bb33dd)
    def test_gpio_two_sample_snapshot_and_side_effect_commit(self):
        a=Agent(1);a.tick(reset=1);a.fixed_switches=0xffff;a.tick()
        a.transact(0,GPIO+4,expect=(0,0));a.transact(0,GPIO+4,expect=(0,0xffff))
        a.transact(0,GPIO,1,0x1234,stall=8);self.assertEqual(a.m.led(),0x1234)
    def test_priority_and_corpus_replay(self):
        text,summary=corpus(1);self.assertEqual((text,summary),corpus(1));self.assertNotEqual(text,corpus(20261106)[0])
        self.assertEqual(summary['canceled'],[1,1]);self.assertGreater(summary['cycles'],4000)
    def test_master_hold_until_acceptance(self):
        text,_=corpus(1);prior=None
        for line in text.splitlines():
            row=[int(v,16) for v in line.split()]
            if prior is not None and not row[0] and not prior[0]:
                for offset,ready_index in ((2,14),(8,19)):
                    if prior[offset] and not prior[ready_index]:self.assertEqual(row[offset:offset+5],prior[offset:offset+5])
            prior=row


if __name__=='__main__':unittest.main(verbosity=2)
