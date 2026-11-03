#!/usr/bin/env python3
"""Manifest-driven unit XSim DV with independent Python vectors and negative gates."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata
import json
import re
import sys
import harness
import rtl_checks


def identifier(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        raise ValueError('Invalid unit identifier')
    return value


def unit_spec(manifest, unit):
    spec = manifest.get('unit_sims', {}).get(unit)
    if not spec:
        raise rtl_checks.NotRun('No configured unit simulation: ' + unit)
    identifier(spec['test_top'])
    if not re.fullmatch(r'T[0-9]{3}', spec['task']) or not spec['sources']:
        raise ValueError('Invalid unit task/sources')
    seeds = spec['seeds']
    if not seeds or len(seeds) != len(set(seeds)) or any(type(s) is not int or not 0 < s < 2**31 for s in seeds):
        raise ValueError('Invalid unit replay seeds')
    for name in spec['sources'] + [spec['testbench'], spec['reference']] + spec.get('extra_inputs', []):
        if not harness.inside(name).is_file():
            raise rtl_checks.NotRun('Missing unit input: ' + name)
    if not spec['waves'] or any(not re.fullmatch(r'/[A-Za-z_][A-Za-z0-9_/]*', name) for name in spec['waves']):
        raise ValueError('Invalid wave signal list')
    return spec


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corrupt_expected(content, full_program=False):
    lines = content.splitlines()
    if not lines:
        raise ValueError('Cannot corrupt empty test input')
    first = lines[0].split()
    first[-1] = '%x' % (int(first[-1], 16) ^ 1)
    lines[0] = ' '.join(first)
    return '\n'.join(lines if full_program else lines[:1]) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('unit')
    unit = identifier(parser.parse_args().unit)
    checks = rtl_checks.Checks(unit, task='units', scope=unit + ' unit simulation only; no full CPU or hardware')
    checks.result['excluded'] = ['full CPU execution/retirement', 'formal', 'timing closure', 'physical hardware', 'ASIC']
    exit_code = 1
    try:
        manifest = rtl_checks.load_manifest()
        spec = unit_spec(manifest, unit)
        checks.result['task'] = spec['task']
        inputs = spec['sources'] + [spec['testbench'], spec['reference'], 'config/rtl_checks.json',
                                    'scripts/unit_checks.py', 'scripts/rtl_checks.py'] + spec.get('extra_inputs', [])
        checks.result['source_sha256'] = {name: digest(harness.inside(name)) for name in inputs}
        checks.versions(manifest)
        module = importlib.util.spec_from_file_location('unit_reference_' + unit, harness.inside(spec['reference']))
        reference = importlib.util.module_from_spec(module)
        module.loader.exec_module(reference)
        if not reference.REQUIRED_BINS:
            raise ValueError('Independent oracle must declare coverage bins')
        cwd = checks.base / ('sim_' + unit)
        tcl = cwd / 'run.tcl'
        harness.atomic_text(tcl, 'log_wave ' + ' '.join(spec['waves']) + '\nrun all\nquit\n')
        checks.result['tcl'] = {'path': tcl.relative_to(harness.ROOT).as_posix(), 'sha256': digest(tcl)}
        compile_record = checks.vendor('xvlog', ['--sv'] + [str(harness.inside(name)) for name in spec['sources'] + [spec['testbench']]], cwd, 15)
        checks.require(rtl_checks.successful(compile_record), unit + ' compile', compile_record)
        elaborate = checks.vendor('xelab', ['work.' + spec['test_top'], '--snapshot', 'unit_snapshot',
                                  '--timescale', '1ns/1ps', '--debug', 'typical'], cwd, 30)
        checks.require(rtl_checks.successful(elaborate), unit + ' elaboration', elaborate)
        prefix = unit.upper()

        def simulate(path, count, seed, label):
            wave = cwd / (label + '.wdb')
            args = ['unit_snapshot', '--tclbatch', str(tcl), '--onerror', 'quit', '--onfinish', 'quit',
                    '--sv_seed', str(seed), '--testplusarg', 'SEED=' + str(seed),
                    '--testplusarg', 'COUNT=' + str(count), '--testplusarg', 'VECTORS=' + str(path),
                    '--log', label + '.log', '--wdb', str(wave)]
            return checks.xsim(args, cwd, 30, label), wave

        for seed in spec['seeds']:
            content, coverage = reference.generate(seed)
            count = len(content.splitlines())
            checks.require(count > 0 and all(coverage.get(name, 0) > 0 for name in reference.REQUIRED_BINS),
                           unit + ' coverage bins seed=' + str(seed))
            path = cwd / ('vectors_' + str(seed) + '.txt')
            harness.atomic_text(path, content)
            record, wave = simulate(path, count, seed, 'seed_' + str(seed))
            marker = '%s_SIM_PASS seed=%d checked=%d' % (prefix, seed, count)
            checks.require(rtl_checks.successful(record, marker), unit + ' independent comparison seed=' + str(seed), record)
            checks.require(wave.is_file() and wave.stat().st_size > 0, unit + ' waveform seed=' + str(seed))
            checks.result['simulations'].append({'design': unit, 'seed': seed, 'checked_vectors': count,
                'vector_path': path.relative_to(harness.ROOT).as_posix(), 'vector_sha256': digest(path),
                'waveform': wave.relative_to(harness.ROOT).as_posix(), 'waveform_sha256': digest(wave),
                'coverage': coverage})
            checks.save()
        bad = cwd / 'corrupt_expected.txt'
        bad_content = corrupt_expected(content, getattr(reference, 'NEGATIVE_FULL_PROGRAM', False))
        harness.atomic_text(bad, bad_content)
        bad_count = len(bad_content.splitlines())
        seed = spec['seeds'][-1]
        marker = '%s_SIM_PASS seed=%d checked=%d' % (prefix, seed, bad_count)
        record, _ = simulate(bad, bad_count, seed, 'corrupt_expected')
        checks.require(getattr(reference, 'NEGATIVE_DIAGNOSTIC', prefix + '_MISMATCH') in record['stdout'] + record['stderr'] and
                       not rtl_checks.successful(record, marker), unit + ' rejects corrupt expected bit', record)
        empty = cwd / 'empty_vectors.txt'
        harness.atomic_text(empty, '')
        record, _ = simulate(empty, 1, seed, 'empty_vectors')
        checks.require('Wrong count' in record['stdout'] + record['stderr'] and
                       not rtl_checks.successful(record, marker), unit + ' rejects empty vectors', record)
        checks.require(all(digest(harness.inside(name)) == value for name, value in checks.result['source_sha256'].items()),
                       unit + ' sources unchanged during verification')
        checks.result['status'] = 'PASS'
        exit_code = 0
    except (rtl_checks.NotRun, FileNotFoundError, importlib.metadata.PackageNotFoundError) as exc:
        checks.result.update(status='NOT RUN', error=str(exc)); exit_code = 125
    except (RuntimeError, ValueError, KeyError, OSError, AssertionError, TypeError, harness.Stop) as exc:
        checks.result.update(status='FAIL', error=str(exc))
    checks.result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    checks.save()
    print(json.dumps({'status': checks.result['status'], 'evidence': checks.path.relative_to(harness.ROOT).as_posix(),
                      'checks': len(checks.result['checks']), 'counts': [s['checked_vectors'] for s in checks.result['simulations']],
                      'error': checks.result.get('error')}, indent=2))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
