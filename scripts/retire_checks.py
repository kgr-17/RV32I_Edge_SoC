#!/usr/bin/env python3
"""Run actual XSim, then compare its ordered trace and terminal state with ISS."""
import hashlib
import json
import sys
import datetime as dt
import argparse
import harness
import rtl_checks

sys.path.insert(0, str(harness.ROOT))
from dv.reference.retire import TraceMismatch, compare_trace, expected_trace, observed_trace, stimulus_images


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile_for(unit):
    """Bind each real DUT backend to its own task, receipt and exact trace tag."""
    if unit == 'core':
        return 'retire', 'T011', 'CORE', 'reference core'
    if unit == 'backpressure':
        return 'pipeline-iss', 'T018', 'BACKPRESSURE', 'executable pipeline'
    raise ValueError('Unregistered ISS backend: ' + str(unit))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', choices=('core', 'backpressure'), default='core')
    args = parser.parse_args()
    profile, task, prefix, label = profile_for(args.unit)
    checks = rtl_checks.Checks(profile, task=task, scope='Independent ISS vs actual ' + label + ' retirement/fault and terminal-state trace')
    checks.result.update(task=task, unit=args.unit, trace_prefix=prefix)
    if args.unit == 'backpressure':
        checks.result['excluded'] = ['formal', 'routed timing closure', 'physical FPGA', 'ASIC',
                                     'complete ISA/EEI compliance', 'random instruction closure', 'in-flight reset closure']
    checks.result['comparisons'] = []
    exit_code = 1
    try:
        manifest = rtl_checks.load_manifest()
        spec = manifest['unit_sims'][args.unit]
        sources = spec['sources'] + spec.get('extra_inputs', []) + [spec['testbench'], spec['reference'],
                  'scripts/unit_checks.py', 'scripts/rtl_checks.py', 'scripts/tool_runner.py',
                  'scripts/tool_child.py', 'config/rtl_checks.json', '.harness/checks.json', 'docs/ARCH_CONTRACT.json',
                  'scripts/retire_checks.py', 'dv/reference/rv32_iss.py', 'dv/reference/retire.py', 'dv/integration/test_retire.py']
        if args.unit == 'backpressure':
            sources.append('dv/integration/test_pipeline_iss.py')
        sources = list(dict.fromkeys(sources))
        checks.result['source_sha256'] = {name: digest(harness.inside(name)) for name in sources}
        checks.versions(manifest)
        record = checks.command([sys.executable, '-B', str(harness.inside('scripts/unit_checks.py')), args.unit],
                                checks.base, 60)
        # unit_checks.py uses ROOT-relative local manifests and sources; its
        # process working directory can be the isolated evidence build folder.
        checks.require(rtl_checks.successful(record), 'Actual ' + args.unit + ' unit backend passes', record)
        metadata = json.loads(record['stdout'])
        run_path = harness.inside(metadata['evidence'])
        run = harness.read(run_path)
        checks.require(run['status'] == 'PASS' and len(run['simulations']) == len(spec['seeds']),
                       'Nonempty complete actual ' + args.unit + ' seed set')
        checks.require([sim['seed'] for sim in run['simulations']] == spec['seeds'], 'Exact ordered configured seed set')
        checks.result['backend'] = {'path': run_path.relative_to(harness.ROOT).as_posix(), 'sha256': digest(run_path)}
        required = ['op:' + name for name in harness.read(harness.inside('docs/ARCH_CONTRACT.json'))['isa']['instructions']]
        required += ['fault:%d' % n for n in range(1, 10)]
        for sim in run['simulations']:
            seed = sim['seed']
            vector_path = harness.inside(sim['vector_path'])
            checks.require(digest(vector_path) == sim['vector_sha256'], 'Exact simulated program seed=' + str(seed))
            expected, coverage, scenarios = expected_trace(stimulus_images(vector_path.read_text(encoding='utf-8')))
            check = next(row for row in run['checks'] if row['name'] == args.unit + ' independent comparison seed=' + str(seed))
            actual_command = run['commands'][check['command_index']]
            checks.require(check['status'] == 'PASS' and rtl_checks.successful(actual_command),
                           'Successful actual trace producer seed=' + str(seed))
            actual = observed_trace(actual_command['stdout'], prefix=prefix)
            compare_trace(actual, expected)
            checks.require(all(coverage.get(name, 0) > 0 for name in required), 'Independent ISS family/fault coverage seed=' + str(seed))
            checks.require(True, 'Actual retirement/fault/GPR/RAM equality seed=' + str(seed))
            trace_path = checks.base / ('observed_' + str(seed) + '.json')
            expected_path = checks.base / ('expected_' + str(seed) + '.json')
            harness.atomic(trace_path, actual)
            harness.atomic(expected_path, expected)
            corrupt = list(actual)
            pos = next(index for index, event in enumerate(corrupt) if event[0] == 'R')
            row = list(corrupt[pos]); row[-1] ^= 1; corrupt[pos] = tuple(row)
            corrupt_path = checks.base / ('corrupt_' + str(seed) + '.json')
            harness.atomic(corrupt_path, corrupt)
            rejected = []
            for label, data in (('mutated_actual_bit', corrupt), ('empty_actual', []), ('extra_actual_event', actual + actual[:1])):
                try:
                    compare_trace(data, expected)
                except TraceMismatch as exc:
                    rejected.append({'case': label, 'diagnostic': str(exc)})
                else:
                    raise RuntimeError('Comparator accepted injected defect: ' + label)
            checks.require(len(rejected) == 3, 'Actual trace mutations rejected seed=' + str(seed))
            checks.result['comparisons'].append({'seed': seed, 'events': len(actual),
                'backend_command_index': check['command_index'],
                'retirements': sum(event[0] == 'R' for event in actual),
                'faults': sum(event[0] == 'F' for event in actual),
                'gpr_words': sum(event[0] == 'G' for event in actual),
                'ram_words': sum(event[0] == 'M' for event in actual),
                'coverage': coverage, 'required_bins': required, 'scenarios': scenarios,
                'artifacts': {str(path.relative_to(harness.ROOT)): digest(path) for path in (trace_path, expected_path, corrupt_path)},
                'negative_rejections': rejected})
            checks.save()
        checks.require(all(digest(harness.inside(name)) == value for name, value in checks.result['source_sha256'].items()),
                       'ISS and simulated sources unchanged')
        checks.result['status'] = 'PASS'
        exit_code = 0
    except (rtl_checks.NotRun, FileNotFoundError) as exc:
        checks.result.update(status='NOT RUN', error=str(exc)); exit_code = 125
    except (RuntimeError, ValueError, KeyError, OSError, AssertionError, TypeError, harness.Stop, StopIteration) as exc:
        checks.result.update(status='FAIL', error=str(exc))
    checks.result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    checks.save()
    print(json.dumps({'status': checks.result['status'], 'evidence': str(checks.path.relative_to(harness.ROOT)),
                      'comparisons': len(checks.result['comparisons']), 'error': checks.result.get('error')}))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
