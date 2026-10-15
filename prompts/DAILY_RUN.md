# Attended daily engineering session

Continue the existing project at `C:\RV32I_Edge_SoC`. Do not create a separate
Vivado project or rely on chat memory. Work on exactly one primary task.

1. Read AGENTS.md, the latest technical handoff, docs/ENVIRONMENT_BOUNDARY.md,
   docs/ARCH_SPEC.md, docs/VERIFICATION_PLAN.md, docs/BACKLOG.json, and state.
2. Inspect actual runtime sandbox/approval settings. Report unrestricted access
   and do not run unattended automation. Keep all writes inside the project.
3. Run `python -B scripts/harness.py daily --supervised`, `validate`, `status`,
   `next`, and `git status --short --branch`. Read the returned handoff content.
4. Recover an active task with `begin SAME_ID`. Do not skip interrupted work or
   overwrite unknown diffs. Otherwise start only the first eligible task and
   only if today's quota is unused and the baseline is clean.
5. Inspect specifications and task acceptance. Implement only the selected task
   and its required independent tests/docs. Do not self-approve owner gates.
6. Run real required gates. Save exact commands, outputs, exit codes, versions,
   replay seeds, waveform paths, starting Git hash, failures and diagnosis in
   evidence/daily/ID.md and receipts. Missing tools are NOT RUN. Maximum three
   bounded verification/correction attempts; no weakening tests or expectations.
7. Create/update exactly docs/daily/YYYY-MM-DD_technical.md (English) and
   YYYY-MM-DD_zh-CN.md (Simplified Chinese), dated America/Los_Angeles. Include all
   handoff/review requirements even if blocked; retain earlier same-day findings.
   Use scripts/report.py with a project-local JSON entry, or append carefully.
8. Run `finish ID --evidence evidence/daily/ID.md`. On unresolved failure, save
   diagnosis with `block`; do not claim pass. Update the two reports with results.
9. Inspect/stage only task files; run `git diff --cached --check`; commit locally
   and record the commit hash. Never push or alter original functionality without
   inspection and recoverability. Stop after this task; no second implementation.

If review or execution authorization is pending, show the concrete decision and
evidence to the owner. No source deletion, downloads/installations, hardware
programming or scheduler changes without the required owner authorization.
Completed project status means no further implementation work.

Final response: selected task/status, PASS/FAIL/NOT RUN evidence, commit, sandbox
limitation, next task, report links and specific owner actions. Do not imply that
simulation proves FPGA timing, board behavior or ASIC signoff.
