#!/usr/bin/env python3
"""Actual XSim decoder DV, separate from the infrastructure register protocol."""
import datetime as dt
import hashlib
import importlib.metadata
import json
import sys
import harness
import rtl_checks

sys.path.insert(0, str(harness.inside('dv/unit')))
import test_decoder as reference


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = rtl_checks.Checks('decode', task='T004',
        scope='Combinational RV32I decoder unit only; no execution, retirement, memory or pipeline')
    checks.result['excluded'] = ['full CPU ISA correctness', 'formal', 'timing closure', 'physical FPGA', 'ASIC']
    exit_code = 1
    try:
        manifest = rtl_checks.load_manifest()
        seeds = manifest['decode_seeds']
        if not seeds or len(seeds) != len(set(seeds)) or any(type(s) is not int or not 0 < s < 2**31 for s in seeds):
            raise ValueError('Invalid decoder replay seeds')
        checks.versions(manifest)
        sources = ['rtl/core/rv32_pkg.sv', 'rtl/core/decoder.sv', 'dv/unit/tb_decoder.sv']
        cwd = checks.base / 'sim_decoder'
        compile_record = checks.vendor('xvlog', ['--sv'] + [str(harness.inside(name)) for name in sources], cwd, 15)
        checks.require(rtl_checks.successful(compile_record), 'Decoder compile', compile_record)
        elaborate = checks.vendor('xelab', ['work.tb_decoder', '--snapshot', 'decoder_snapshot',
                                  '--timescale', '1ns/1ps', '--debug', 'typical'], cwd, 30)
        checks.require(rtl_checks.successful(elaborate), 'Decoder elaboration', elaborate)

        def simulate(path, count, seed, label):
            wave = cwd / (label + '.wdb')
            args = ['decoder_snapshot', '--tclbatch', str(harness.inside('scripts/xsim_decode.tcl')),
                    '--onerror', 'quit', '--onfinish', 'quit', '--sv_seed', str(seed),
                    '--testplusarg', 'SEED=' + str(seed), '--testplusarg', 'COUNT=' + str(count),
                    '--testplusarg', 'VECTORS=' + str(path), '--log', label + '.log', '--wdb', str(wave)]
            return checks.xsim(args, cwd, 30, label), wave

        for seed in seeds:
            content, coverage = reference.generate(seed)
            count = len(content.splitlines())
            checks.require(count > 0 and all(coverage.get(rule.name, 0) for rule in reference.RULES)
                           and coverage.get('ILLEGAL', 0) > 0,
                           'Nonempty complete decoder suite seed=' + str(seed))
            path = cwd / ('vectors_' + str(seed) + '.txt')
            harness.atomic_text(path, content)
            record, wave = simulate(path, count, seed, 'seed_' + str(seed))
            marker = 'DECODE_SIM_PASS seed=%d checked=%d' % (seed, count)
            checks.require(rtl_checks.successful(record, marker), 'Independent decoder seed=' + str(seed), record)
            checks.require(wave.is_file() and wave.stat().st_size > 0, 'Decoder waveform seed=' + str(seed))
            checks.result['simulations'].append({'design': 'decoder', 'seed': seed, 'checked_vectors': count,
                'vector_path': path.relative_to(harness.ROOT).as_posix(), 'vector_sha256': digest(path),
                'waveform': wave.relative_to(harness.ROOT).as_posix(), 'waveform_sha256': digest(wave),
                'coverage': coverage})
            checks.save()
        # Challenge the actual bench/acceptance path, preserving the good vectors.
        first = content.splitlines()[0].split()
        bad = cwd / 'corrupt_expected.txt'
        harness.atomic_text(bad, '%s %015x\n' % (first[0], int(first[1], 16) ^ 1))
        record, _ = simulate(bad, 1, seeds[-1], 'corrupt_expected')
        checks.require('DECODE_MISMATCH' in record['stdout'] + record['stderr'] and
                       not rtl_checks.successful(record, 'DECODE_SIM_PASS seed=%d checked=1' % seeds[-1]),
                       'Actual decoder bench rejects corrupt expected bit', record)
        empty = cwd / 'empty_vectors.txt'
        harness.atomic_text(empty, '')
        record, _ = simulate(empty, 1, seeds[-1], 'empty_vectors')
        checks.require('Wrong count' in record['stdout'] + record['stderr'] and
                       not rtl_checks.successful(record, 'DECODE_SIM_PASS seed=%d checked=1' % seeds[-1]),
                       'Actual decoder bench rejects empty vectors', record)
        checks.result['status'] = 'PASS'
        exit_code = 0
    except (rtl_checks.NotRun, FileNotFoundError, importlib.metadata.PackageNotFoundError) as exc:
        checks.result.update(status='NOT RUN', error=str(exc))
        exit_code = 125
    except (RuntimeError, ValueError, KeyError, OSError, AssertionError, harness.Stop) as exc:
        checks.result.update(status='FAIL', error=str(exc))
    checks.result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    checks.save()
    print(json.dumps({'status': checks.result['status'], 'evidence': checks.path.relative_to(harness.ROOT).as_posix(),
                      'checks': len(checks.result['checks']), 'counts': [s['checked_vectors'] for s in checks.result['simulations']],
                      'error': checks.result.get('error')}, indent=2))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
