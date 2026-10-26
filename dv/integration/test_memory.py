#!/usr/bin/env python3
"""Independent edge ledger, directed protocol tests and deliberate model defects."""
from collections import Counter
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dv.models.memory import FixedLatencyMemory, MemoryImage, ProtocolError, Request

SEEDS = (1, 20261025)
LATENCIES = (1, 3, 7)
STRESS_EDGES = 4096
RUN_DIR = None
STRESS_RESULTS = []
REJECTED_DEFECTS = []


def check_deferred_store(model):
    req = Request(0x10001, True, 2, 0xaa00)
    before = bytes(model.image.ram)
    first = model.tick(True, req, True)
    assert first.request_accepted and not first.rsp_valid
    assert bytes(model.image.ram) == before, 'store changed memory at request acceptance'
    for _ in range(model.latency + 3):
        model.tick(rsp_ready=False)
        assert bytes(model.image.ram) == before, 'store changed memory before response acceptance'
    edge = model.tick(rsp_ready=True)
    assert edge.response_accepted and not edge.response.error
    expected = bytearray(before)
    expected[1] = 0xaa
    assert model.image.ram == expected


def check_response_stability(model):
    model.image.initialize(0, bytes.fromhex('11223344'))
    model.tick(True, Request(0))
    for _ in range(model.latency):
        first = model.tick()
    assert first.rsp_valid and first.response.data == 0x44332211
    # Explicit setup mutation simulates another agent changing storage. The
    # published response snapshot must remain frozen until its handshake.
    model.image.initialize(0, bytes.fromhex('aabbccdd'))
    for _ in range(5):
        held = model.tick()
        assert held.rsp_valid and held.response == first.response, 'response changed while stalled'
    assert model.tick(rsp_ready=True).response == first.response


def check_no_replacement(model):
    model.tick(True, Request(0))
    for _ in range(model.latency - 1):
        model.tick()
    next_request = Request(4)
    edge = model.tick(True, next_request, True)
    assert edge.response_accepted
    assert not edge.req_ready and not edge.request_accepted, 'replacement accepted on response edge'
    assert model.tick(True, next_request).request_accepted


def check_reset_cancel(model):
    model.tick(True, Request(0x10000, True, 15, 0x12345678))
    for _ in range(model.latency):
        model.tick()
    reset = model.tick(True, Request(4), True, reset=True)
    assert not any((reset.req_ready, reset.rsp_valid, reset.request_accepted, reset.response_accepted))
    assert model.image.read_word(0x10000) == 0
    for _ in range(model.latency + 3):
        assert not model.tick(rsp_ready=True).rsp_valid, 'ghost response after reset'


class MemoryTests(unittest.TestCase):
    def test_fixed_latency_minimum_and_no_duplicate(self):
        for latency in LATENCIES:
            model = FixedLatencyMemory(MemoryImage(), latency=latency)
            req = model.tick(True, Request(0), True)
            self.assertTrue(req.request_accepted)
            self.assertFalse(req.rsp_valid)
            for delta in range(1, latency):
                self.assertFalse(model.tick(rsp_ready=True).rsp_valid, delta)
            rsp = model.tick(rsp_ready=True)
            self.assertEqual(rsp.cycle - req.cycle, latency)
            self.assertTrue(rsp.response_accepted)
            for _ in range(8):
                self.assertFalse(model.tick(rsp_ready=True).rsp_valid)
            self.assertEqual((model.accepted, model.completed, model.cancelled), (1, 1, 0))

    def test_deferred_store_and_each_lane_neighbor(self):
        check_deferred_store(FixedLatencyMemory(MemoryImage(), latency=3))
        for mask, offset in ((1, 0), (2, 1), (4, 2), (8, 3), (3, 0), (12, 2), (15, 0)):
            image = MemoryImage()
            image.initialize(0x10000, bytes.fromhex('112233445566778899aabbcc'))
            model = FixedLatencyMemory(image)
            payload = sum(value << (lane * 8) for lane, value in enumerate((0xde, 0xad, 0xbe, 0xef))
                          if mask & (1 << lane))
            req = Request(0x10004 + offset, True, mask, payload)
            model.tick(True, req)
            self.assertEqual(image.read_word(0x10004), 0x88776655)
            self.assertTrue(model.tick(rsp_ready=True).response_accepted)
            expected = bytearray(bytes.fromhex('55667788'))
            for lane, value in enumerate((0xde, 0xad, 0xbe, 0xef)):
                if mask & (1 << lane):
                    expected[lane] = value
            self.assertEqual(image.ram[:12], bytes.fromhex('11223344') + expected + bytes.fromhex('99aabbcc'))
            # Byte reads return the full aligned word, not the selected byte.
            model.tick(True, Request(0x10004 + offset, byte_enable=mask))
            self.assertEqual(model.tick(rsp_ready=True).response.data, int.from_bytes(expected, 'little'))

    def test_stalled_response_snapshot_and_no_replacement(self):
        check_response_stability(FixedLatencyMemory(MemoryImage(), latency=3))
        check_no_replacement(FixedLatencyMemory(MemoryImage(), latency=3))

    def test_request_stability_and_producer_violations(self):
        original = Request(0x10000, True, 15, 0x12345678)
        changes = [Request(0x10004, True, 15, 0x12345678), Request(0x10000),
                   Request(0x10000, True, 3, 0x5678), Request(0x10000, True, 15, 0x87654321)]
        for changed in changes:
            model = FixedLatencyMemory(MemoryImage())
            self.assertFalse(model.tick(True, original, allow_request=False).req_ready)
            for _ in range(10):
                self.assertFalse(model.tick(True, original, allow_request=False).request_accepted)
            with self.assertRaises(ProtocolError):
                model.tick(True, changed)
            with self.assertRaises(ProtocolError):
                model.tick(req_valid=False)
            self.assertEqual(model.cycle, 11)  # Exceptions have no partial edge effect.
            self.assertTrue(model.tick(True, original).request_accepted)
        with self.assertRaises(FrozenInstanceError):
            original.addr = 4

    def test_invalid_requests_fail_before_bus_acceptance(self):
        for args in ((1, False, 15, 0), (3, True, 12, 0), (0, False, 0, 0),
                     (0, False, 5, 0), (0, False, 15, 1), (1, True, 2, 0xff),
                     (-1,), (2**32,), (0, True, 15, 2**32), (0, 1)):
            with self.subTest(args=args), self.assertRaises(ProtocolError):
                Request(*args)
        instruction = FixedLatencyMemory(MemoryImage(), port='instruction')
        for request in (Request(1, byte_enable=2), Request(0, True, 15, 1), Request(0, byte_enable=1)):
            with self.assertRaises(ProtocolError):
                instruction.tick(True, request)
        with self.assertRaises(ProtocolError):
            instruction.tick(True, None)

    def test_map_permissions_boundaries_and_errors_have_no_effect(self):
        image = MemoryImage()
        image.initialize(0xfffc, bytes.fromhex('01020304'))
        image.initialize(0x1fffc, bytes.fromhex('a1b2c3d4'))
        for port, request, expected_error, data in (
            ('instruction', Request(0xfffc), False, 0x04030201),
            ('instruction', Request(0x10000), True, 0),
            ('data', Request(0xffff, byte_enable=8), False, 0x04030201),
            ('data', Request(0x1ffff, byte_enable=8), False, 0xd4c3b2a1),
            ('data', Request(0x1ffff, True, 8, 0xab000000), False, 0),
            ('data', Request(0, True, 15, 0xdeadbeef), True, 0),
            ('data', Request(0x20000), True, 0),
            ('data', Request(0x10000000), True, 0),  # MMIO is explicitly outside this model.
            ('data', Request(0xfffffffc, True, 15, 0xffffffff), True, 0)):
            before = bytes(image.rom), bytes(image.ram)
            model = FixedLatencyMemory(image, port=port)
            model.tick(True, request)
            response = model.tick(rsp_ready=True)
            self.assertEqual((response.response.error, response.response.data), (expected_error, data))
            if expected_error:
                self.assertEqual((bytes(image.rom), bytes(image.ram)), before)
        model = FixedLatencyMemory(image, error_words=(0x10000,))
        for req in (Request(0x10000), Request(0x10001, True, 2, 0xaa00)):
            before = bytes(image.ram)
            model.tick(True, req)
            for _ in range(7):
                edge = model.tick()
                self.assertEqual((edge.response.error, edge.response.data), (True, 0))
                self.assertEqual(bytes(image.ram), before)
            self.assertTrue(model.tick(rsp_ready=True).response_accepted)
            self.assertEqual(bytes(image.ram), before)

    def test_reset_offered_waiting_stalled_and_committed(self):
        check_reset_cancel(FixedLatencyMemory(MemoryImage(), latency=3))
        for phase in ('offered', 'waiting', 'stalled', 'committed'):
            model = FixedLatencyMemory(MemoryImage(), latency=3)
            req = Request(0x10000, True, 15, 0x12345678)
            model.tick(True, req, allow_request=phase != 'offered')
            if phase in ('stalled', 'committed'):
                for _ in range(3):
                    model.tick(rsp_ready=phase == 'committed')
            model.tick(True, Request(4), True, reset=True)
            for _ in range(8):
                self.assertFalse(model.tick(rsp_ready=True).rsp_valid)
            self.assertEqual(model.image.read_word(0x10000), 0x12345678 if phase == 'committed' else 0)
            self.assertEqual(model.accepted, model.completed + model.cancelled)
            self.assertTrue(model.tick(True, Request(0)).request_accepted)

    def test_instruction_and_data_have_independent_outstanding_slots(self):
        image = MemoryImage()
        image.initialize(0, bytes.fromhex('13000000'))
        instruction = FixedLatencyMemory(image, 'instruction', latency=1)
        data = FixedLatencyMemory(image, 'data', latency=3)
        self.assertTrue(instruction.tick(True, Request(0)).request_accepted)
        self.assertTrue(data.tick(True, Request(0x10000, True, 15, 0xaabbccdd)).request_accepted)
        for _ in range(3):
            self.assertTrue(instruction.tick().rsp_valid)
            data.tick()
        self.assertEqual(image.read_word(0x10000), 0)
        self.assertTrue(data.tick(rsp_ready=True).response_accepted)
        self.assertTrue(instruction.tick(rsp_ready=True).response_accepted)
        self.assertEqual(image.read_word(0x10000), 0xaabbccdd)
        for model in (instruction, data):
            self.assertEqual((model.accepted, model.completed), (1, 1))

    def test_configuration_and_explicit_initialization(self):
        for latency in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                FixedLatencyMemory(MemoryImage(), latency=latency)
        with self.assertRaises(ValueError):
            FixedLatencyMemory(MemoryImage(), port='other')
        with self.assertRaises(ValueError):
            FixedLatencyMemory(MemoryImage(), error_words=(1,))
        image = MemoryImage()
        for addr, payload in ((0xffff, b'ab'), (0x1ffff, b'ab'), (0, b'')):
            with self.assertRaises(ValueError):
                image.initialize(addr, payload)
        with self.assertRaises(KeyError):
            image.initialize(0x20000, b'a')

    def test_deliberate_model_defects_are_rejected(self):
        class EarlyStore(FixedLatencyMemory):
            def tick(self, *args, **kwargs):
                edge = super().tick(*args, **kwargs)
                if edge.request_accepted and self._pending.write:
                    self.image._commit_store(self._pending)
                return edge

        class MovingSnapshot(FixedLatencyMemory):
            def tick(self, *args, **kwargs):
                self._response = None
                return super().tick(*args, **kwargs)

        class ReplacementAcceptance(FixedLatencyMemory):
            def tick(self, *args, **kwargs):
                edge = super().tick(*args, **kwargs)
                if edge.response_accepted:
                    edge = replace(edge, req_ready=True, request_accepted=True)
                return edge

        class IgnoredReset(FixedLatencyMemory):
            def tick(self, *args, **kwargs):
                kwargs['reset'] = False
                return super().tick(*args, **kwargs)

        for defect, probe in ((EarlyStore, check_deferred_store), (MovingSnapshot, check_response_stability),
                              (ReplacementAcceptance, check_no_replacement), (IgnoredReset, check_reset_cancel)):
            with self.subTest(defect=defect.__name__):
                with self.assertRaises(AssertionError):
                    probe(defect(MemoryImage()))
                REJECTED_DEFECTS.append(defect.__name__)

    def test_seeded_independent_event_ledger(self):
        for seed in SEEDS:
            for port in ('instruction', 'data'):
                for latency in LATENCIES:
                    with self.subTest(seed=seed, port=port, latency=latency):
                        self.run_ledger(seed, port, latency)

    def run_ledger(self, seed, port, latency):
        rng = random.Random(seed + latency * 100 + (port == 'data') * 10000)
        initial_rom = bytes(rng.randrange(256) for _ in range(128))
        initial_ram = bytes(rng.randrange(256) for _ in range(128))
        shadow = {index: value for index, value in enumerate(initial_rom)}
        shadow.update({0x10000 + index: value for index, value in enumerate(initial_ram)})
        image = MemoryImage()
        image.initialize(0, initial_rom)
        image.initialize(0x10000, initial_ram)
        model = FixedLatencyMemory(image, port, latency, error_words=(0x10010, 0x10))
        pending = offer = snapshot = None
        accepted = completed = cancelled = 0
        coverage = Counter()
        trace = []
        masks = ((1, 0), (2, 1), (4, 2), (8, 3), (3, 0), (12, 2), (15, 0))
        # At cutoff one request can be pending and another offered but not yet
        # accepted. With ready/allow forced high, both require at most 2*N+2
        # drain edges, including the required no-replacement acceptance bubble.
        for cycle in range(STRESS_EDGES + 2 * latency + 3):
            draining = cycle >= STRESS_EDGES
            reset = not draining and rng.random() < 0.035
            rsp_ready = draining or rng.random() < 0.45
            allow = draining or rng.random() < 0.6
            if offer is None and not draining and rng.random() < 0.65:
                base = rng.choice((0, 0x10000, 0x20000))
                word = rng.randrange(32) * 4
                if port == 'instruction':
                    offer = Request(base + word)
                else:
                    mask, lane = rng.choice(masks)
                    write = rng.random() < 0.5
                    payload = bytes(rng.randrange(256) if write and mask & (1 << n) else 0 for n in range(4))
                    offer = Request(base + word + lane, write, mask, int.from_bytes(payload, 'little'))
            old_pending = pending
            expected_ready = not reset and old_pending is None and allow
            expected_valid = not reset and old_pending is not None and cycle - old_pending[1] >= latency
            if expected_valid and snapshot is None:
                request = old_pending[0]
                address = request.addr
                permitted = (address < 0x10000 and not request.write) or (
                    port == 'data' and 0x10000 <= address <= 0x1ffff)
                error = not permitted or address // 4 in (4, 0x4004)
                value = 0
                if not error and not request.write:
                    value = sum(shadow.get(address // 4 * 4 + n, 0) * (256 ** n) for n in range(4))
                snapshot = value, error
            expected_response = snapshot if expected_valid else (0, False)
            edge = model.tick(offer is not None, offer, rsp_ready, allow, reset)
            self.assertEqual(edge.cycle, cycle)
            self.assertEqual((edge.req_ready, edge.rsp_valid, edge.response.data, edge.response.error),
                             (expected_ready, expected_valid, *expected_response))
            take_req = offer is not None and expected_ready
            take_rsp = expected_valid and rsp_ready
            self.assertEqual((edge.request_accepted, edge.response_accepted), (take_req, take_rsp))
            self.assertFalse(take_req and take_rsp)
            trace.append({'cycle': cycle, 'offer': vars(offer) if offer else None,
                          'allow': allow, 'rsp_ready': rsp_ready, 'reset': reset,
                          'expected': [expected_ready, expected_valid, *expected_response, take_req, take_rsp],
                          'actual': [edge.req_ready, edge.rsp_valid, edge.response.data, edge.response.error,
                                     edge.request_accepted, edge.response_accepted]})
            if reset:
                coverage['reset'] += 1
                if pending:
                    coverage['cancel_response' if snapshot is not None else 'cancel_wait'] += 1
                    cancelled += 1
                if offer:
                    coverage['cancel_offer'] += 1
                pending = offer = snapshot = None
            else:
                if offer and not expected_ready:
                    coverage['request_stall'] += 1
                if expected_valid and not rsp_ready:
                    coverage['response_stall'] += 1
                if take_rsp:
                    completed += 1
                    request = pending[0]
                    coverage['error' if snapshot[1] else 'success'] += 1
                    if not snapshot[1] and request.write:
                        for n, value in enumerate(request.wdata.to_bytes(4, 'little')):
                            if request.byte_enable & (1 << n):
                                shadow[request.addr // 4 * 4 + n] = value
                    pending = snapshot = None
                if take_req:
                    accepted += 1
                    coverage['write' if offer.write else 'read'] += 1
                    coverage['mask:%d' % offer.byte_enable] += 1
                    pending, offer = (offer, cycle), None
            self.assertEqual(bytes(image.ram[:128]), bytes(shadow[0x10000 + n] for n in range(128)))
            self.assertEqual(bytes(image.rom[:128]), initial_rom)
            self.assertEqual(accepted - completed - cancelled, int(pending is not None))
        self.assertIsNone(pending)
        self.assertIsNone(offer)
        self.assertEqual((model.accepted, model.completed, model.cancelled), (accepted, completed, cancelled))
        self.assertEqual(bytes(image.ram[128:]), bytes(0x10000 - 128))
        self.assertEqual(bytes(image.rom[128:]), bytes(0x10000 - 128))
        required = ['reset', 'cancel_wait', 'cancel_response', 'cancel_offer', 'request_stall',
                    'response_stall', 'success', 'error', 'read', 'mask:15']
        # With latency=1 there is no whole edge between acceptance and response
        # creation; resetting that edge is accounted as cancel_wait in this ledger.
        if latency == 1:
            required.remove('cancel_wait')
        if port == 'data':
            required += ['write'] + ['mask:%d' % mask for mask, _ in masks]
        self.assertTrue(all(coverage[name] > 0 for name in required), dict(coverage))
        result = {'seed': seed, 'port': port, 'latency': latency, 'edges': len(trace),
                  'accepted': accepted, 'completed': completed, 'cancelled': cancelled,
                  'coverage': dict(sorted(coverage.items())), 'required_bins': required}
        if RUN_DIR is not None:
            path = RUN_DIR / ('%s-seed_%d-latency_%d.jsonl' % (port, seed, latency))
            raw = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in trace).encode('utf-8')
            path.write_bytes(raw)
            result.update(trace=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest())
        STRESS_RESULTS.append(result)


def main():
    global RUN_DIR
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    RUN_DIR = ROOT / 'build' / 'T009' / ('memory-' + stamp)
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    sources = ['dv/models/memory.py', 'dv/integration/test_memory.py', '.harness/checks.json']
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MemoryTests)
    count = suite.countTestCases()
    if count == 0:
        raise RuntimeError('NOT RUN: no memory model tests')
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    drift = any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value for name, value in hashes.items())
    passed = result.wasSuccessful() and not drift and len(STRESS_RESULTS) == 12 and len(REJECTED_DEFECTS) == 4
    evidence = {'profile': 'memory-model', 'task': 'T009', 'stamp': stamp,
                'scope': 'Python behavioral models; no RTL bus/core simulation',
                'argv': [sys.executable, '-B', *sys.argv], 'python': platform.python_version(),
                'git': subprocess.check_output(['git', '--version'], cwd=ROOT, text=True).strip(),
                'status': 'PASS' if passed else 'FAIL', 'exit_code': 0 if passed else 1,
                'elapsed_seconds': round(time.monotonic() - started, 3),
                'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                'skipped': len(result.skipped), 'source_sha256': hashes, 'source_drift': drift,
                'directed_defects_rejected': REJECTED_DEFECTS,
                'failure_details': [(str(test), detail) for test, detail in result.failures + result.errors],
                'stress': STRESS_RESULTS}
    path = ROOT / 'evidence' / 'toolchain_runs' / ('memory-' + stamp + '.json')
    path.write_bytes((json.dumps(evidence, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'status': evidence['status'], 'evidence': str(path.relative_to(ROOT)),
                      'tests': result.testsRun, 'stress_edges': sum(row['edges'] for row in STRESS_RESULTS)}))
    return evidence['exit_code']


if __name__ == '__main__':
    sys.exit(main())
