"""History/deadline oracle for asynchronous reset and scalar/word synchronizers."""
import random
import unittest


def vectors(seed):
    rng=random.Random(seed)
    stimuli=[(1,0,0,0xffffffff,1)]+[(0,0,n%4,0xa55aff00+n,n%2) for n in range(8)]
    for bit in range(32):stimuli.extend([(0,0,bit%4,1<<bit,bit%2),(0,0,(bit+1)%4,0xffffffff^(1<<bit),1-bit%2)])
    for phase in range(4):
        stimuli += [(0,1,phase,0xffffffff,1)]+[(0,0,phase,0x5aa50000+n,n%2) for n in range(6)]
    for n in range(1536):stimuli.append((int(n%97<3),int(n%47==13 and n%97>=3),rng.randrange(4),rng.getrandbits(32),rng.randrange(2)))
    stimuli += [(0,0,n%4,0,n%2) for n in range(8)]
    return expected(stimuli)


def expected(stimuli):
    if not stimuli or not stimuli[0][0]:raise ValueError('Start with reset')
    since_assert=2;visible=(0,0,0);samples=[];rows=[];resets=pulses=0
    for n,(held,pulse,phase,data,bit) in enumerate(stimuli):
        assert held in (0,1) and pulse in (0,1) and bit in (0,1) and phase in range(4) and 0<=data<2**32
        if held or pulse:since_assert=0;resets+=int(bool(held));pulses+=int(bool(pulse))
        pre_reset=int(since_assert<2)
        pre=(pre_reset,*visible)
        if pre_reset:samples=[];visible=(0,0,0)
        else:
            samples.append((data,bit))
            visible=(samples[-2][0]&65535,samples[-2][0],samples[-2][1]) if len(samples)>=2 else (0,0,0)
        if not held:since_assert+=1
        post=(int(since_assert<2),*visible)
        rows.append((held,pulse,phase,data,bit,*pre,*post))
    summary={'cycles':len(rows),'held_reset_edges':resets,'subcycle_pulses':pulses,'phases':sorted({r[2] for r in rows}),
        'one_hot_bits':sorted({r[3].bit_length()-1 for r in rows if r[3] and r[3]&(r[3]-1)==0}),
        'checks':['INIT-before-clock','async-assert-clock-stopped','release-needs-clock','two-edge-release','synchronous-downstream-reset','input-width1-16-32','short-pulses','phases0-3','all32-onehot','seeded-replay']}
    return ''.join(' '.join('%x'%v for v in row)+'\n' for row in rows),summary


class CdcReferenceTests(unittest.TestCase):
    def test_manual_release_and_downstream_samples(self):
        text,_=expected([(1,0,0,9,1),(0,0,0,8,1),(0,0,0,7,1),(0,0,0,6,0),(0,0,0,5,1)])
        rows=[[int(v,16) for v in line.split()] for line in text.splitlines()]
        self.assertEqual([row[9] for row in rows],[1,1,0,0,0])
        self.assertEqual([row[11] for row in rows],[0,0,0,0,6])
        self.assertEqual(rows[2][5],1);self.assertEqual(rows[3][5],0)
    def test_short_pulse_restarts_two_edge_barrier(self):
        text,_=expected([(1,0,0,1,1)]+[(0,0,0,2,0)]*4+[(0,1,3,3,1),(0,0,1,4,1),(0,0,0,5,0)])
        rows=[[int(v,16) for v in line.split()] for line in text.splitlines()]
        self.assertEqual([row[9] for row in rows[5:]],[1,0,0]);self.assertEqual(rows[5][5],1)
    def test_replay_complete_patterns(self):
        text,summary=vectors(1);self.assertEqual((text,summary),vectors(1));self.assertNotEqual(text,vectors(20261106)[0])
        self.assertEqual(summary['one_hot_bits'],list(range(32)));self.assertEqual(summary['phases'],[0,1,2,3]);self.assertGreater(summary['subcycle_pulses'],30)


if __name__=='__main__':unittest.main(verbosity=2)
