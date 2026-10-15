#!/usr/bin/env python3
"""Validate repository metadata and inventory tools without starting EDA builds."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import harness


def main():
    plan, state = harness.load()
    path = harness.inside('RV32I_Edge_SoC.xpr')
    project = ET.parse(path).getroot()
    part = project.find("./Configuration/Option[@Name='Part']").get('Val')
    filesets = {fs.get('Name'): [f.get('Path') for f in fs.findall('File')]
                for fs in project.findall('./FileSets/FileSet')}
    baseline = harness.read(harness.inside('docs/PROJECT_BASELINE.json'))
    current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if part != baseline['fpga_part']:
        raise harness.Stop('FPGA part changed; requires owner target review')
    config_path = harness.inside('.harness/toolchain.json')
    config = harness.read(config_path) if config_path.is_file() else {}
    board = config.get('board', {})
    if board.get('fpga_part', part) != part:
        raise harness.Stop('Configured board part does not match the active project')
    tools = {}
    for name in ('vivado', 'xvlog', 'xelab', 'xsim', 'verilator', 'iverilog', 'vvp', 'yosys', 'sby', 'make', 'git', 'docker'):
        explicit = config.get('tools', {}).get(name)
        found = str(Path(explicit)) if explicit and Path(explicit).is_file() else shutil.which(name)
        tools[name] = {'path': found, 'status': 'FOUND' if found else 'NOT FOUND',
                       'found_via': 'project configuration' if explicit and Path(explicit).is_file() else 'PATH'}
    versions = [harness.run(['{python}', '--version']), harness.run(['git', '--version'])]
    packages = {}
    for name in ('cocotb', 'pytest', 'tzdata'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = 'NOT AVAILABLE'
    result = {'status': 'PASS', 'scope': 'metadata and Python/Git readiness ONLY',
              'report_date': harness.today(), 'platform': platform.platform(),
              'python': sys.version, 'tools': tools, 'packages': packages, 'versions': versions,
              'fpga_part': part, 'board': board.get('name', 'UNCONFIRMED'),
              'board_confirmation': board, 'filesets': filesets,
              'configured_vivado_version': config.get('vivado_version'),
              'vivado_version_evidence': config.get('vivado_version_evidence'),
              'xpr_sha256': current_hash, 'xpr_matches_bootstrap': current_hash == baseline['xpr_sha256'],
              'tasks': len(plan['tasks']), 'rtl_simulation': 'NOT RUN', 'vivado_build': 'NOT RUN',
              'sandbox': harness.read(harness.inside('.harness/environment.json'))}
    if any(x['status'] != 'PASS' for x in versions):
        result['status'] = 'FAIL'
    harness.atomic(harness.inside('evidence/toolchain.json'), result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (harness.Stop, OSError, ValueError, AttributeError, ET.ParseError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
