#!/usr/bin/env python3
"""Freshness, failure propagation and source-binding policy tests."""
import copy
import datetime as dt
import json
import sys
import unittest
from closure_checks import passed_prefix,metadata_objects,validate_tool


class ClosurePolicyTests(unittest.TestCase):
    def setUp(self):
        self.commands=[['{python}','-B','scripts/verify.py','regress']]
        self.records=[dict(argv=[sys.executable,'-B','scripts/verify.py','regress'],status='PASS',exit_code=0)]
        self.since=dt.datetime(2026,11,4,tzinfo=dt.timezone.utc)
        self.run=dict(status='PASS',started_utc='20261104T010000000000Z',checks=[dict(status='PASS')],
                      pins={'vivado_version':'2025.2'},source_sha256={'rtl.sv':'right'})

    def test_current_complete_exact_command_set(self):
        passed_prefix(self.records,self.commands)
        for rows in ([],self.records*2,[{**self.records[0],'status':'NOT RUN','exit_code':125}],
                     [{**self.records[0],'exit_code':1}],[{**self.records[0],'argv':['other']} ]):
            with self.assertRaises(ValueError):passed_prefix(rows,self.commands)

    def test_older_pass_cannot_replace_current_failed_or_empty_record(self):
        for change in ({'status':'FAIL'},{'status':'NOT RUN'},{'checks':[]},
                       {'checks':[{'status':'FAIL'}]},{'started_utc':'20261103T010000000000Z'}):
            with self.assertRaises(ValueError):validate_tool({**self.run,**change},self.since,{'vivado_version':'2025.2'},lambda f:'right')

    def test_source_or_tool_drift_rejected(self):
        validate_tool(self.run,self.since,{'vivado_version':'2025.2'},lambda f:'right')
        with self.assertRaises(ValueError):validate_tool(self.run,self.since,{'vivado_version':'2025.2'},lambda f:'changed')
        with self.assertRaises(ValueError):validate_tool(self.run,self.since,{'vivado_version':'different'},lambda f:'right')

    def test_memory_model_schema_requires_real_tests_and_all_four_negative_controls(self):
        run=dict(profile='memory-model',status='PASS',exit_code=0,tests=11,failures=0,errors=0,skipped=0,
                 source_drift=False,stamp='20261104T010000000000Z',source_sha256={'model.py':'right'},
                 directed_defects_rejected=['EarlyStore','MovingSnapshot','ReplacementAcceptance','IgnoredReset'],stress=[{}]*12)
        validate_tool(run,self.since,{},lambda f:'right')
        for changed in ({'tests':0},{'skipped':1},{'source_drift':True},{'directed_defects_rejected':['EarlyStore']}):
            with self.assertRaises(ValueError):validate_tool({**run,**changed},self.since,{},lambda f:'right')

    def test_nested_json_metadata_is_exactly_decoded(self):
        row={'argv':['tool'],'stdout':json.dumps({'status':'PASS','evidence':'evidence/toolchain_runs/fresh.json'})}
        self.assertEqual(metadata_objects(json.dumps(row)),[row])
        self.assertEqual(metadata_objects(json.dumps(row)+'\n'+json.dumps(row)),[row,row])
        self.assertEqual(metadata_objects('not metadata\n'),[])


if __name__=='__main__':unittest.main(verbosity=2)
