#!/usr/bin/env python3
"""T025 actual XSim boundary checks and Vivado pin/clock inspection."""
import datetime as dt
import hashlib
import json
import re
import sys
import harness
import rtl_checks
sys.path.insert(0, str(harness.inside('dv/board')))
import board_model


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_xdc(content, facts):
    if (facts['board'] != 'Digilent Basys 3' or facts['part'] != 'xc7a35tcpg236-1' or
            facts['clock'] != {'port':'clk','period_ns':10,'waveform_ns':[0,5]}):
        raise ValueError('Board/clock facts mismatch approved target')
    pattern = r'set_property -dict \{PACKAGE_PIN (\w+) IOSTANDARD (\w+)\} \[get_ports \{([^}]+)\}\]'
    actual = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(pattern, line)
        if match:
            pin, standard, port = match.groups()
            if port in actual:
                raise ValueError('Duplicate port constraint')
            actual[port] = (pin, standard)
        elif line not in ('create_clock -name sys_clk -period 10.000 -waveform {0.000 5.000} [get_ports {clk}]',
                          'set_property CONFIG_VOLTAGE 3.3 [current_design]',
                          'set_property CFGBVS VCCO [current_design]'):
            raise ValueError('Unexpected/relaxed constraint: ' + line)
    expected = {name: (entry[0], facts['io_standard']) for name, entry in facts['pins'].items()}
    if actual != expected or len(actual) != 36 or len(set(pin for pin, _ in actual.values())) != 36:
        raise ValueError('Incomplete/incorrect/aliased board pin map')
    for required in ('create_clock -name sys_clk -period 10.000 -waveform {0.000 5.000} [get_ports {clk}]',
                     'set_property CONFIG_VOLTAGE 3.3 [current_design]', 'set_property CFGBVS VCCO [current_design]'):
        if content.splitlines().count(required) != 1:
            raise ValueError('Missing/duplicate clock or voltage constraint')


def validate_xpr(content):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    options = {x.attrib['Name']: x.attrib['Val'] for x in root.findall('./Configuration/Option')}
    if options.get('Part') != 'xc7a35tcpg236-1':
        raise ValueError('Project part mismatch')
    sets = {x.attrib['Name']: x for x in root.findall('./FileSets/FileSet')}
    for fileset, suffix in [('sources_1', '/fpga/basys3/top.sv'), ('constrs_1', '/fpga/basys3/basys3.xdc')]:
        names = [x.attrib['Path'].replace('\\', '/') for x in sets[fileset].findall('File')]
        if len(names) != 1 or not names[0].endswith(suffix):
            raise ValueError('Unexpected project fileset: ' + fileset)
    top = {x.attrib['Name']: x.attrib['Val'] for x in sets['sources_1'].findall('./Config/Option')}
    if top.get('TopModule') != 'basys3_top':
        raise ValueError('Project top mismatch')


def main():
    c = rtl_checks.Checks('top', task='T025', scope='Basys3 diagnostic shell and selected board constraints only')
    c.result['excluded'] = ['CPU/SoC execution', 'UART controller', 'metastability proof', 'complete CDC analysis', 'formal', 'routed timing', 'physical FPGA', 'ASIC']
    code = 1
    try:
        manifest = rtl_checks.load_manifest()
        sources = ['fpga/basys3/top.sv', 'fpga/basys3/basys3.xdc', 'fpga/basys3/integrate.tcl',
            'config/basys3_pins.json', 'config/rtl_checks.json', 'scripts/board_checks.py',
            'scripts/test_board_checks.py', 'scripts/vivado_board_check.tcl', 'scripts/rtl_checks.py',
            'scripts/tool_runner.py', 'scripts/tool_child.py', 'dv/board/board_model.py',
            'dv/board/tb_board_io.sv', 'RV32I_Edge_SoC.xpr', 'docs/ARCH_CONTRACT.json']
        c.result['source_sha256'] = {f: digest(harness.inside(f)) for f in sources}
        facts = harness.read(harness.inside('config/basys3_pins.json'))
        xdc = harness.inside('fpga/basys3/basys3.xdc')
        validate_xdc(xdc.read_text(), facts)
        validate_xpr(harness.inside('RV32I_Edge_SoC.xpr').read_text())
        c.require(True, 'Exact selected documented pin/clock map and integrated project')
        c.versions(manifest)
        cwd = c.base / 'simulation'
        compile_record = c.vendor('xvlog', ['--sv', str(harness.inside('fpga/basys3/top.sv')),
            str(harness.inside('dv/board/tb_board_io.sv'))], cwd, 15)
        c.require(rtl_checks.successful(compile_record), 'Board shell compile', compile_record)
        elaborate = c.vendor('xelab', ['work.tb_board_io', '--snapshot', 'board_snapshot', '--timescale',
            '1ns/1ps', '--debug', 'typical'], cwd, 30)
        c.require(rtl_checks.successful(elaborate), 'Board shell elaboration', elaborate)
        run_tcl = cwd / 'run.tcl'
        harness.atomic_text(run_tcl, 'log_wave /tb_board_io/clk /tb_board_io/btnC /tb_board_io/sw /tb_board_io/led /tb_board_io/RsRx /tb_board_io/RsTx /tb_board_io/dut/rst_s\nrun all\nquit\n')
        artifacts = {run_tcl.relative_to(harness.ROOT).as_posix(): digest(run_tcl)}
        for seed in (1, 20261104):
            vector = cwd / ('vectors_' + str(seed) + '.txt')
            harness.atomic_text(vector, board_model.vectors(seed))
            count = len(vector.read_text().splitlines())
            wave = cwd / ('seed_' + str(seed) + '.wdb')
            command = ['board_snapshot', '--tclbatch', str(run_tcl), '--onerror', 'quit', '--onfinish', 'quit',
                '--sv_seed', str(seed), '--testplusarg', 'SEED=' + str(seed), '--testplusarg', 'VECTORS=' + str(vector), '--wdb', str(wave)]
            record = c.xsim(command, cwd, 15, 'seed_' + str(seed))
            c.require(rtl_checks.successful(record, 'TOP_SIM_PASS seed=%d checked=%d' % (seed, count)), 'Independent history comparison seed=' + str(seed), record)
            c.require(wave.is_file() and wave.stat().st_size > 0, 'Positive waveform exists')
            c.result['simulations'].append(dict(seed=seed,checked_vectors=count,vector_path=vector.relative_to(harness.ROOT).as_posix(),vector_sha256=digest(vector),waveform=wave.relative_to(harness.ROOT).as_posix(),waveform_sha256=digest(wave)))
        for mode, text, diagnostic in [('wrong-expected', board_model.vectors(1).splitlines()[0].replace(' 0000 ', ' 0001 ') + '\n', 'TOP_MISMATCH'),
                                       ('empty', '', 'TOP_EMPTY_VECTORS'),
                                       ('truncated', board_model.vectors(1).splitlines()[0]+'\n0 1234\n', 'TOP_MALFORMED_VECTOR')]:
            vector = cwd / (mode + '.txt'); harness.atomic_text(vector, text)
            wave = cwd / (mode + '.wdb')
            record = c.xsim(['board_snapshot','--tclbatch',str(run_tcl),'--onerror','quit','--onfinish','quit',
                '--testplusarg','SEED=1','--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],cwd,15,mode)
            output = record['stdout'] + record['stderr']
            c.require(record['status'] in ('PASS','FAIL') and diagnostic in output and 'TOP_SIM_PASS' not in output,
                'Actual negative detected: ' + mode, record)
            c.require(wave.is_file() and wave.stat().st_size > 0, 'Negative waveform exists')
            artifacts.update({p.relative_to(harness.ROOT).as_posix(): digest(p) for p in (vector, wave)})
        expected = c.base / 'expected_pins.tsv'
        harness.atomic_text(expected, ''.join('%s %s %s\n' % (name, entry[0], entry[1]) for name, entry in facts['pins'].items()))
        artifacts[expected.relative_to(harness.ROOT).as_posix()] = digest(expected)
        for label, file, negative in [('positive', xdc, False), ('wrong-clock', c.base / 'wrong-clock.xdc', True)]:
            if negative:
                harness.atomic_text(file, xdc.read_text().replace('-period 10.000', '-period 11.000'))
                artifacts[file.relative_to(harness.ROOT).as_posix()] = digest(file)
            directory = c.base / label
            record = c.vendor('vivado', ['-mode','batch','-nolog','-nojournal','-notrace','-source',
                str(harness.inside('scripts/vivado_board_check.tcl')),'-tclargs',str(harness.ROOT),str(file),str(expected)], directory, 60)
            if negative:
                output = record['stdout'] + record['stderr']
                c.require(record['status']=='FAIL' and record['exit_code']==1 and
                    'BOARD_CONSTRAINTS_FAIL: BOARD_CLOCK_PERIOD' in output and 'BOARD_CONSTRAINTS_PASS' not in output,
                    'Actual wrong clock constraint rejected', record)
            else:
                c.require(rtl_checks.successful(record,'BOARD_CONSTRAINTS_PASS ports=36 clock_ns=10.000') and
                    'SW Build '+manifest['vivado_sw_build'] in record['stdout'],'Actual synthesized pin/clock/DRC inspection',record)
                for name in ('board_io.rpt','board_clocks.rpt','board_utilization.rpt','board_drc.rpt'):
                    path=directory/name;artifacts[path.relative_to(harness.ROOT).as_posix()]=digest(path)
        c.result['artifacts'] = artifacts
        c.require(all(digest(harness.inside(f))==h for f,h in c.result['source_sha256'].items()), 'All board verification sources unchanged')
        c.result['status'] = 'PASS'; code = 0
    except (rtl_checks.NotRun, FileNotFoundError) as exc:
        c.result.update(status='NOT RUN', error=str(exc)); code=125
    except (RuntimeError, ValueError, KeyError, OSError, harness.Stop) as exc:
        c.result.update(status='FAIL', error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps(dict(status=c.result['status'],evidence=c.path.relative_to(harness.ROOT).as_posix(),error=c.result.get('error'))))
    return code


if __name__ == '__main__': sys.exit(main())
