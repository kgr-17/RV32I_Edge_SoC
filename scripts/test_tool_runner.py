#!/usr/bin/env python3
"""Exercise real subprocess success, failure and descendant timeout cleanup."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
import harness
import tool_runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        base = harness.inside('build/tool_runner_tests')
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=str(base))
        self.cwd = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def python(self, code, timeout=5):
        return tool_runner.run([sys.executable, '-B', '-c', code], self.cwd, timeout)

    def test_success_and_unicode(self):
        result = self.python("print('PASS \\u5de5\\u7a0b')")
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('\u5de5\u7a0b', result['stdout'])

    def test_nonzero_exit_and_stderr(self):
        result = self.python("import sys; print('intentional', file=sys.stderr); sys.exit(7)")
        self.assertEqual(result['exit_code'], 7)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('intentional', result['stderr'])

    def test_missing_executable_not_run(self):
        result = tool_runner.run([str(self.cwd / 'missing_tool.exe')], self.cwd, 5)
        self.assertEqual(result['exit_code'], 125)
        self.assertEqual(result['status'], 'NOT RUN')

    def test_child_environment_paths(self):
        result = self.python("import os,json; print(json.dumps({key:os.environ[key] for key in ('TMP','TEMP','APPDATA','LOCALAPPDATA','USERPROFILE')}))")
        import json
        for path in json.loads(result['stdout']).values():
            self.assertTrue(Path(path).resolve().is_relative_to(harness.ROOT))

    def test_timeout_kills_descendant(self):
        marker = self.cwd / 'descendant_survived.txt'
        child_code = "import time; from pathlib import Path; time.sleep(1.5); Path(" + repr(str(marker)) + ").write_text('bad')"
        parent_code = ("import subprocess,sys,time; subprocess.Popen([sys.executable,'-B','-c'," + repr(child_code) +
                       "]); print('DESCENDANT_STARTED',flush=True); time.sleep(30)")
        result = self.python(parent_code, timeout=1)
        self.assertIn('DESCENDANT_STARTED', result['stdout'])
        self.assertEqual(result['status'], 'TIMEOUT')
        time.sleep(1)
        self.assertFalse(marker.exists(), 'Timed-out descendant survived its job/process group')

    def test_cwd_escape_and_unbounded_timeout_rejected(self):
        with self.assertRaises(harness.Stop):
            tool_runner.run([sys.executable, '--version'], harness.ROOT.parent)
        with self.assertRaises(ValueError):
            self.python('pass', timeout=61)


if __name__ == '__main__':
    unittest.main(verbosity=2)
