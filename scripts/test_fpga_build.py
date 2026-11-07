"""Input/output/owner-workflow policy checks; no EDA execution or owner commands."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import fpga_build
import harness


class FpgaBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=harness.inside('build/T030');base.mkdir(parents=True,exist_ok=True)
        cls.base=Path(tempfile.mkdtemp(prefix='policy-',dir=base)) # retained evidence
    def test_config_contract_rejects_drift_and_missing_inputs(self):
        good=fpga_build.load_config()
        for key,value in [('schema_version',True),('part','xc7a100tcsg324-1'),('top','other'),('clock_period_ns',11),('clock_period_ns',True),
                ('vivado_version','2026.1'),('rtl_sources',[]),('constraints',[]),('memory_files','bad'),('rtl_sources',['missing.sv']),
                ('rtl_sources',['fpga/basys3/top.sv','fpga/basys3/top.sv'])]:
            bad=copy.deepcopy(good);bad[key]=value
            with self.subTest(key=key,value=value),mock.patch.object(harness,'read',return_value=bad):
                with self.assertRaises((ValueError,harness.Stop)):fpga_build.load_config()
    def test_memory_basename_alias(self):
        good=fpga_build.load_config();paths=[]
        for name in ('a','b'):
            folder=self.base/name;folder.mkdir();p=folder/'same.mem';p.write_bytes(b'00000000\n');paths.append(p.relative_to(harness.ROOT).as_posix())
        good['memory_files']=paths
        with mock.patch.object(harness,'read',return_value=good):
            with self.assertRaisesRegex(ValueError,'BASENAME_ALIAS'):fpga_build.load_config()
    def test_plan_has_hashed_inputs_and_no_build_output(self):
        job,record=fpga_build.prepare_job(self.base/'plan')
        self.assertTrue(job.is_file());self.assertFalse((job.parent/'artifacts').exists());self.assertTrue(record['source_sha256'])
        self.assertIn('mode\tplan\n',job.read_text());self.assertIn('authorization\tnone\n',job.read_text())
        with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):fpga_build.prepare_job(job.parent)
    def test_forbidden_output_and_existing_content_preserved(self):
        for output in (harness.inside('build'),harness.inside('docs/T030-never-create')):
            with self.assertRaisesRegex(ValueError,'OUTSIDE_BUILD'):fpga_build.prepare_job(output)
        existing=self.base/'retained';existing.mkdir();sentinel=existing/'owner.txt';sentinel.write_bytes(b'retain exactly\n')
        with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):fpga_build.prepare_job(existing)
        self.assertEqual(sentinel.read_bytes(),b'retain exactly\n');self.assertFalse(harness.inside('docs/T030-never-create').exists())
    def test_implementation_checkpoint_required_and_no_fake_artifact(self):
        with self.assertRaisesRegex(ValueError,'CHECKPOINT_REQUIRED'):fpga_build.prepare_job(self.base/'no-checkpoint',stage='impl')
        self.assertFalse((self.base/'no-checkpoint').exists())
    def test_owner_policy_in_memory_only_and_real_execution_rejected(self):
        config=fpga_build.load_config();state={'active':'T043','start_approvals':{'T043':{}},'task_states':{k:'completed' for k in ('T031','T044','T045')},'owner_reviews':{'T044':{}}}
        with self.assertRaises(harness.Stop):fpga_build.check_execution(config,state)
        config['design_scope']='integrated_soc';fpga_build.check_execution(config,state) # pure predicate, no write/build
        for key in ('active','start_approvals','owner_reviews'):
            bad=copy.deepcopy(state);bad[key]=None if key=='active' else {}
            with self.assertRaises(harness.Stop):fpga_build.check_execution(config,bad)
        output=self.base/'unauthorized'
        with self.assertRaisesRegex(harness.Stop,'OWNER_AUTH_REQUIRED'):fpga_build.prepare_job(output,mode='execute')
        self.assertFalse(output.exists())


if __name__=='__main__':unittest.main(verbosity=2)
