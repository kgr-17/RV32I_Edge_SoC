"""Decode stimulus images and compare complete, ordered observed ISS traces."""
from collections import Counter
from dv.reference.rv32_iss import RV32ISS


class TraceMismatch(ValueError):
    pass


def stimulus_images(content):
    """Ignore hand-authored expected rows; only load program/data initialization."""
    cases, current = [], None
    for line in content.splitlines():
        values = [int(token, 16) for token in line.split()]
        if len(values) != 13:
            raise ValueError('malformed stimulus record')
        kind = values[0]
        if kind == 0:
            if current is not None:
                raise ValueError('unclosed scenario')
            current = {'id': values[5], 'image': {}}
        elif kind in (1, 2):
            if current is None:
                raise ValueError('initialization outside scenario')
            addr, value = values[1:3]
            current['image'].update({addr + n: byte for n, byte in enumerate(value.to_bytes(4, 'little'))})
        elif kind == 3:
            if current is None:
                raise ValueError('expectation outside scenario')
            # T010's expected records are deliberately NOT an input to this oracle.
        elif kind == 4:
            if current is None:
                raise ValueError('termination outside scenario')
            cases.append(current)
            current = None
        else:
            raise ValueError('unknown stimulus record')
    if current is not None or not cases or len({case['id'] for case in cases}) != len(cases):
        raise ValueError('empty, incomplete or duplicate scenarios')
    return cases


def expected_trace(cases, error_words_by_scenario=None):
    error_words_by_scenario = error_words_by_scenario or {}
    if any(type(ident) is not int or ident not in {case['id'] for case in cases}
           for ident in error_words_by_scenario):
        raise ValueError('fault injection names an unknown scenario')
    result, coverage, summaries = [], Counter(), []
    for case in cases:
        ident = case['id']
        iss = RV32ISS(case['image'], error_words=error_words_by_scenario.get(ident, ()))
        events, fault = iss.run()
        result.extend(('R', ident, *event.fields()) for event in events)
        result.append(('F', ident, fault.pc, fault.insn, fault.code, fault.tval))
        result.extend(('G', ident, n, iss.regs[n]) for n in range(1, 32))
        # Directed programs touch this 128-byte window. T010's SV scoreboard
        # independently checks all 64 KiB; effects outside this sample remain
        # represented in each complete memory retirement record.
        result.extend(('M', ident, n, iss._word(0x10000 + n * 4)) for n in range(32))
        coverage.update('op:' + op for op in iss.operations)
        coverage['fault:%d' % fault.code] += 1
        summaries.append({'scenario': ident, 'retirements': len(events), 'fault': vars(fault),
                          'gpr_words': 31, 'ram_words': 32})
    return result, dict(sorted(coverage.items())), summaries


def observed_trace(output, prefix='CORE'):
    if prefix not in ('CORE', 'BACKPRESSURE', 'ISA_COMPLETE', 'RANDOM'):
        raise ValueError('Unregistered observed trace prefix')
    tags = {prefix + '_' + name: (kind, length) for name, kind, length in
            (('RETIRE', 'R', 15), ('FAULT', 'F', 6), ('GPR', 'G', 4), ('RAM', 'M', 4))}
    events = []
    for line in output.splitlines():
        parts = line.split()
        if not parts or parts[0] not in tags:
            continue
        tag = parts[0]
        kind, expected_length = tags[tag]
        if len(parts) != expected_length:
            raise TraceMismatch('malformed observed ' + tag)
        try:
            ident = int(parts[1], 10)
            if kind in ('G', 'M'):
                events.append((kind, ident, int(parts[2], 10), int(parts[3], 16)))
            else:
                events.append((kind, ident, *(int(token, 16) for token in parts[2:])))
        except ValueError as exc:
            raise TraceMismatch('invalid/X-valued observed trace: ' + line) from exc
    if not events:
        raise TraceMismatch('zero observed events')
    return events


def compare_trace(actual, expected):
    if not actual or not expected:
        raise TraceMismatch('zero-test trace comparison')
    if len(actual) != len(expected):
        raise TraceMismatch('event count mismatch actual=%d expected=%d' % (len(actual), len(expected)))
    for index, (observed, reference) in enumerate(zip(actual, expected)):
        if tuple(observed) != tuple(reference):
            raise TraceMismatch('event %d mismatch: actual=%r expected=%r' % (index, observed, reference))
