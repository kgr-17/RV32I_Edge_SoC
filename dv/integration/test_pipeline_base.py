#!/usr/bin/env python3
"""Independent stage-event ledger; opaque 129-bit tagged payloads, not ISA decode."""
from collections import Counter
import random
import unittest

WIDTH = 129
MASK = 2**WIDTH-1
REQUIRED_BINS = ['stage:%d:%s' % (stage, action) for stage in range(5)
                 for action in ('reset','clear','hold_valid','hold_bubble','capture','bubble','clear_over_hold')]
REQUIRED_BINS += ['wb_drain_front_held','between_edge_reset','all_valid','all_bubble']


class Ledger:
    def __init__(self):
        self.history = [[] for _ in range(5)]

    def snapshot(self):
        # Last architectural storage event wins. Hold deliberately adds no
        # event; clear/reset/bubble are tombstones, capture is an opaque token.
        values = [events[-1] if events else None for events in self.history]
        return sum(2**stage for stage, value in enumerate(values) if value is not None), [value or 0 for value in values]

    def step(self, reset, clear, hold, valid, data):
        for stage, events in enumerate(self.history):
            if reset or clear & 2**stage:
                events.append(None)
            elif not hold & 2**stage:
                events.append(data[stage] if valid & 2**stage else None)
        return self.snapshot()


def generate(seed):
    rng = random.Random(seed)
    ledger, coverage, rows = Ledger(), Counter(), []
    def add(reset=0, clear=0, hold=0, valid=31, data=None, pulse=0, group='directed'):
        data = data if data is not None else [rng.getrandbits(WIDTH) for _ in range(5)]
        before = ledger.snapshot()
        if reset: before = 0, [0]*5
        previous_valid = ledger.snapshot()[0]
        after = ledger.step(reset,clear,hold,valid,data)
        if reset: after = 0, [0]*5
        rows.append((reset,clear,hold,valid,pulse,*data,before[0],after[0],*before[1],*after[1]))
        coverage['group:'+group] += 1
        for stage in range(5):
            bit = 2**stage
            action = 'reset' if reset else 'clear' if clear&bit else (
                ('hold_valid' if previous_valid&bit else 'hold_bubble') if hold&bit else ('capture' if valid&bit else 'bubble'))
            coverage['stage:%d:%s'%(stage,action)] += 1
            if not reset and clear&bit and hold&bit: coverage['stage:%d:clear_over_hold'%stage] += 1
        if clear == 16 and hold == 15 and previous_valid == 31: coverage['wb_drain_front_held'] += 1
        if pulse: coverage['between_edge_reset'] += 1
        coverage['all_valid' if after[0]==31 else 'all_bubble' if after[0]==0 else 'mixed_valid'] += 1
    add(reset=1,clear=31,hold=31,group='reset')
    add(data=[0,1,2,3,MASK])
    add(clear=16,hold=15)
    for clear in range(32):
        for hold in range(32):
            for valid in range(32): add(clear=clear,hold=hold,valid=valid,group='control-cross')
    for stage in range(5):
        for bit in range(WIDTH):
            for value in (2**bit,MASK^2**bit):
                data=[0]*5;data[stage]=value
                add(valid=2**stage,data=data,group='walking-payload')
                add(hold=2**stage,valid=0,data=[MASK]*5,group='hold-walking')
    for controls in range(32):
        add(reset=1,clear=controls,hold=31-controls,group='reset-cross')
        add(valid=controls,pulse=1,group='pulse-reset')
    for _ in range(4096):
        add(reset=int(rng.randrange(32)==0),clear=rng.randrange(32),hold=rng.randrange(32),valid=rng.randrange(32),group='random')
    assert all(coverage[key] > 0 for key in REQUIRED_BINS), coverage
    return ''.join(' '.join('%x'%value for value in row)+'\n' for row in rows),dict(sorted(coverage.items()))


class StageLedgerTests(unittest.TestCase):
    def test_capture_hold_and_clear_have_distinct_events(self):
        model=Ledger()
        self.assertEqual(model.step(0,0,0,31,[1,2,3,4,5]),(31,[1,2,3,4,5]))
        self.assertEqual(model.step(0,16,15,31,[9]*5),(15,[1,2,3,4,0]))
        self.assertEqual([len(events) for events in model.history],[1,1,1,1,2])

    def test_invalid_input_cannot_retain_metadata(self):
        model=Ledger();model.step(0,0,0,31,[MASK]*5)
        self.assertEqual(model.step(0,0,0,0,[MASK]*5),(0,[0]*5))

    def test_reset_dominates_every_local_control(self):
        model=Ledger();model.step(0,0,0,31,[MASK]*5)
        self.assertEqual(model.step(1,31,31,31,[MASK]*5),(0,[0]*5))

    def test_each_stage_is_independent_and_zero_is_valid_data(self):
        for stage in range(5):
            model=Ledger()
            self.assertEqual(model.step(0,0,0,2**stage,[0]*5),(2**stage,[0]*5))


if __name__=='__main__': unittest.main(verbosity=2)
