"""Challenge report integrity and timing failure propagation without EDA claims."""
import pathlib
import hashlib
import json
import zipfile
import unittest
import tempfile
import fpga_reports
import harness


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=harness.inside('dv/fpga/fixtures')
        manifest=json.loads((folder/'manifest.json').read_text())
        assert hashlib.sha256((folder/'reports.zip').read_bytes()).hexdigest()==manifest['zip_sha256']
        with zipfile.ZipFile(folder/'reports.zip') as archive:
            for name,digest in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==digest
            cls.raw=archive.read('synthesis_timing.rpt').decode().replace('\r\n','\n')
            cls.use=archive.read('synthesis_utilization.rpt').decode().replace('\r\n','\n')
        manifest=json.loads((folder/'routed_manifest.json').read_text())
        assert hashlib.sha256((folder/'routed_reports.zip').read_bytes()).hexdigest()==manifest['zip_sha256']
        with zipfile.ZipFile(folder/'routed_reports.zip') as archive:
            cls.routed={name:archive.read(name) for name in manifest['files']}
        for name,digest in manifest['files'].items():assert hashlib.sha256(cls.routed[name]).hexdigest()==digest
    def setUp(self):
        base=harness.inside('build/T043/report-policy-tests');base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=str(base));self.folder=pathlib.Path(self.temp.name)
        for name,data in self.routed.items():(self.folder/name).write_bytes(data)
    def tearDown(self):self.temp.cleanup()
    def test_real_routed_reports_decode_but_negative_timing_cannot_pass(self):
        r=fpga_reports.routed_reports(self.folder)
        self.assertEqual(r['timing']['setup']['worst_slack_ns'],-1.657)
        self.assertEqual(r['utilization']['Slice Registers']['used'],2567)
        self.assertEqual(r['physical_inventory']['async_chains'],18)
        self.assertEqual(r['power']['confidence'],'Low')
        self.assertEqual(r['route_status']['nets with routing errors'],0)
        with self.assertRaisesRegex(ValueError,'TIMING_FAILED'):fpga_reports.validate_complete(self.folder)
    def test_real_routed_report_defects_are_rejected(self):
        mutations=[('routed_clocks.rpt','10.000','11.000'),
            ('routed_clock_interaction.rpt','Clean','Unknown'),
            ('routed_cdc.rpt','All paths are Safely Timed.','CDC-1 Critical'),
            ('routed_drc.rpt','Checks found: 0','Checks found: 1'),
            ('routed_route_status.rpt','errors.......... :           0','errors.......... :           1'),
            ('routed_route_status.rpt','6462','6461'),
            ('physical_inventory.tsv','async_regs\t36','async_regs\t35'),
            ('physical_inventory.tsv','\t1\t1\t1','\t1\t0\t1'),
            ('routed_power.rpt','0.095','NaN'),
            ('routed_power.rpt','| Low          |','| Unknown      |'),
            ('routed_power.rpt','| Simulation Activity File | ---','| Simulation Activity File | other.saif'),
            ('routed_activity.rpt','btnC','missing_button')]
        for name,before,after in mutations:
            raw=self.routed[name].decode();self.assertIn(before,raw)
            (self.folder/name).write_text(raw.replace(before,after),encoding='utf-8')
            with self.subTest(name=name,before=before),self.assertRaises(ValueError):fpga_reports.routed_reports(self.folder)
            (self.folder/name).write_bytes(self.routed[name])
        path=self.folder/'effective_constraints.xdc';path.write_bytes(self.routed[path.name]+b'\nset_false_path -from [all_registers]\n')
        with self.assertRaisesRegex(ValueError,'TIMING_EXCEPTION'):fpga_reports.routed_reports(self.folder)
    def test_repeated_resource_summaries_must_agree(self):
        path=self.folder/'routed_utilization.rpt';raw=self.routed[path.name].decode()
        # Preserve one good row, then contradict only the distribution row.
        position=raw.index('2. Slice Logic Distribution',raw.index('1.1 Summary of Registers by Type')+50)
        bad=raw[:position]+raw[position:].replace('2567','2568')
        self.assertNotEqual(raw,bad);path.write_text(bad,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'CONTRADICTORY_RESOURCE_ROW'):fpga_reports.routed_reports(self.folder)
    def test_real_synthesis_fixture_retains_negative_estimate(self):
        r=fpga_reports.timing(self.raw,'Synthesized',False)
        self.assertEqual(r['setup']['worst_slack_ns'],-5.559)
        self.assertEqual(r['checks']['no_input_delay'],18)
        self.assertEqual(r['checks']['no_output_delay'],17)
        with self.assertRaisesRegex(ValueError,'TIMING_FAILED'):fpga_reports.timing(self.raw,'Synthesized',True)
    def test_headers_clock_inventory_and_partial_reports_rejected(self):
        mutations=[self.raw.replace('Build 6299465','Build 0'),self.raw.replace('basys3_top','other'),
            self.raw.replace('Speed File   : -1','Speed File   : -2'),
            self.raw.replace('10.000          100.000','11.000          100.000'),
            self.raw.replace('checking no_clock (0)','checking no_clock (1)'),
            self.raw.replace('checking no_input_delay (18)','checking no_input_delay (17)'),
            self.raw.replace('report_unconstrained','omitted_scope'),self.raw[:100],self.raw+self.raw]
        for bad in mutations:
            with self.subTest(prefix=bad[:20]),self.assertRaises(ValueError):fpga_reports.timing(bad,'Synthesized',False)
    def test_every_timing_failure_and_zero_endpoints_rejected(self):
        good=self.raw.replace('Synthesized','Routed').replace('-5.559    -4283.602                   1515','1.000        0.000                      0')
        self.assertEqual(fpga_reports.timing(good)['setup']['failing_endpoints'],0)
        for before,after in [('0.045        0.000','-0.001       -0.001'),('4.500        0.000','-0.100       -0.100'),
            ('0                 8369','0                    0'),('0                 8369','9000              8369'),('1.000        0.000','NaN          0.000')]:
            with self.subTest(after=after),self.assertRaises(ValueError):fpga_reports.timing(good.replace(before,after))
    def test_resource_caps_latches_and_missing_memory_rejected(self):
        r=fpga_reports.utilization(self.use,'Synthesized');self.assertEqual(r['Slice LUTs']['used'],4625)
        for before,after in [('4625','99999'),('| Block RAM Tile','| Wrong RAM Tile'),('Register as Latch     |    0','Register as Latch     |    1')]:
            with self.subTest(before=before),self.assertRaises(ValueError):fpga_reports.utilization(self.use.replace(before,after),'Synthesized')
    def test_bitstream_structure_part_sync_and_truncation(self):
        # In-memory format fixture only, never a configuration file or hardware
        # image. The native artifact must independently come from Vivado.
        def field(key,value):return key+len(value).to_bytes(2,'big')+value
        payload=b'\xff'*16+b'\xaa\x99\x55\x66'+b'\0'*100000
        data=b'\0\x09'+bytes.fromhex('0ff00ff00ff00ff000')+b'\0\1'+field(b'a',b'unit\0')+field(b'b',b'7a35tcpg236\0')
        data+=field(b'c',b'2026/11/07\0')+field(b'd',b'20:00:00\0')+b'e'+len(payload).to_bytes(4,'big')+payload
        self.assertEqual(fpga_reports.bitstream(data)['part'],'7a35tcpg236')
        for bad in (data[:7],data[:-1],data+b'x',data.replace(b'7a35tcpg236',b'7a50tcpg236'),data.replace(b'\xaa\x99\x55\x66',b'ABCD')):
            with self.assertRaises(ValueError):fpga_reports.bitstream(bad)


if __name__=='__main__':unittest.main(verbosity=2)
