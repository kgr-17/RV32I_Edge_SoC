#!/usr/bin/env python3
"""Negative tests for the architecture checker, not a CPU/ISA testbench."""
import json
from pathlib import Path
import unittest
import check_arch_spec as checker

ROOT = Path(__file__).resolve().parents[1]


class ContractChecks(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / 'docs/ARCH_CONTRACT.json').read_text(encoding='utf-8'))
        self.spec = (ROOT / 'docs/ARCH_SPEC.md').read_text(encoding='utf-8')
        self.backlog = json.loads((ROOT / 'docs/BACKLOG.json').read_text(encoding='utf-8'))

    def check(self):
        return checker.validate(self.contract, self.spec, self.backlog,
                                'xc7a35tcpg236-1', 'xc7a35tcpg236-1')

    def reject(self, fragment):
        self.assertTrue(any(fragment in e for e in self.check()), self.check())

    def test_actual_proposal_is_consistent(self):
        self.assertEqual(self.check(), [])

    def test_instruction_missing_or_duplicate(self):
        self.contract['isa']['instructions'][-1] = 'ECALL'
        self.reject('instruction inventory')

    def test_overlapping_regions_rejected(self):
        self.contract['memory_map'][1]['base'] = 0xfffc
        self.reject('overlap')

    def test_nonexecutable_boot_rejected(self):
        self.contract['core']['reset']['pc'] = 0x10000
        self.reject('Reset PC')

    def test_port_documentation_drift_rejected(self):
        self.spec = self.spec.replace('| dmem_req_be_o | output | 4 |',
                                      '| dmem_req_be_o | output | 8 |')
        self.reject('port table')

    def test_bus_width_mismatch_rejected(self):
        self.contract['bus']['byte_enable_width'] = 8
        self.reject('lane/width')

    def test_wrong_priority_rejected(self):
        self.contract['core']['priority'][2:4] = ['redirect', 'memory_hold']
        self.reject('priority')

    def test_response_zero_latency_rejected(self):
        self.contract['bus']['min_response_cycles'] = 0
        self.reject('protocol invariant')

    def test_fault_code_collision_rejected(self):
        self.contract['fault_codes']['BREAKPOINT'] = 8
        self.reject('collision')

    def test_register_outside_region_rejected(self):
        self.contract['registers'][0]['offset'] = 0x20
        self.reject('Register escapes')

    def test_unknown_traceability_task_rejected(self):
        self.contract['requirements'][0]['tasks'] = ['T999']
        self.reject('unknown task')

    def test_wrong_target_part_rejected(self):
        self.contract['target']['fpga_part'] = 'unapproved-part'
        self.reject('Target part')

    def test_self_approval_rejected(self):
        self.contract['approval_status'] = 'approved'
        self.reject('self-approve')

    def test_reset_policy_ambiguity_rejected(self):
        self.contract['core']['reset']['synchronous'] = False
        self.reject('Reset contract')

    def test_missing_required_field_rejected(self):
        del self.contract['bus']['write_error_has_no_effect']
        self.reject('Malformed')

    def test_direction_suffix_rejected(self):
        self.contract['core']['ports'][0]['direction'] = 'output'
        self.reject('direction suffix')


if __name__ == '__main__':
    unittest.main(verbosity=2)
