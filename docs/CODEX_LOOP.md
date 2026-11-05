# Sequential attended engineering loop

The harness selects and verifies work; Codex performs the engineering in an
attended session. Nothing here installs or invokes a scheduler or a model loop.

On 2026-10-23 the owner removed the daily task quota and stop-after-success rule.
An attended session may complete multiple tasks sequentially. Keep exactly one
active task, verify/report/commit it, then continue with the first dependency-ready
task without waiting for a new calendar day or asking for a daily exception.
Stop for owner review/authorization, a genuine blocker, exhausted verification
budget, project completion, the owner's stop request or session budget limits.
Provenance: `evidence/owner_reviews/workflow-policy-2026-10-23.json`.

The earlier T004 exception and original claims remain historical evidence in
`daily_exceptions`/`daily_claims`. They are no longer quota gates. State schema 3
adds `daily_tasks`, an ordered list of distinct tasks worked per date. Older
schema-2 state can be read; the next state save copies its claims/exceptions into
that history without changing them. The retired `--owner-day-exception` begin
flag is no longer needed or accepted. All task dependencies, review gates,
clean-baseline protection and three-attempt checks remain enforced.

## Start and recover

Run from the official workspace:

```powershell
python -B scripts/harness.py daily --supervised
python -B scripts/harness.py validate
python -B scripts/harness.py status
python -B scripts/harness.py next
git status --short --branch
```

Read the latest technical handoff, AGENTS.md, architecture, verification plan,
backlog, boundary document and persistent state. The daily command loads and
prints the handoff; an agent must actually read it before touching RTL/testbenches.
Inspect all existing diffs. New tasks require a clean Git baseline. An interrupted
active task is resumed with `begin SAME_ID`, including on a later day; do not
discard its changes or skip to another task. Resume adds that task to today's
participation list once; repeated resumes do not create duplicate entries.

If no active task exists, begin only the first dependency-ready task:

```powershell
python -B scripts/harness.py begin T002
```

Priority then ID determines selection. Dependencies must be completed. A required
blocked/review task conservatively holds other work. Disabled optional tasks do
not block the mandatory project. Report/history dates use America/Los_Angeles,
never the host's implicit timezone. There is no calendar task cap and no
production date override.

## Implement, verify, report, commit, continue

Implement only the selected task and its directly required tests/documentation.
Preserve independent oracles, assertions, seeds and requirements. Never lower a
gate to make it pass. Run each specified command and save substantive evidence in
`evidence/daily/ID.md`, including acceptance evidence and limitations.

Prepare both dated reports before finish. `scripts/report.py --entry PATH` accepts
a project-local JSON object with substantive `technical` and `zh-CN` strings.
It appends same-day findings, preserves prior entries/dates and skips duplicate
entries. Exactly two files are created under `docs/daily/` per report date.

```powershell
python -B scripts/report.py --entry evidence/report_entries/your-entry.json
python -B scripts/harness.py finish T002 --evidence evidence/daily/T002.md
```

Finish checks required files and both reports, reserves an attempt BEFORE running
commands, and records full exact argv/stdout/stderr/exit codes in timestamped JSON
receipts under `evidence/runs/ID/`. Each completed command is persisted immediately.
A crash leaves an active task and a running journal rather than a false pass.
The receipt records Python version, starting Git commit, seed/waveform fields;
task evidence must include applicable tool versions, actual seed and waveforms.
Preflight records current tool discovery and available version output.

Required command exits must all be zero, including diff whitespace checks. Exit
125/127 or an unavailable executable is NOT RUN, never PASS. There are at most
three verification executions per task, conservatively bounding correction
attempts even across days. Logs survive retries and owner reopen. Failure remains
active (`failed`) until corrected or explicitly blocked; the third failure blocks.

```powershell
python -B scripts/harness.py block T002 --reason 'Concrete diagnosis and required owner action'
```

After gates, append final results to the same two reports, review/stage only task
files, run `git diff --cached --check` and make a local commit. Record the
commit identifier in the handoff. A post-commit report update may require a small
documentation commit; do not amend/reset user history. Inspect status/next and
continue with the next ready task from a clean Git baseline. Do not start work
across a pending review/execution gate or leave failed active work behind.
Append each task's outcome to the same two dated reports; do not create another
pair for each task. The daily entrypoint still prepares a single attended session,
not an autonomous process that runs itself in the background.

## State and approvals

Task states: pending, in_progress, passed, failed, blocked, awaiting_review,
completed, skipped. `skipped` is an owner-authorized scope exception, never PASS.
Only task-specific BACKLOG.owner_skip_policy and matching immutable owner evidence
can release that dependency. Current authorization covers T023 only; preserve its
attempts/NOT RUN receipts. No review/execution gate can be skipped with this command.
`passed` is reserved for recoverable pre-finalization states; ordinary
success transitions to completed or awaiting_review. The authoritative atomic
file is `.harness/state.json`; BACKLOG statuses are its repairable mirror. A crash
between writes cannot promote a task based on stale backlog data. State updates
are guarded by an exclusive Windows/POSIX lock. They do not constrain arbitrary
programs or authenticate human identities.

Only the owner may run these acknowledgments after inspecting evidence:

```powershell
python -B scripts/harness.py approve T002 --confirm-owner-review
python -B scripts/harness.py authorize T043 --confirm-owner-review
python -B scripts/harness.py reopen TASK_ID --confirm-owner-review
python -B scripts/harness.py enable OPTIONAL_ID --confirm-owner-review
```

Approve closes a verified review gate. Authorize grants a task-specific execution
gate before significant Vivado/ASIC operations or physical programming. Reopen
requires diagnosis, resets the attempt budget and preserves the current daily
history and old receipts. It must not be used to evade verification limits. These
flags are process rules; human review is still essential for semantic correctness.

The final T040 owner gate depends directly on EVERY mandatory task. The project
becomes completed only after all mandatory tasks complete or have an explicit
validated owner skip, and the final owner review completes with those skips
disclosed. Owner review records retain acknowledged_skipped_tasks separately.
Completed projects refuse new implementation, including optional work; no infinite
in-process loop exists. Daily reporting/status may continue without implementation.

## Scheduling readiness

The manual daily entrypoint is ready:

```powershell
Set-Location C:\RV32I_Edge_SoC
python -B scripts/harness.py daily --supervised
```

`scripts/daily.ps1` additionally prints the daily prompt and Git status. Both are
for operator-attended use. `daily` without `--supervised` refuses execution. This
is a deliberate guard, not proof that a caller is a human.

No host scheduler or Codex automation has been installed or enabled. This session
has unrestricted permissions; unattended operation is not authorized until actual
sandbox and approval controls are configured. After that, the owner must choose
working days/time/timezone and explicitly authorize scheduling. A future adapter
must use this persistent project, preserve state across runs, execute one active
task at a time, respect review/terminal holds and explicit run budgets, and produce
both reports even when blocked. Removing the calendar quota does not authorize
such an adapter or unlimited unattended execution.

## Bounded runtime growth (T015, 2026-11-02)

The integrated pipeline exceeded the old 45-second synthesis allowance while
still mapping logic, so the first attempt correctly failed TIMEOUT. New per-design
manifest timeout_seconds defaults to the original 45 and is validated <=120;
only rv32_pipeline_cpu currently uses 120. The process runner has the same finite
120-second maximum and retains Windows Job/POSIX process-tree cleanup. Existing
simulator/version and intentional-hang timeouts are unchanged. TIMEOUT never passes.

Registered composite checks may set timeout_seconds <=600; lint and toolchain-rtl
use 600 because growing sequential probe lists exceed the former 300 aggregate.
Both the outer harness and inner verify child honor that same declared ceiling.
Other commands still default to 300. Invalid/unbounded budgets are rejected.
This allocates compute time; it does not suppress diagnostics, remove any check,
alter the three-attempt task limit, change actual sandbox permissions or enable
unattended work. New policy and actual descendant-kill tests must pass after
runner changes. Original timeout logs/inputs remain preserved.
Do not assume availability of a particular Codex scheduling feature or launch a
full-access CLI to bypass restrictions. Use the manual workflow until verified.

T024 observed runtime adjustment (2026-11-04): the reference-core probe completed
warning-free synthesis/DRC and the exact marker but missed the45-second process
deadline. Its first attempt remains TIMEOUT/FAIL. Only rv32_reference_core now
uses90 seconds, under the existing120-second per-design maximum; executable
pipeline CPU stays120, other probes default45, negatives and composite ceilings
are unchanged. This is bounded tool compute time, not a hardware timing or
functional-check waiver. Retry all required task gates and retain the first log.
