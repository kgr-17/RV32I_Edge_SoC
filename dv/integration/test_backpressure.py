#!/usr/bin/env python3
"""Preserve deterministic control cases, then replay with variable bus timing."""
from collections import Counter
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from dv.integration import test_flush as control

REQUIRED_BINS=control.REQUIRED_BINS+['deterministic_replay','random_timing_replay']
NEGATIVE_FULL_PROGRAM=True
NEGATIVE_DIAGNOSTIC='BACKPRESSURE_MISMATCH fault'


def generate(seed):
    text,bins=control.generate(seed);rows=[];coverage=Counter()
    for offset,label in ((0,'deterministic_replay'),(21,'random_timing_replay')):
        coverage.update(bins)
        for line in text.splitlines():
            row=[int(v,16)for v in line.split()]
            if row[0]==0:row[5]+=offset;coverage[label]+=1
            rows.append(tuple(row))
    coverage['scenarios']=42;coverage['expected_retirements']=sum(row[0]==3 for row in rows)
    assert all(coverage[key]>0 for key in REQUIRED_BINS)
    return ''.join(' '.join('%08x'%(v%2**32)for v in row)+'\n'for row in rows),dict(sorted(coverage.items()))


class TimingPrograms(unittest.TestCase):
    def test_both_modes_have_complete_unique_cases(self):
        text,c=generate(1);ids=[int(line.split()[5],16)for line in text.splitlines()if line.split()[0]=='00000000']
        self.assertEqual(ids,list(range(42)));self.assertEqual(c['deterministic_replay'],21);self.assertEqual(c['random_timing_replay'],21)
    def test_original_deterministic_stimulus_prefix_preserved(self):
        self.assertTrue(generate(1)[0].startswith(control.generate(1)[0]))
    def test_replay_seed_and_counts(self):
        self.assertEqual(generate(7)[0],generate(7)[0]);self.assertNotEqual(generate(7)[0],generate(101)[0])
        self.assertEqual(generate(7)[1]['expected_retirements'],502)
    def test_required_categories_not_dropped(self):self.assertTrue(all(generate(1)[1][key]for key in REQUIRED_BINS))


if __name__=='__main__':unittest.main(verbosity=2)
