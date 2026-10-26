#!/usr/bin/env python3
"""Register-file reference from event history, not a copy of the RTL storage array."""
from collections import Counter
import random
import unittest

MASK = (1 << 32) - 1
REQUIRED_BINS = ['reset', 'reset-over-write', 'x0-write', 'bypass-a', 'bypass-b',
                 'bypass-both', 'write-disabled', 'reset-pulse', 'held-reset']
REQUIRED_BINS += ['read-%s:%d' % (port, addr) for port in ('a', 'b') for addr in range(32)]


def committed(history, addr):
    if addr == 0:
        return 0
    for reset, enable, target, value in reversed(history):
        if reset:
            return 0
        if enable and target == addr:
            return value
    raise AssertionError('Undefined initial register read: apply reset first')


def before_edge(history, reset, enable, target, value, addr):
    if reset or addr == 0:
        return 0
    if enable and target == addr:
        return value
    return committed(history, addr)


def generate(seed):
    rng = random.Random(seed)
    history, rows, coverage = [], [], Counter()

    def add(reset=0, enable=0, target=0, value=0, a=0, b=0, pulse=0):
        if pulse and reset:
            raise AssertionError('Pulse test starts with reset low')
        pre = [before_edge(history, reset, enable, target, value, addr) for addr in (a, b)]
        history.append((reset, enable, target, value))
        post = [committed(history, addr) for addr in (a, b)]
        rows.append((reset, enable, target, value, a, b, pulse, *pre, *post))
        coverage['read-a:' + str(a)] += 1; coverage['read-b:' + str(b)] += 1
        if reset: coverage['reset'] += 1
        if reset and enable: coverage['reset-over-write'] += 1
        if len(history) > 1 and reset and history[-2][0]: coverage['held-reset'] += 1
        if enable and target == 0: coverage['x0-write'] += 1
        if not enable: coverage['write-disabled'] += 1
        if pulse: coverage['reset-pulse'] += 1
        if not reset and enable and target != 0:
            if target == a: coverage['bypass-a'] += 1
            if target == b: coverage['bypass-b'] += 1
            if target == a == b: coverage['bypass-both'] += 1

    add(reset=1, enable=1, target=1, value=MASK, a=1, b=31)
    add(reset=1, enable=1, target=31, value=MASK, a=31, b=0)
    for reg in range(32): add(a=reg, b=31-reg)
    # Unique full-width values in every register, then exhaustive read pairs.
    for reg in range(1, 32):
        add(enable=1, target=reg, value=(0x9e3779b9 * reg) & MASK, a=reg, b=reg)
    for a in range(32):
        for b in range(32): add(a=a, b=b)
    # A pulse between clock edges must mask reads temporarily but not erase state.
    for reg in range(1,32): add(a=reg, b=32-reg, pulse=1)
    for target in range(32):
        for a in range(32):
            add(enable=1, target=target, value=rng.getrandbits(32), a=a, b=31-a)
        add(enable=1, target=target, value=rng.getrandbits(32), a=target, b=target)
        add(enable=0, target=target, value=MASK, a=target, b=target)
    # Walking bits and complements on all stored words; disabled writes hold.
    for reg in range(1,32):
        for bit in range(32):
            for value in (1 << bit, MASK ^ (1 << bit)):
                add(enable=1, target=reg, value=value, a=reg, b=0)
                add(target=reg, value=value ^ MASK, a=0, b=reg)
    for _ in range(64): add(enable=1, value=rng.getrandbits(32), a=0, b=rng.randrange(32))
    add(reset=1, enable=1, target=31, value=MASK, a=31, b=1)
    for reg in range(32): add(a=reg, b=31-reg)
    for index in range(4096):
        target = 0 if index % 4 == 0 else rng.randrange(32)
        a = target if index % 3 == 0 else rng.randrange(32)
        b = target if index % 5 == 0 else rng.randrange(32)
        add(reset=int(index % 97 == 0), enable=rng.randrange(3) != 0,
            target=target, value=rng.getrandbits(32), a=a, b=b)
    assert all(coverage[name] > 0 for name in REQUIRED_BINS)
    return ''.join('%x %x %02x %08x %02x %02x %x %08x %08x %08x %08x\n' % row for row in rows), dict(sorted(coverage.items()))


class RegfileOracleTests(unittest.TestCase):
    def test_reset_wins_over_write(self):
        self.assertEqual(committed([(1,1,7,MASK)],7),0)

    def test_x0_cannot_be_overridden(self):
        self.assertEqual(before_edge([],0,1,0,MASK,0),0)
        self.assertEqual(committed([(1,0,0,0),(0,1,0,MASK)],0),0)

    def test_newest_committed_enabled_write(self):
        events=[(1,0,0,0),(0,1,3,17),(0,1,3,29),(0,0,3,42)]
        self.assertEqual(committed(events,3),29)
        self.assertEqual(committed(events,4),0)

    def test_bypass_is_visible_before_commit(self):
        events=[(1,0,0,0),(0,1,3,17)]
        self.assertEqual(before_edge(events,0,1,3,29,3),29)
        self.assertEqual(committed(events,3),17)
        self.assertEqual(before_edge(events,0,0,3,29,3),17)

    def test_warm_reset_cancels_history(self):
        self.assertEqual(committed([(1,0,0,0),(0,1,3,17),(1,1,3,29)],3),0)

    def test_uninitialized_nonzero_read_is_not_assumed_zero(self):
        with self.assertRaises(AssertionError): committed([],1)


if __name__ == '__main__': unittest.main(verbosity=2)
