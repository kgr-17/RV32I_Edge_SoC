#!/usr/bin/env python3
"""Pinned, bounded local synthesis lint and independent XSim infrastructure DV."""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import random
import re
import sys
from pathlib import Path
import harness
import tool_runner


class NotRun(RuntimeError):
    pass


def load_manifest():
    manifest = harness.read(harness.inside('config/rtl_checks.json'))
    if manifest['schema_version'] != 1 or not manifest['designs'] or not manifest['seeds']:
        raise ValueError('Invalid/empty toolchain manifest')
    if any(type(seed) is not int or not 0 < seed < 2**31 for seed in manifest['seeds']):
        raise ValueError('Seeds must be positive 31-bit integers')
    registered = set()
    names = set()
    for design in manifest['designs'] + manifest.get('lint_designs', []):
        simulation = design in manifest['designs']
        for key in (('name', 'top', 'test_top') if simulation else ('name', 'top')):
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', design[key]):
                raise ValueError('Invalid design identifier')
        if design['name'] in names or not design['sources']:
            raise ValueError('Duplicate/empty design')
        names.add(design['name'])
        for name in design['sources'] + ([design['testbench']] if simulation else []):
            if not harness.inside(name).is_file():
                raise NotRun('Missing source: ' + name)
        registered.update(design['sources'])
    production = {path.relative_to(harness.ROOT).as_posix()
                  for pattern in ('*.sv', '*.v') for path in harness.inside('rtl').rglob(pattern)}
    if production - registered:
        raise NotRun('Unregistered production RTL: ' + ', '.join(sorted(production - registered)))
    return manifest


def vectors(seed):
    """Oracle = most recent reset or enabled sample in the input history."""
    generator = random.Random(seed)
    stimuli = [(1, 1, 0xffffffff), (0, 0, 0xffffffff), (0, 1, 0x80000001),
               (0, 0, 0x55555555), (1, 0, 0x12345678), (0, 1, 0)]
    stimuli += [(int(index % 29 == 0), generator.randrange(2), generator.getrandbits(32)) for index in range(128)]
    rows = []
    for index, (reset, enable, data) in enumerate(stimuli):
        event = next((sample for sample in reversed(stimuli[:index + 1]) if sample[0] or sample[1]))
        expected = 0 if event[0] else event[2]
        rows.append('%x %x %08x %08x' % (reset, enable, data, expected))
    return '\n'.join(rows) + '\n'


def successful(record, marker=None):
    output = record['stdout'] + '\n' + record['stderr']
    if record['status'] != 'PASS' or record['exit_code'] != 0 or re.search(r'(?im)^\s*(?:ERROR:|FATAL:|Fatal:|WARNING:)', output):
        return False
    return marker is None or output.splitlines().count(marker) == 1


class Checks:
    def __init__(self, profile, task='T003', scope=None):
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        self.path = harness.inside('evidence/toolchain_runs/' + profile + '-' + stamp + '.json')
        self.base = harness.inside('build/' + task + '/' + profile + '-' + stamp)
        self.base.mkdir(parents=True)
        self.result = {'profile': profile, 'status': 'RUNNING', 'started_utc': stamp,
                       'base_commit': harness.run(['git', 'rev-parse', 'HEAD'])['stdout'].strip(),
                       'scope': scope or 'Infrastructure fixture only; no CPU/SoC implementation or hardware',
                       'commands': [], 'checks': [], 'simulations': [],
                       'excluded': ['formal', 'timing closure', 'physical FPGA', 'ASIC', 'CPU ISA correctness']}
        self.save()

    def save(self):
        harness.atomic(self.path, self.result)

    def command(self, argv, directory, timeout):
        record = tool_runner.run(argv, directory, timeout)
        self.result['commands'].append(record)
        self.save()
        if record['status'] == 'NOT RUN':
            raise NotRun('Required command unavailable: ' + repr(argv))
        return record

    def vendor(self, name, args, directory, timeout):
        return self.command(tool_runner.vendor_argv(name, args), directory, timeout)

    def xsim(self, args, directory, timeout, label):
        # AMD's Windows rdiArgs.bat rebuilds argv through %1/shift. Keep values
        # such as SEED=1 out of that batch tokenization; XSim reads them itself.
        path = directory / (label + '.args')
        intended = [arg.replace('\\', '/') for arg in args]
        content = '\n'.join(intended[1:]) + '\n'
        harness.atomic_text(path, content)
        record = self.vendor('xsim', [args[0], '--file', str(path)], directory, timeout)
        record['argument_file'] = {'path': str(path.relative_to(harness.ROOT)),
                                   'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                   'content': content, 'intended_argv': intended}
        self.save()
        return record

    def require(self, condition, description, record=None):
        self.result['checks'].append({'name': description, 'status': 'PASS' if condition else 'FAIL',
                                      'command_index': self.result['commands'].index(record) if record else None})
        self.save()
        if not condition:
            raise RuntimeError(description)

    def versions(self, manifest):
        self.require(platform.python_version() == manifest['python_version'], 'Pinned Python version')
        self.require(importlib.metadata.version('tzdata') == manifest['tzdata_version'], 'Pinned tzdata version')
        git = self.command(['git', '--version'], self.base / 'versions', 10)
        self.require(successful(git) and git['stdout'].strip() == 'git version ' + manifest['git_version'], 'Pinned Git version', git)
        for name in ('xvlog', 'xelab', 'xsim'):
            record = self.vendor(name, ['--version'], self.base / 'versions' / name, 10)
            self.require(successful(record) and 'Vivado Simulator v' + manifest['vivado_version'] in record['stdout'], 'Pinned ' + name + ' version', record)
        self.result['pins'] = {key: value for key, value in manifest.items() if key.endswith('_version') or key == 'vivado_sw_build'}
        self.save()

    def lint(self, sources, top, manifest, negative=False):
        cwd = self.base / ('negative_latch' if negative else 'lint_' + top)
        cwd.mkdir(parents=True)
        source_list = cwd / 'sources.txt'
        harness.atomic_text(source_list, '\n'.join(str(harness.inside(name)) for name in sources) + '\n')
        record = self.vendor('vivado', ['-mode', 'batch', '-nolog', '-nojournal', '-notrace', '-source',
                            str(harness.inside('scripts/vivado_lint.tcl')), '-tclargs', str(source_list), top,
                            'xc7a35tcpg236-1', manifest['vivado_version']], cwd, 45)
        output = record['stdout'] + '\n' + record['stderr']
        if negative:
            self.require(record['status'] == 'FAIL' and 'LATCH_DETECTED' in output,
                         'Inferred latch explicitly rejected', record)
        else:
            self.require(successful(record, 'TOOLCHAIN_LINT_PASS top=' + top), 'Synthesis lint ' + top, record)
            self.require('SW Build ' + manifest['vivado_sw_build'] in output, 'Pinned Vivado SW build', record)

    def simulation(self, design, manifest):
        cwd = self.base / ('sim_' + design['name'])
        compile_record = self.vendor('xvlog', ['--sv'] + [str(harness.inside(name)) for name in design['sources'] + [design['testbench']]], cwd, 15)
        self.require(successful(compile_record), 'SystemVerilog compile ' + design['name'], compile_record)
        elaborate = self.vendor('xelab', ['work.' + design['test_top'], '--snapshot', 'toolchain_snapshot', '--timescale', '1ns/1ps', '--debug', 'typical'], cwd, 30)
        self.require(successful(elaborate), 'Elaboration ' + design['name'], elaborate)
        for seed in manifest['seeds']:
            vector_path = cwd / ('vectors_' + str(seed) + '.txt')
            harness.atomic_text(vector_path, vectors(seed))
            wave = cwd / ('seed_' + str(seed) + '.wdb')
            args = ['toolchain_snapshot', '--tclbatch', str(harness.inside('scripts/xsim_run.tcl')),
                    '--onerror', 'quit', '--onfinish', 'quit', '--sv_seed', str(seed),
                    '--testplusarg', 'SEED=' + str(seed), '--testplusarg', 'VECTORS=' + str(vector_path),
                    '--log', 'seed_' + str(seed) + '.log', '--wdb', str(wave)]
            record = self.xsim(args, cwd, 15, 'seed_' + str(seed))
            self.require(successful(record, 'TOOLCHAIN_SIM_PASS seed=%d checked=134' % seed), 'Independent simulation seed=' + str(seed), record)
            self.require(wave.is_file() and wave.stat().st_size > 0, 'Waveform saved seed=' + str(seed))
            self.result['simulations'].append({'design': design['name'], 'seed': seed, 'checked_vectors': 134,
                'vector_path': str(vector_path.relative_to(harness.ROOT)),
                'vector_sha256': hashlib.sha256(vector_path.read_bytes()).hexdigest(),
                'waveform': str(wave.relative_to(harness.ROOT)), 'waveform_sha256': hashlib.sha256(wave.read_bytes()).hexdigest()})
            self.save()
        seed = manifest['seeds'][0]
        vector_path = cwd / ('vectors_' + str(seed) + '.txt')
        for mode in ('INJECT_FATAL', 'OMIT_PASS', 'HANG'):
            args = ['toolchain_snapshot', '--runall', '--onerror', 'quit', '--onfinish', 'quit',
                    '--testplusarg', 'SEED=' + str(seed), '--testplusarg', 'VECTORS=' + str(vector_path),
                    '--testplusarg', mode, '--log', mode.lower() + '.log', '--wdb', mode.lower() + '.wdb']
            record = self.xsim(args, cwd, 2 if mode == 'HANG' else 15, mode.lower())
            output = record['stdout'] + '\n' + record['stderr']
            rejected = not successful(record, 'TOOLCHAIN_SIM_PASS seed=%d checked=134' % seed)
            if mode == 'INJECT_FATAL':
                rejected = rejected and 'TOOLCHAIN_EXPECTED_FATAL' in output
            elif mode == 'OMIT_PASS':
                rejected = rejected and record['exit_code'] == 0 and 'TOOLCHAIN_SIM_PASS' not in output
            else:
                hang_marker = cwd / 'hang_started.txt'
                rejected = (rejected and record['status'] == 'TIMEOUT' and hang_marker.is_file()
                            and hang_marker.read_text(encoding='utf-8').strip() == 'TOOLCHAIN_EXPECTED_HANG')
            self.require(rejected, 'Negative simulation gate rejects ' + mode, record)

    def syntax_failure(self):
        record = self.vendor('xvlog', ['--sv', str(harness.inside('dv/toolchain/negative_syntax.sv'))], self.base / 'negative_syntax', 15)
        self.require(record['status'] == 'FAIL' and 'syntax error' in (record['stdout'] + record['stderr']).lower(),
                     'Syntax error explicitly rejected', record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', choices=('all', 'lint', 'regress'))
    args = parser.parse_args()
    checks = Checks(args.profile)
    exit_code = 1
    try:
        manifest = load_manifest()
        checks.versions(manifest)
        if manifest.get('lint_designs') and args.profile in ('all', 'lint'):
            checks.result['scope'] = 'Manifest RTL synthesis lint plus infrastructure fixture DV; no complete CPU/SoC or hardware'
            for design in manifest['lint_designs']:
                checks.lint(design['sources'], design['top'], manifest)
        for design in manifest['designs']:
            if args.profile in ('all', 'lint'):
                checks.lint(design['sources'], design['top'], manifest)
            if args.profile in ('all', 'regress'):
                checks.simulation(design, manifest)
        if args.profile in ('all', 'lint'):
            checks.lint(['dv/toolchain/negative_latch.sv'], 'negative_latch', manifest, negative=True)
        if args.profile in ('all', 'regress'):
            checks.syntax_failure()
        checks.result['status'] = 'PASS'
        exit_code = 0
    except (NotRun, FileNotFoundError, importlib.metadata.PackageNotFoundError) as exc:
        checks.result.update(status='NOT RUN', error=str(exc))
        exit_code = 125
    except (RuntimeError, ValueError, KeyError, OSError, harness.Stop) as exc:
        checks.result.update(status='FAIL', error=str(exc))
    checks.result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    checks.save()
    print(json.dumps({'status': checks.result['status'], 'evidence': str(checks.path.relative_to(harness.ROOT)),
                      'checks': len(checks.result['checks']), 'simulations': checks.result['simulations'],
                      'error': checks.result.get('error')}, indent=2))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
