#!/usr/bin/env python3
"""Independent pin/constraint mutations and closed-form reset/sample examples."""
import copy
import unittest
from pathlib import Path
import harness
from board_checks import validate_xdc, validate_xpr
import board_model


class BoardPolicyTests(unittest.TestCase):
    def test_integrated_manifest_rejects_missing_extra_disabled_and_stale_sources(self):
        config=harness.read(harness.inside('config/fpga_build.json'))
        source=harness.inside('RV32I_Edge_SoC.xpr').read_text()
        validate_xpr(source,config)
        for before,after in [('/rtl/soc/edge_soc.sv','/rtl/soc/missing.sv'),
                             ('UsedIn" Val="synthesis"','UsedIn" Val="disabled"')]:
            with self.assertRaises(ValueError):validate_xpr(source.replace(before,after),config)
        bad=copy.deepcopy(config);bad['rtl_sources']=bad['rtl_sources'][:-1]
        with self.assertRaises(ValueError):validate_xpr(source,bad)
        # Diagnostic content is byte-identical to the pre-T031 body except name.
        diagnostic=harness.inside('fpga/basys3/diagnostic_top.sv').read_text()
        import zipfile
        with zipfile.ZipFile(harness.inside('evidence/prepare/T031-before-integration/inputs.zip')) as archive:
            original=archive.read('fpga/basys3/top.sv').decode().replace('\r\n','\n')
        self.assertEqual(diagnostic,original.replace('module basys3_top (','module basys3_diagnostic_top ('))

    def setUp(self):
        self.facts = harness.read(harness.inside('config/basys3_pins.json'))
        self.xdc = harness.inside('fpga/basys3/basys3.xdc').read_text()

    def test_actual_documented_constraints(self):
        validate_xdc(self.xdc, self.facts)
        self.assertEqual(self.facts['pins']['RsRx'], ['B18','IN'])
        self.assertEqual(self.facts['pins']['RsTx'], ['A18','OUT'])
        self.assertEqual(self.facts['pins']['clk'], ['W5','IN'])
        self.assertEqual(self.facts['pins']['btnC'], ['U18','IN'])

    def test_missing_extra_duplicate_and_aliased_pins_rejected(self):
        lines = self.xdc.splitlines()
        pin = next(line for line in lines if 'PACKAGE_PIN B18' in line)
        bad = [self.xdc.replace(pin+'\n',''), self.xdc+'\n'+pin,
               self.xdc.replace('PACKAGE_PIN A18','PACKAGE_PIN B18'),
               self.xdc+'\n'+pin.replace('{RsRx}','{unexpected}')]
        for content in bad:
            with self.assertRaises(ValueError):validate_xdc(content,self.facts)

    def test_reversed_uart_bad_standard_and_wrong_clock_rejected(self):
        for before, after in [('PACKAGE_PIN B18','PACKAGE_PIN A18'),('LVCMOS33','LVCMOS18'),
                              ('-period 10.000','-period 20.000'),('-waveform {0.000 5.000}','-waveform {0.000 4.000}')]:
            with self.assertRaises(ValueError):validate_xdc(self.xdc.replace(before,after),self.facts)

    def test_blanket_exceptions_and_missing_config_rejected(self):
        for text in [self.xdc+'\nset_false_path -from [all_inputs]',
                     self.xdc.replace('set_property CFGBVS VCCO [current_design]',''),
                     self.xdc.replace('create_clock -name sys_clk -period 10.000 -waveform {0.000 5.000} [get_ports {clk}]','')]:
            with self.assertRaises(ValueError):validate_xdc(text,self.facts)

    def test_wrong_board_fact_cannot_change_target(self):
        facts=copy.deepcopy(self.facts);facts['part']='xc7a100tcsg324-1'
        with self.assertRaises(ValueError):validate_xdc(self.xdc,facts)

    def test_history_expected_exact_release_and_sample_latency(self):
        samples=[(1,0xffff,0),(0,0x1234,0),(0,0xabcd,1),(0,0x5678,0),(0,0x9876,1),(0,0,1)]
        out=board_model.expected_samples(samples)
        self.assertEqual([x[3:] for x in out],[(0,1,1),(0,1,1),(0,1,0),(0,1,0),(0x5678,0,0),(0x9876,1,0)])

    def test_reasserted_reset_discards_prior_samples(self):
        out=board_model.expected_samples([(1,0,1)]+[(0,65535,0)]*6+[(1,1,0)]+[(0,2,0)]*4)
        self.assertEqual(out[6][3],65535)
        self.assertEqual([row[3:] for row in out[7:]],[(0,1,1),(0,1,1),(0,1,0),(0,1,0),(2,0,0)])

    def test_seed_replay_variation_and_walking_bit_inventory(self):
        self.assertEqual(board_model.vectors(1),board_model.vectors(1))
        self.assertNotEqual(board_model.vectors(1),board_model.vectors(20261104))
        stimulus=board_model.samples(1)
        for bit in range(16):
            self.assertIn(1<<bit,[x[1] for x in stimulus])
            self.assertIn(65535^(1<<bit),[x[1] for x in stimulus])
        for samples in ([],[(0,0,1)],[(1,65536,1)],[(1,0,2)]):
            with self.assertRaises(ValueError):board_model.expected_samples(samples)

    def test_project_parser_requires_real_sources_top_and_part(self):
        source='<Project><Configuration><Option Name="Part" Val="xc7a35tcpg236-1"/></Configuration><FileSets><FileSet Name="sources_1"><File Path="$PPRDIR/fpga/basys3/top.sv"/><Config><Option Name="TopModule" Val="basys3_top"/></Config></FileSet><FileSet Name="constrs_1"><File Path="$PPRDIR/fpga/basys3/basys3.xdc"/></FileSet></FileSets></Project>'
        validate_xpr(source)
        for old,new in [('xc7a35tcpg236-1','wrong'),('basys3_top','unknown'),('/top.sv','/missing.sv'),
                        ('<File Path="$PPRDIR/fpga/basys3/basys3.xdc"/>','')]:
            with self.assertRaises(ValueError):validate_xpr(source.replace(old,new))


if __name__ == '__main__': unittest.main(verbosity=2)
