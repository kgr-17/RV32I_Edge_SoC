#!/usr/bin/env python3
"""Check the proposed architecture documents. This does not verify any RTL."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import harness

ROOT = Path(__file__).resolve().parents[1]
RV32I = set("""LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU
SB SH SW ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU
XOR SRL SRA OR AND FENCE ECALL EBREAK""".split())
PRIORITY = ['reset', 'oldest_fault', 'memory_hold', 'redirect', 'load_use', 'advance']


def validate(contract, spec, backlog, xpr_part, board_part):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    try:
        require(contract['schema_version'] == 1, 'Unknown contract schema')
        require(contract['version'] == '0.2-proposed', 'Unexpected submission version')
        require(contract['approval_status'] == 'pending_owner_review',
                'This submission must not self-approve its architecture')
        target = contract['target']
        require(target['fpga_part'] == xpr_part == board_part, 'Target part mismatch')
        require(target['board'] == 'Digilent Basys 3', 'Unexpected board')
        require(target['clock_hz'] == 100000000 and target['clock_period_ns'] == 10,
                'Clock frequency/period mismatch')
        require(target['clock_domains'] == 1 and target['clock_pin'] == 'W5',
                'Clock-domain or documented source-pin mismatch')
        isa = contract['isa']
        require(isa['name'] == 'RV32I' and isa['version'] == '2.1' and
                isa['manual_snapshot'] == '20240411', 'Unpinned ISA identity')
        require(isa['xlen'] == 32 and isa['registers'] == 32 and
                isa['ialign_bits'] == 32 and isa['endianness'] == 'little', 'ISA state mismatch')
        require(len(isa['instructions']) == 40 and set(isa['instructions']) == RV32I,
                'Base instruction inventory missing, duplicated or extended')
        require({'Zicsr', 'Zifencei', 'C', 'M'} <= set(isa['excluded_extensions']),
                'Unsupported extensions must be explicit')
        require(isa['eei_policy'] == 'precise_fatal_fault_halt_until_reset' and
                isa['fence_policy'] == 'conservative_full_drain', 'EEI/FENCE ambiguity')
        core = contract['core']
        require(core['stages'] == ['IF', 'ID', 'EX', 'MEM', 'WB'] and
                core['branch_stage'] == 'EX' and core['retire_stage'] == 'WB', 'Pipeline mismatch')
        require(core['priority'] == PRIORITY, 'Conflicting control priority')
        reset = core['reset']
        require(reset['signal'] == 'rst_i' and reset['active_level'] == 1 and
                reset['synchronous'] is True and reset['gpr_policy'] == 'all_zero' and
                reset['memory_contents'] == 'preserved', 'Reset contract ambiguity')
        require(core['load_forwarding'] == 'WB_only' and
                core['store_effect_point'] == 'successful_response_handshake',
                'Forwarding/effect-point mismatch')
        bus = contract['bus']
        require(bus['address_width'] == bus['data_width'] == 32 and
                bus['byte_enable_width'] == bus['data_width'] // 8, 'Bus lane/width mismatch')
        require(bus['max_outstanding_per_bus'] == 1 and bus['min_response_cycles'] == 1 and
                bus['stalled_request_stable'] is True and bus['reset_cancels_transactions'] is True and
                bus['write_error_has_no_effect'] is True, 'Bus protocol invariant violated')
        require(bus['request_address'] == 'original_byte_effective_address' and
                bus['read_data'] == 'aligned_32bit_word' and bus['write_data'] == 'lane_shifted' and
                bus['byte_enable'] == 'selected_lanes_for_reads_and_writes', 'Address/lane semantic drift')
        require(sorted(bus['valid_byte_enables']) == [1, 2, 3, 4, 8, 12, 15],
                'Invalid byte-enable inventory')
        ports = core['ports']
        byport = {p['name']: p for p in ports}
        require(len(byport) == len(ports), 'Duplicate port name')
        required = {'clk_i': 1, 'rst_i': 1, 'imem_req_addr_o': 32, 'dmem_req_addr_o': 32,
                    'imem_rsp_rdata_i': 32, 'dmem_rsp_rdata_i': 32, 'dmem_req_wdata_o': 32,
                    'dmem_req_be_o': 4, 'retire_order_o': 64, 'retire_rd_o': 5,
                    'fault_code_o': 4, 'fault_valid_o': 1}
        for name, width in required.items():
            require(name in byport and byport[name]['width'] == width, 'Missing/incorrect port: ' + name)
        for p in ports:
            require(type(p['width']) is int and p['width'] > 0 and
                    p['direction'] in ('input', 'output'), 'Invalid port shape')
            require((p['name'].endswith('_i') and p['direction'] == 'input') or
                    (p['name'].endswith('_o') and p['direction'] == 'output'), 'Port direction suffix mismatch')
        rows = re.findall(r'^\| (\w+) \| (input|output) \| (\d+) \|$', spec, flags=re.M)
        require(len(rows) == len(ports) and
                {(n, d, int(w)) for n, d, w in rows} ==
                {(p['name'], p['direction'], p['width']) for p in ports}, 'Markdown port table drifts from JSON')
        regions = contract['memory_map']
        byregion = {r['id']: r for r in regions}
        require(set(byregion) == {'rom', 'ram', 'uart', 'gpio', 'timer'} and
                len(byregion) == len(regions), 'Missing/duplicate map region')
        ordered = sorted(regions, key=lambda r: r['base'])
        for region in regions:
            base, size = region['base'], region['size']
            require(type(base) is int and type(size) is int and
                    base >= 0 and size > 0 and base % 4 == size % 4 == 0 and
                    base + size <= 2**32, 'Invalid region bounds/alignment')
            require(all(type(region[k]) is bool for k in ('read', 'write', 'execute')),
                    'Access permissions must be booleans')
            require('0x{:08x}'.format(base) in spec and
                    '0x{:08x}'.format(base + size - 1) in spec, 'Markdown region bounds drift')
        require(all(a['base'] + a['size'] <= b['base'] for a, b in zip(ordered, ordered[1:])),
                'Memory regions overlap')
        rom, ram = byregion['rom'], byregion['ram']
        require(rom['base'] == 0 and ram['base'] == 0x10000 and rom['size'] == ram['size'] == 65536,
                'Original ROM/RAM addresses or capacity changed')
        require(rom['execute'] and rom['read'] and not rom['write'] and not ram['execute'] and
                ram['read'] and ram['write'], 'ROM/RAM permissions mismatch')
        require(any(r['execute'] and r['base'] <= reset['pc'] < r['base'] + r['size']
                    and reset['pc'] % 4 == 0 for r in regions), 'Reset PC is not executable/aligned')
        registers = contract['registers']
        addresses, names = [], []
        for reg in registers:
            region = byregion[reg['region']]
            offset = reg['offset']
            require(type(offset) is int and offset >= 0 and offset % 4 == 0 and
                    offset + 4 <= region['size'], 'Register escapes or misaligns its region')
            address = region['base'] + offset
            addresses.append(address); names.append(reg['name'])
            require('| 0x{:08x} | {} |'.format(address, reg['name']) in spec,
                    'Markdown register drift: ' + reg['name'])
            require(reg['access'] in ('read', 'write', 'read_write') and
                    type(reg['reset']) is int and 0 <= reg['reset'] < 2**32, 'Register metadata invalid')
        require(len(set(addresses)) == len(addresses) and len(set(names)) == len(names),
                'Register aliases/duplicates require explicit review')
        faults = contract['fault_codes']
        require(len(faults) == 9 and sorted(faults.values()) == list(range(1, 10)) and
                max(faults.values()) < 2**byport['fault_code_o']['width'], 'Fault code collision/overflow')
        known = {t['id'] for t in backlog['tasks']}
        requirements = contract['requirements']
        require(len({r['id'] for r in requirements}) == len(requirements), 'Duplicate requirement ID')
        require(len(requirements) >= 20, 'Missing requirement traceability')
        for req in requirements:
            require(req['tasks'] and set(req['tasks']) <= known, 'Requirement references unknown task')
        for source in contract['sources']:
            require(urlparse(source['url']).scheme == 'https' and
                    urlparse(source['url']).hostname in ('docs.riscv.org', 'digilent.com'),
                    'Nonprimary/unsecured normative source')
    except (KeyError, TypeError, ValueError) as exc:
        errors.append('Malformed contract: ' + str(exc))
    return errors


def main():
    raw = (ROOT / 'docs/ARCH_CONTRACT.json').read_bytes()
    contract = json.loads(raw)
    part = ET.parse(ROOT / 'RV32I_Edge_SoC.xpr').getroot().find(
        "./Configuration/Option[@Name='Part']").get('Val')
    errors = validate(contract, (ROOT / 'docs/ARCH_SPEC.md').read_text(encoding='utf-8'),
                      harness.read(ROOT / 'docs/BACKLOG.json'), part,
                      harness.read(ROOT / '.harness/toolchain.json')['board']['fpga_part'])
    result = {'status': 'FAIL' if errors else 'PASS', 'scope': 'Proposed document consistency ONLY',
              'contract_sha256': hashlib.sha256(raw).hexdigest(), 'version': contract['version'],
              'ports': len(contract['core']['ports']), 'instructions': len(contract['isa']['instructions']),
              'requirements': len(contract['requirements']), 'errors': errors,
              'rtl_verification': 'NOT RUN', 'owner_approval': 'PENDING'}
    harness.atomic(ROOT / 'evidence/arch_contract_check.json', result)
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
