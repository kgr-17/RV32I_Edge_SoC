#!/usr/bin/env python3
"""Behavioral controller tests. Fixtures and disposable Git repos stay project-local."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import harness as h
import report
import verify

SOURCE = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def setUp(self):
        parent = SOURCE / 'build/selftests'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=str(parent))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(h, 'ROOT', self.root).start()
        self.date = patch.object(h, 'today', return_value='2026-10-14').start()
        self.tasks = []
        for tid, deps, gate, optional, priority in (
                ('A', [], False, False, 1), ('B', ['A'], True, False, 2),
                ('F', ['A', 'B'], True, False, 4), ('O', ['B'], False, True, 3)):
            self.tasks.append({'id': tid, 'title': tid, 'description': 'Fixture task',
                'engineering_objective': 'Verify controller invariants', 'depends_on': deps,
                'required_files': ['docs/fixture.md'], 'acceptance_criteria': ['Actual command must pass'],
                'verification_commands': [['{python}', '-c', "print('fixture gate')"]],
                'priority': priority, 'status': 'pending', 'human_approval_required': gate,
                'optional': optional})
        self.plan = {'tasks': self.tasks, 'final_review_task': 'F'}
        self.state = {'schema_version': 2, 'project_status': 'in_progress', 'active': None,
            'daily_claims': {}, 'task_states': {t['id']: 'pending' for t in self.tasks},
            'attempts': {}, 'blocked_reasons': {}, 'receipts': {}, 'owner_reviews': {},
            'enabled_optional_ids': [], 'start_approvals': {}}
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        h.atomic(self.root / '.harness/state.json', self.state)
        (self.root / 'docs/fixture.md').write_text('Fixture deliverable.\n', encoding='utf-8')
        (self.root / '.gitignore').write_text('.harness/lockfile\n.tmp/\n', encoding='utf-8')
        for suffix in ('technical', 'zh-CN'):
            p = self.root / ('docs/daily/2026-10-14_' + suffix + '.md')
            p.parent.mkdir(exist_ok=True)
            p.write_text('Fixture handoff with exact evidence and remaining limitations.\n' * 5, encoding='utf-8')
        for tid in ('A', 'B', 'F', 'O'):
            p = self.root / ('evidence/daily/' + tid + '.md')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('# Fixture acceptance evidence\n' + 'Controller test, not CPU verification.\n' * 6, encoding='utf-8')
        self.git('init', '-b', 'test')
        self.git('config', '--local', 'core.autocrlf', 'false')
        self.commit()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Harness Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-m', 'fixture')

    def persist_plan(self):
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        self.commit()

    def finish(self, tid='A'):
        with contextlib.redirect_stdout(io.StringIO()):
            return h.finish(tid, 'evidence/daily/' + tid + '.md')

    def complete_a(self):
        h.begin('A')
        self.finish()
        self.commit()

    def next_day(self, date='2026-10-15'):
        self.date.return_value = date
        # Daily reports are always required, including resumed tasks.
        for suffix in ('technical', 'zh-CN'):
            (self.root / ('docs/daily/' + date + '_' + suffix + '.md')).write_text(
                'Next day report with test evidence and known limitations.\n' * 5, encoding='utf-8')
        self.commit()

    def test_dependency_enforcement(self):
        with self.assertRaises(h.Stop):
            h.begin('B')
        self.assertEqual(h.candidates(*h.load())[0]['id'], 'A')

    def skip_policy(self,tid='A'):
        plan,state=h.load()
        record={'schema_version':1,'date':h.today(),'task':tid,'action':'skip',
            'owner_instruction':'Skip this task and continue other work.',
            'reason':'Explicit owner acceptance of missing selected verification.',
            'verification_status':'NOT RUN','formal_proof_claim':False,
            'preserved_attempts':state['attempts'].get(tid,0),
            'preserved_receipt':state['receipts'].get(tid)}
        if record['preserved_receipt']:
            record['preserved_receipt_sha256']=hashlib.sha256(h.inside(record['preserved_receipt']).read_bytes()).hexdigest()
        path='evidence/owner_skip_'+tid+'.json';h.atomic(h.inside(path),record)
        policy={'evidence':path,'sha256':hashlib.sha256(h.inside(path).read_bytes()).hexdigest()}
        plan.setdefault('owner_skip_policy',{})[tid]=policy
        h.atomic(h.inside('docs/BACKLOG.json'),plan)
        return path

    def test_owner_skip_preserves_failed_attempt_and_unblocks_dependency_without_pass(self):
        self.tasks[0]['verification_commands']=[['{python}','-c','raise SystemExit(125)']]
        self.persist_plan();h.begin('A')
        with self.assertRaises(h.Stop):self.finish('A')
        _,before=h.load();receipt=before['receipts']['A'];raw=h.inside(receipt).read_bytes()
        self.skip_policy();h.owner_action('skip','A',True)
        plan,state=h.load()
        self.assertEqual(state['task_states']['A'],'skipped');self.assertIsNone(state['active'])
        self.assertEqual(state['attempts']['A'],1);self.assertEqual(h.inside(receipt).read_bytes(),raw)
        self.assertEqual(h.candidates(plan,state)[0]['id'],'B')
        with self.assertRaises(h.Stop):self.finish('A')
        self.assertEqual(h.owner_action('skip','A',True)['action'],'ALREADY_SKIPPED')

    def test_skip_requires_confirmation_and_task_specific_policy(self):
        h.begin('A')
        with self.assertRaises(h.Stop):h.owner_action('skip','A',False)
        with self.assertRaises(h.Stop):h.owner_action('skip','A',True)
        self.assertEqual(h.load()[1]['active'],'A')

    def test_forged_skipped_status_without_owner_record_rejected(self):
        self.state['task_states']['A']='skipped';self.state['active']=None
        h.atomic(h.inside('.harness/state.json'),self.state)
        with self.assertRaises(h.Stop):h.load()

    def test_changed_skip_evidence_rejected(self):
        h.begin('A');path=self.skip_policy();h.owner_action('skip','A',True)
        record=h.read(h.inside(path));record['task']='B';h.atomic(h.inside(path),record)
        with self.assertRaises(h.Stop):h.load()

    def test_skip_cannot_erase_attempts_or_alter_original_failure_receipt(self):
        self.tasks[0]['verification_commands']=[['{python}','-c','raise SystemExit(125)']]
        self.persist_plan();h.begin('A')
        with self.assertRaises(h.Stop):self.finish('A')
        self.skip_policy();h.owner_action('skip','A',True)
        _,state=h.load();state['attempts']['A']=0;h.atomic(h.inside('.harness/state.json'),state)
        with self.assertRaises(h.Stop):h.load()
        state['attempts']['A']=1;h.atomic(h.inside('.harness/state.json'),state)
        receipt=h.inside(state['receipts']['A']);receipt.write_bytes(receipt.read_bytes()+b'\n')
        with self.assertRaises(h.Stop):h.load()

    def test_null_skip_acknowledgment_rejected(self):
        h.begin('A');self.skip_policy();h.owner_action('skip','A',True)
        _,state=h.load();state['owner_skips']['A']=None;h.atomic(h.inside('.harness/state.json'),state)
        with self.assertRaises(h.Stop):h.load()

    def test_skip_cannot_target_another_active_task_or_review_gate(self):
        h.begin('A');self.skip_policy('B')
        with self.assertRaises(h.Stop):h.owner_action('skip','B',True)
        self.assertEqual(h.load()[1]['active'],'A')
        self.complete_a();h.begin('B');self.skip_policy('B')
        with self.assertRaises(h.Stop):h.owner_action('skip','B',True)

    def test_valid_skip_still_requires_successor_and_final_owner_reviews(self):
        h.begin('A');self.skip_policy();h.owner_action('skip','A',True);self.commit()
        h.begin('B');self.finish('B')
        self.assertEqual(h.load()[1]['task_states']['B'],'awaiting_review')
        self.assertEqual(h.candidates(*h.load()),[])
        h.owner_action('approve','B',True);self.commit();h.begin('F');self.finish('F')
        self.assertEqual(h.load()[1]['owner_reviews']['B']['acknowledged_skipped_tasks'],['A'])
        self.assertEqual(h.load()[1]['project_status'],'in_progress')
        h.owner_action('approve','F',True)
        self.assertEqual(h.load()[1]['project_status'],'completed')
        self.assertEqual(h.load()[1]['task_states']['A'],'skipped')
        self.assertEqual(h.load()[1]['owner_reviews']['F']['acknowledged_skipped_tasks'],['A'])

    def test_priority_selection(self):
        self.tasks[1]['depends_on'] = []
        self.tasks[1]['priority'] = 0
        self.persist_plan()
        self.assertEqual(h.candidates(*h.load())[0]['id'], 'B')
        with self.assertRaises(h.Stop):
            h.begin('A')

    def test_failed_verification_blocks_completion(self):
        self.tasks[0]['verification_commands'] = [['{python}', '-c', 'raise SystemExit(1)']]
        self.persist_plan()
        h.begin('A')
        with self.assertRaises(h.Stop):
            self.finish()
        _, state = h.load()
        self.assertEqual(state['task_states']['A'], 'failed')
        self.assertEqual(state['active'], 'A')
        self.assertEqual(h.candidates(*h.load()), [])

    def test_missing_tool_is_not_run(self):
        self.tasks[0]['verification_commands'] = [['intentionally-absent-rv32-test-tool']]
        self.persist_plan()
        h.begin('A')
        with self.assertRaises(h.Stop):
            self.finish()
        _, state = h.load()
        receipt = h.read(h.inside(state['receipts']['A']))
        self.assertEqual(receipt['commands'][0]['status'], 'NOT RUN')
        self.assertIsNone(receipt['commands'][0]['exit_code'])

    def test_missing_input_cannot_finish(self):
        h.begin('A')
        (self.root / 'docs/fixture.md').unlink()
        with self.assertRaises(h.Stop):
            self.finish()

    def test_both_reports_required(self):
        h.begin('A')
        (self.root / 'docs/daily/2026-10-14_zh-CN.md').unlink()
        with self.assertRaises(h.Stop):
            self.finish()
        self.assertEqual(h.load()[1]['attempts']['A'], 0)

    def test_interrupted_execution_recovery(self):
        h.begin('A')
        with patch.object(h, 'run', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.finish()
        _, state = h.load()
        journal = h.read(h.inside(state['receipts']['A']))
        self.assertEqual(journal['stage'], 'running')
        self.assertEqual(h.begin('A')['action'], 'RESUME')
        self.assertEqual(h.load()[1]['attempts']['A'], 1)
        self.finish()
        self.assertEqual(h.load()[1]['attempts']['A'], 2)

    def test_multiple_tasks_same_day_preserve_order_and_no_duplicate_work(self):
        self.complete_a()
        h.begin('B')
        self.assertEqual(h.begin('B')['action'], 'RESUME')
        self.finish('B')
        self.assertEqual(h.load()[1]['daily_tasks']['2026-10-14'], ['A', 'B'])
        self.assertEqual(h.load()[1]['attempts'], {'A': 1, 'B': 1})
        self.assertEqual(len(list((self.root / 'docs/daily').glob('2026-10-14_*.md'))), 2)
        self.assertEqual(self.finish('B')['action'], 'ALREADY_VERIFIED')

    def test_next_task_requires_previous_task_commit(self):
        h.begin('A')
        self.finish()
        with self.assertRaisesRegex(h.Stop, 'clean Git baseline'):
            h.begin('B')
        self.commit()
        self.assertEqual(h.begin('B')['action'], 'BEGIN')

    def test_active_task_cannot_be_skipped_on_same_date(self):
        h.begin('A')
        with self.assertRaisesRegex(h.Stop, 'Recover active task A'):
            h.begin('B')

    def test_three_tasks_can_complete_same_day_with_reviews_and_commits(self):
        self.complete_a()
        h.begin('B')
        self.finish('B')
        self.assertEqual(h.candidates(*h.load()), [])
        with self.assertRaises(h.Stop):
            h.begin('F')
        h.owner_action('approve', 'B', True)  # Fixture owner, never production approval.
        self.commit()
        h.begin('F')
        self.finish('F')
        self.assertEqual(h.load()[1]['daily_tasks']['2026-10-14'], ['A', 'B', 'F'])
        self.assertEqual(h.load()[1]['task_states']['F'], 'awaiting_review')
        h.owner_action('approve', 'F', True)  # Fixture final review.
        self.assertEqual(h.load()[1]['project_status'], 'completed')

    def test_idempotent_begin_and_finish(self):
        h.begin('A')
        self.assertEqual(h.begin('A')['action'], 'RESUME')
        self.finish()
        before = (self.root / '.harness/state.json').read_bytes()
        self.assertEqual(self.finish()['action'], 'ALREADY_VERIFIED')
        self.assertEqual(before, (self.root / '.harness/state.json').read_bytes())

    def prepare_day_exception(self):
        # Preserve the actual old one-time exception as immutable provenance.
        self.date.return_value = '2026-10-23'
        rename = {'A': 'T003', 'B': 'T004'}
        for task in self.tasks:
            task['id'] = rename.get(task['id'], task['id'])
            task['depends_on'] = [rename.get(tid, tid) for tid in task['depends_on']]
        self.state['task_states'] = {t['id']: 'pending' for t in self.tasks}
        self.state['task_states']['T003'] = 'completed'
        self.state['daily_claims']['2026-10-23'] = 'T003'
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        h.atomic(self.root / '.harness/state.json', self.state)
        self.evidence = 'evidence/exception.json'
        h.atomic(self.root / self.evidence, {
            'schema_version': 1, 'date': '2026-10-23', 'task': 'T004', 'previous_task': 'T003',
            'owner_answer': 'Yes—start T004 today',
            'question_item_id': '["request_user_input_async","call_db6019c10ff8475da53c07dfb0dd2c37",0]'})
        self.state['daily_exceptions'] = {'2026-10-23': {
            'task': 'T004', 'evidence': self.evidence,
            'sha256': hashlib.sha256((self.root / self.evidence).read_bytes()).hexdigest()}}
        h.atomic(self.root / '.harness/state.json', self.state)
        h.atomic_text(self.root / 'evidence/daily/T004.md', 'Explicit exception acceptance evidence.\n' * 8)
        self.next_day('2026-10-23')

    def test_legacy_claim_and_exception_preserved_through_resume_and_finish(self):
        self.prepare_day_exception()
        h.begin('T004')
        self.assertEqual(h.begin('T004')['action'], 'RESUME')
        self.finish('T004')
        state = h.load()[1]
        self.assertEqual(state['daily_claims']['2026-10-23'], 'T003')
        self.assertEqual(state['daily_exceptions']['2026-10-23']['task'], 'T004')
        self.assertEqual(state['attempts']['T004'], 1)
        self.assertEqual(state['schema_version'], 3)
        self.assertEqual(state['daily_tasks']['2026-10-23'], ['T003', 'T004'])

    def test_legacy_exception_wrong_binding_and_missing_evidence_rejected(self):
        self.prepare_day_exception()
        original = h.read(self.root / self.evidence)
        for key, value in (('date', '2026-10-24'), ('task', 'F'), ('previous_task', 'F'),
                           ('owner_answer', 'assumed'), ('question_item_id', 'unrelated')):
            with self.subTest(key=key):
                h.atomic(self.root / self.evidence, {**original, key: value})
                self.commit()
                with self.assertRaises(h.Stop):
                    h.load()
        h.atomic(self.root / self.evidence, original)
        (self.root / self.evidence).unlink()
        with self.assertRaises(OSError):
            h.load()

    def test_exception_evidence_tampering_detected(self):
        self.prepare_day_exception()
        h.begin('T004')
        value = h.read(self.root / self.evidence)
        h.atomic(self.root / self.evidence, {**value, 'extra': 'changed'})
        with self.assertRaises(h.Stop):
            h.load()

    def test_legacy_exception_does_not_restrict_later_days(self):
        self.prepare_day_exception()
        self.next_day('2026-10-24')
        h.begin('T004')
        self.finish('T004')
        state = h.load()[1]
        self.assertEqual(state['daily_tasks']['2026-10-24'], ['T004'])
        self.assertEqual(state['daily_claims'], {'2026-10-23': 'T003'})

    def test_resume_across_day_records_history_without_blocking_next_task(self):
        h.begin('A')
        self.next_day()
        h.begin('A')
        self.finish()
        self.commit()
        h.begin('B')
        state = h.load()[1]
        self.assertEqual(state['daily_tasks']['2026-10-14'], ['A'])
        self.assertEqual(state['daily_tasks']['2026-10-15'], ['A', 'B'])

    def test_invalid_history_and_lost_legacy_claim_rejected(self):
        self.prepare_day_exception()
        h.begin('T004')
        original = h.read(self.root / '.harness/state.json')
        for value in ({'2026-10-23': ['T004']}, {'2026-10-23': ['T003', 'T004', 'T004']},
                      {'2026-10-23': ['T003', 'T004', 'UNKNOWN']},
                      {'2026-10-23': 'T003'}, {'bad-date': ['T003']}):
            with self.subTest(value=value):
                h.atomic(self.root / '.harness/state.json', {**original, 'daily_tasks': value})
                with self.assertRaises((h.Stop, ValueError)):
                    h.load()

    def test_readiness_not_blocked_by_legacy_date_claim(self):
        self.prepare_day_exception()
        result = h.daily(True)
        self.assertIsNone(result['daily_task_limit'])
        self.assertEqual(result['tasks_today'], ['T003', 'T004'])
        self.assertEqual(result['next']['id'], 'T004')

    def test_owner_review_gate(self):
        self.complete_a()
        self.next_day()
        h.begin('B')
        self.finish('B')
        self.assertEqual(h.load()[1]['task_states']['B'], 'awaiting_review')
        self.assertEqual(h.candidates(*h.load()), [])
        with self.assertRaises(h.Stop):
            h.owner_action('approve', 'B', False)
        h.owner_action('approve', 'B', True)  # Fixture owner; production agent never approves.
        self.assertEqual(h.candidates(*h.load())[0]['id'], 'F')

    def test_three_attempt_budget_and_failure_preservation(self):
        self.tasks[0]['verification_commands'] = [['{python}', '-c', 'raise SystemExit(1)']]
        self.persist_plan()
        h.begin('A')
        logs = []
        for _ in range(3):
            with self.assertRaises(h.Stop):
                self.finish()
            logs.append(h.load()[1]['receipts']['A'])
        self.assertEqual(len(set(logs)), 3)
        self.assertTrue(all(h.inside(p).is_file() for p in logs))
        self.assertEqual(h.load()[1]['task_states']['A'], 'blocked')
        with self.assertRaises(h.Stop):
            self.finish()
        with self.assertRaises(h.Stop):
            h.owner_action('reopen', 'A', False)
        h.owner_action('reopen', 'A', True)
        self.tasks[0]['verification_commands'] = [['{python}', '-c', "print('corrected fixture')"]]
        self.persist_plan()
        self.next_day()
        h.begin('A')
        self.finish()
        self.assertTrue(all(h.inside(p).is_file() for p in logs))
        self.assertNotIn(h.load()[1]['receipts']['A'], logs)

    def test_preexecution_authorization(self):
        self.tasks[0]['start_approval_required'] = True
        self.persist_plan()
        with self.assertRaises(h.Stop):
            h.begin('A')
        with self.assertRaises(h.Stop):
            h.owner_action('authorize', 'A', False)
        h.owner_action('authorize', 'A', True)
        self.commit()
        self.assertEqual(h.begin('A')['action'], 'BEGIN')

    def test_terminal_completion_ignores_disabled_optional(self):
        self.state['task_states'].update(A='completed', B='completed', F='awaiting_review')
        h.atomic(self.root / '.harness/state.json', self.state)
        h.owner_action('approve', 'F', True)
        self.assertEqual(h.load()[1]['project_status'], 'completed')
        self.assertEqual(h.candidates(*h.load()), [])
        with self.assertRaises(h.Stop):
            h.begin('O')

    def test_final_review_cannot_skip_mandatory_work(self):
        self.tasks[2]['depends_on'] = ['B']
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        with self.assertRaises(h.Stop):
            h.load()

    def test_dependency_cycle_rejected(self):
        self.tasks[0]['depends_on'] = ['B']
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        with self.assertRaises(h.Stop):
            h.load()

    def test_dirty_worktree_protected(self):
        (self.root / 'user-work.txt').write_text('Preserve me', encoding='utf-8')
        with self.assertRaises(h.Stop):
            h.begin('A')
        self.assertEqual((self.root / 'user-work.txt').read_text(), 'Preserve me')

    def test_path_escape_and_link_rejected(self):
        with self.assertRaises(h.Stop):
            h.inside('../outside')
        with self.assertRaises(h.Stop):
            h.inside('C:/outside')
        # Path.resolve also rejects external junction/symlink destinations.

    def test_concurrent_controller_rejected(self):
        script = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv.pop(1)); "
                  "import harness; harness.ROOT=Path(sys.argv.pop(1)); sys.exit(harness.main())")
        with h.lock():
            result = h.run(['{python}', '-B', '-c', script, str(SOURCE / 'scripts'),
                            str(self.root), 'begin', 'A'])
        self.assertEqual(result['exit_code'], 2)
        self.assertIn('state lock', result['stderr'])

    def test_unattended_refused_and_handoff_loaded(self):
        with self.assertRaises(h.Stop):
            h.daily(False)
        result = h.daily(True)
        self.assertIn('Fixture handoff', result['handoff'])
        self.assertEqual(result['next']['id'], 'A')

    def test_report_append_idempotence_and_date_preservation(self):
        entry = {'technical': 'Detailed engineering evidence and known limitations.\n' * 6,
                 'zh-CN': '工程验证报告：只记录实际证据，并说明未完成事项和下一步。\n' * 8}
        paths = report.generate(entry)
        before = [h.inside(p).read_bytes() for p in paths]
        report.generate(entry)
        self.assertEqual(before, [h.inside(p).read_bytes() for p in paths])
        report.generate({**entry, 'technical': entry['technical'] + 'New finding.'})
        self.assertIn('New finding.', h.inside(paths[0]).read_text(encoding='utf-8'))
        self.assertIn('Fixture handoff', h.inside(paths[0]).read_text(encoding='utf-8'))
        self.assertEqual(len(list((self.root / 'docs/daily').glob('2026-10-14_*.md'))), 2)
        previous = [h.inside(p).read_bytes() for p in paths]
        self.date.return_value = '2026-10-15'
        report.generate(entry)
        self.assertEqual(previous, [h.inside(p).read_bytes() for p in paths])
        self.assertEqual(len(list((self.root / 'docs/daily').glob('2026-10-15_*.md'))), 2)

    def test_unregistered_checks_and_missing_inputs_not_run(self):
        h.atomic(self.root / '.harness/checks.json', {})
        with patch.object(sys, 'argv', ['verify.py', 'lint']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.main(), 125)
        h.atomic(self.root / '.harness/checks.json', {'lint': {
            'inputs': ['missing.sv'], 'commands': [['{python}', '-c', 'raise SystemExit(0)']]}})
        with patch.object(sys, 'argv', ['verify.py', 'lint']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.main(), 125)

    def test_optional_enable_and_terminal_review(self):
        self.state['task_states'].update(A='completed', B='completed')
        h.atomic(self.root / '.harness/state.json', self.state)
        self.assertEqual(h.candidates(*h.load())[0]['id'], 'F')
        with self.assertRaises(h.Stop):
            h.owner_action('enable', 'O', False)
        h.owner_action('enable', 'O', True)
        self.assertEqual(h.candidates(*h.load())[0]['id'], 'O')

    def test_runtime_cannot_bypass_dependencies(self):
        self.state['task_states']['B'] = 'completed'
        h.atomic(self.root / '.harness/state.json', self.state)
        with self.assertRaises(h.Stop):
            h.load()

    def test_state_recovers_stale_backlog_projection(self):
        h.begin('A')
        plan, state = h.load()
        self.tasks[0]['status'] = 'pending'
        h.atomic(self.root / 'docs/BACKLOG.json', self.plan)
        plan, state = h.load()
        self.assertEqual(h.status(state, plan['tasks'][0]), 'in_progress')
        h.save(plan, state)
        self.assertEqual(h.read(self.root / 'docs/BACKLOG.json')['tasks'][0]['status'], 'in_progress')

    def test_full_output_preserved_and_command_not_shell(self):
        record = h.run(['{python}', '-c', "print('x' * 14000); print('literal $(no shell)')"])
        self.assertEqual(record['status'], 'PASS')
        self.assertGreater(len(record['stdout']), 14000)
        self.assertIn('$(no shell)', record['stdout'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
