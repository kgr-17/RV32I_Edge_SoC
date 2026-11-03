#!/usr/bin/env python3
"""Bounded aggregate selection; functional failure/timeout guards remain required."""
from unittest import mock
import unittest
import harness


class BudgetTests(unittest.TestCase):
    def test_default_unchanged(self):
        self.assertEqual(harness.execution_timeout(['git','--version']),300)
    def test_registered_composite_budget(self):
        with mock.patch.object(harness,'read',return_value={'lint':{'timeout_seconds':600}}):
            self.assertEqual(harness.execution_timeout(['python','-B','scripts/verify.py','lint']),600)
    def test_override_for_child_uses_same_bound(self):
        self.assertEqual(harness.execution_timeout(['python','-B','scripts/rtl_checks.py','lint'],600),600)
    def test_unbounded_or_invalid_rejected(self):
        for value in (0,-1,True,601,float('inf'),'600'):
            with self.assertRaises(harness.Stop):harness.execution_timeout(['git'],value)
    def test_bad_registry_budget_rejected(self):
        with mock.patch.object(harness,'read',return_value={'lint':{'timeout_seconds':601}}):
            with self.assertRaises(harness.Stop):harness.execution_timeout(['python','-B','scripts/verify.py','lint'])


if __name__=='__main__':unittest.main(verbosity=2)
