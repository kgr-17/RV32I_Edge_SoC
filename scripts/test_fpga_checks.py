"""Exercise provenance failure cases in a private fixture root, without EDA."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import fpga_checks
import harness


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        base=harness.inside('build/T043/policy-tests');base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=str(base));self.root=Path(self.temp.name)
        self.patch=mock.patch.object(harness,'ROOT',self.root);self.patch.start()
        self.source=self.root/'rtl/subject.sv';self.source.parent.mkdir();self.source.write_bytes(b'fixture source\n')
        self.artifact=self.root/'build/checkpoint';self.artifact.parent.mkdir();self.artifact.write_bytes(b'policy fixture, not DCP\n')
        self.name='evidence/toolchain_runs/fpga-synth-fixture.json'
        self.path=harness.inside(self.name);self.path.parent.mkdir(parents=True)
        self.run={'profile':'fpga-synth','status':'PASS','checks':[{'status':'PASS'}],
            'attempt':1,'attempt_journal':'evidence/runs/T043/current.json','base_commit':'fixture',
            'started_utc':'20261108T030100000000Z','source_sha256':{'rtl/subject.sv':fpga_checks.sha(self.source)},
            'artifacts':{'build/checkpoint':fpga_checks.sha(self.artifact)}}
        self.journal={'attempt':1,'git_commit':'fixture','commands':[{'started_utc':'2026-11-08T03:00:00+00:00',
            'stdout':json.dumps({'argv':['python','-B','scripts/fpga_checks.py','synth'],
                'status':'PASS','exit_code':0,'stdout':json.dumps({'evidence':self.name})})}]}
        self.save(self.run)
    def tearDown(self):self.patch.stop();self.temp.cleanup()
    def save(self,r):self.path.write_text(json.dumps(r),encoding='utf-8')
    def prior(self):return fpga_checks.prior_tool(self.journal,0,'fpga-synth','evidence/runs/T043/current.json')
    def test_current_receipt_bound(self):self.assertEqual(self.prior()[1],self.run)
    def test_critical_diagnostics_never_pass_native_success(self):
        record={'status':'PASS','exit_code':0,'stdout':'DONE\n','stderr':''}
        self.assertTrue(fpga_checks.native_success(record,'DONE'))
        for channel in ('stdout','stderr'):
            bad=copy.deepcopy(record);bad[channel]+='CRITICAL WARNING: deliberate policy fixture\n'
            self.assertFalse(fpga_checks.native_success(bad,'DONE'))
    def test_failed_stale_other_attempt_and_other_journal_rejected(self):
        for key,value in [('status','FAIL'),('checks',[]),('attempt',0),('attempt_journal','old.json'),
            ('base_commit','other'),('started_utc','20261108T020000000000Z')]:
            bad=copy.deepcopy(self.run);bad[key]=value;self.save(bad)
            with self.subTest(key=key),self.assertRaises(ValueError):self.prior()
    def test_source_and_checkpoint_drift_rejected(self):
        for p in (self.source,self.artifact):
            old=p.read_bytes();p.write_bytes(b'changed')
            with self.assertRaises(ValueError):self.prior()
            p.write_bytes(old)
    def test_missing_extra_or_wrong_location_receipt_rejected(self):
        for data in ({},[{'evidence':self.name},{'evidence':self.name}],{'evidence':'build/fake.json'}):
            self.journal['commands'][0]['stdout']=json.dumps(data)
            with self.assertRaises(ValueError):self.prior()
    def test_missing_or_reordered_native_stage_rejected(self):
        for run in ({'jobs':[],'commands':[]},{'jobs':[{'stage':'route'}],'commands':[{}]}):
            with self.assertRaisesRegex(ValueError,'STAGE_INVENTORY'):fpga_checks.validate_chain(run,['synth'])


if __name__=='__main__':unittest.main(verbosity=2)
