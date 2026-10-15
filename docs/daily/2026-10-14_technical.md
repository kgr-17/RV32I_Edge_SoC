<!-- entry:c804ab0a8c2f92f56f89e2ad87fb611e2ed00de0fa5e273044b1b4905f18fdd8 -->

# Technical engineering handoff — 2026-10-14 (America/Los_Angeles)

## 1. Phase and primary task

P0 bootstrap, T001: existing-project baseline, portable engineering harness, audited backlog and daily evidence. T001 is reserved for this day; do not begin T002 today. This entry records pre-final-gate facts. Append the final receipt/status after verification.

## 2. Overall status

No CPU RTL, pipeline, peripherals, firmware, constraints, FPGA implementation or ASIC results exist. There are 43 planned tasks (39 mandatory, 4 optional). Architecture is a proposal, not an approved freeze. Only attended work is authorized under the current unrestricted session; unattended automation is disabled.

## 3. Project configuration and technical decisions

Official workspace: C:/RV32I_Edge_SoC, explicitly authorized for in-place development by the owner. Existing XPR was inspected as XML without launching Vivado. Part is xc7a35tcpg236-1; BoardPart is empty. All four file sets have no File entries. No top, RTL source, XDC or clock configuration is present. XPR comment identifies Vivado v2025.2; no executable version has been verified. Basys3 and 100 MHz remain candidate assumptions.

Keep the existing XPR and original kit unchanged during bootstrap. Root-level kit copies are now the active engineering system. Python 3.9.13 and installed tzdata 2026.2 are sufficient for the standard-library harness. Windows byte-range locking replaces the Linux-only assumption. State is authoritative; backlog statuses are its repairable projection. One task per Los Angeles calendar date, at most three verification attempts, exact argv without a shell, timestamped full-output receipts and append-preserving bilingual reports.

## 4. Work completed

Created a recoverable baseline before changing files: Git commit 8f16054b24a9d50021f8a805f7f0d78435206daa plus .baseline/20261015T051119Z/original.zip and SHA-256 manifest. Verified archive-member hashes for all 23 original files. Initialized dedicated branch engineering/bootstrap, preserving the previously non-Git project.

Audited the existing kit and repaired its Windows execution assumptions, task states, interrupted recovery, daily quota, evidence gates and final-completion logic. Added explicit owner execution gates and preserved review-only authority. Migrated the original 40 tasks, added full RV32I closure T041, UART RX T042 and actual FPGA execution T043. Final T040 depends directly on every mandatory task. Optional AXI4-Lite and DMA remain disabled and cannot block required completion.

Created preflight, explicit verification registry, bilingual report writer, manual daily entrypoint, local Make aliases and documentation. Registry starts empty intentionally: absent RTL/checks return NOT RUN rather than zero-test success. No dependencies, network downloads, host scheduler, FPGA programming or remote changes occurred.

## 5. Exact files added or changed

No original XPR, original kit file or original generated metadata was edited. Root-level additions at this snapshot:

- .gitignore
- .harness/checks.json
- .harness/environment.json
- .harness/state.json
- AGENTS.md
- Makefile
- README.md
- docs/ARCH_AUDIT.md
- docs/ARCH_SPEC.md
- docs/BACKLOG.json
- docs/CAREER_PORTFOLIO.md
- docs/CODEX_LOOP.md
- docs/DECISIONS.md
- docs/ENVIRONMENT_BOUNDARY.md
- docs/GETTING_STARTED_CN.md
- docs/PROJECT_BASELINE.json
- docs/PROJECT_CHARTER.md
- docs/PROJECT_STRUCTURE.md
- docs/REFERENCES.md
- docs/TOOLCHAIN.md
- docs/VERIFICATION_PLAN.md
- evidence/daily/README.md
- prompts/BOOTSTRAP_PROMPT.md
- prompts/DAILY_CODEX_PROMPT.md
- prompts/DAILY_RUN.md
- prompts/WEEKLY_REVIEW_PROMPT.md
- scripts/daily.ps1
- scripts/harness.py
- scripts/preflight.py
- scripts/report.py
- scripts/test_harness.py
- scripts/verify.py

Additional generated records are evidence/toolchain.json, evidence/daily/T001.md, evidence/report_entries/bootstrap-initial.json and the two docs/daily/2026-10-14 reports. Final timestamped receipt and any later same-day entries are listed in the final addendum. build/ and .tmp/ are ignored local scratch; .baseline/ and .git/ are also local additions.

## 6. Interfaces and assumptions

No RTL ports exist. The v0.1 draft proposes IF/ID/EX/MEM/WB, one outstanding ready/valid memory transaction, EX branch resolution, forwarding, load-use stalls and retirement comparison. Exact reset, port timing, memory map, error/trap behavior and stall/flush priority require T002 review. Do not implement tentative interfaces today. The MVP subset cannot satisfy full RV32I completion; FENCE/ECALL/EBREAK and approved EEI behavior need T041.

Controller interface: python -B scripts/harness.py validate|status|next|daily|begin|finish|block. Owner-only approve/reopen/enable/authorize commands require explicit acknowledgment; the agent must not self-approve. These flags are process rules, not authentication or an OS sandbox. Reports use scripts/report.py --entry <project-relative JSON> with technical and zh-CN strings.

## 7. Tests and exact commands

- python -B riscv_edge_soc_codex_kit/scripts/harness.py validate: exit 1, ModuleNotFoundError: fcntl. This is the preserved original defect; the archived kit remains unchanged.
- python --version: exit 0, Python 3.9.13.
- git --version: exit 0, Git 2.48.1.windows.1.
- python -B scripts/test_harness.py: preliminary suite passed 23 tests, exit 0 (9.021 seconds reported by unittest). Additional tests/guards were subsequently added; final finish must rerun the complete suite.
- python -B scripts/harness.py validate and status: exit 0; 43 tasks, T001 active, current date claimed.
- python -B scripts/preflight.py: exit 0; metadata/Python/Git readiness PASS only. evidence/toolchain.json contains exact commands, versions, paths and observed package metadata.
- git diff --check: exit 0 during preparation. Newly added files must also be staged and checked with git diff --cached --check before commit.
- Initial git status checks returned not-a-repository before baseline creation. No prior commits or uncommitted Git work existed to overwrite.
- A read-only Windows PowerShell Get-Date -AsUTC diagnostic failed because that switch is unavailable; subsequent timestamps used Python aware datetime and installed timezone data.

Final required command execution and exit codes will be captured by finish T001; do not infer them from this preliminary entry.

## 8. Verification coverage and gaps

Controller tests cover dependencies/priority, failed and missing-tool gates, dirty-tree protection, interrupted recovery, daily duplication, idempotent reruns, same-task cross-day recovery, owner review, bounded retries, concurrency, output preservation, reports and terminal behavior. Later additions cover optional enable, registry/input absence, runtime dependency corruption and prior-date preservation.

These are Python controller tests, not CPU simulation or HDL functional coverage. The harness cannot establish semantic correctness from file existence or command exit codes; independent RTL oracles and human review remain necessary. No RTL functional coverage, formal proof, ISA test, waveform, timing or hardware observation exists.

## 9. Timing, FPGA and ASIC results

All NOT RUN. No WNS/TNS/Fmax, setup/hold, area, power, resource, CDC signoff or board result is available. No build was attempted on an empty design. Docker's executable was found but no daemon/container operation was run.

## 10. Bugs and root causes

Original harness imported fcntl unconditionally, failing immediately on Windows. It also assumed make/python3, used todo/done rather than required states, blocked rather than resumed interrupted tasks, wrote temporary self-test repositories outside the project, truncated command output and did not implement the complete required daily reporting/terminal gates. These issues were addressed in root tooling while preserving original files for provenance.

Backlog omissions could have allowed apparent project completion without RX, complete RV32I behavior or actual FPGA run evidence. New mandatory tasks and final dependency validation close those planning gaps without asserting any implementation.

## 11. Unresolved issues

Unrestricted filesystem/network access is a real residual risk. No prompt, environment observation file or virtual environment enforces isolation. The owner authorized attended bootstrap but prohibited unattended work until suitable actual permissions are configured.

Vivado, Verilator, Icarus/vvp, Yosys, SBY, Make and RISC-V GCC were not found on PATH; cocotb and pytest are not available in the interpreter. This is discovery evidence only, not proof that no alternate installation exists. Board identity and Vivado executable path have been requested from the owner.

## 12. Dependencies and blockers

Bootstrap final gate is still pending at this entry. T002 can prepare architecture details on the next eligible date; owner must review before implementation depends on its completion. T003 must establish approved local tools before CPU work. No external installation or download is authorized. Physical programming, disruptive EDA and ASIC execution retain explicit owner gates. No daily scheduling time/days or actual sandbox change has been authorized/configured.

## 13. Git history

Branch: engineering/bootstrap. Baseline commit: 8f16054b24a9d50021f8a805f7f0d78435206daa. No remote/push exists. Only local core.autocrlf was configured; commit identity is supplied per command, without changing global Git configuration. Final engineering commit identifier will be recorded in a same-day addendum after verification/commit; a report cannot include its own containing commit hash before that commit exists.

## 14. Next recommended task

T002: produce precise architecture/reset/port/ISA-gap proposal and owner review checklist, including board confirmation. It must not start while today's T001 daily claim is in effect. After T002 verification, stop at awaiting_review until the owner approves.

## 15. Exact next-session instructions

Run python -B scripts/harness.py daily --supervised from the project root. Read this entire report including appended final results, AGENTS, boundary, specs, plan and state. Inspect actual sandbox and Git status. If T001 is still active/failed, resume T001 with begin T001; preserve unknown diffs. If it completed, do not start T002 on 2026-10-14. On a new eligible day with a clean baseline, select only T002. Review pending owner board/tool answers. Never run approve/authorize/reopen/enable for the owner. Generate both reports even on a blocked day. No unattended scheduler, installation, hardware programming or second task today.


---

<!-- entry:3a1e00389cde12a56f7bbd93456cac5331827dcab7d4db7a6b5b2afa1250789c -->

# Bootstrap gate attempt 1 — failure retained

The full controller suite passed 26 tests in 10.365s (exit 0). Preflight, backlog validation and unstaged diff checks passed. The staged whitespace check failed with exit 2 because some newly created root files used CRLF while core.autocrlf was false, and generated additions had extra blank lines at EOF. T001 remained failed/active with attempt count 1. Full original output is preserved in evidence/runs/T001/attempt-1-20261015T052429061951Z.json.

Correction: normalized line endings and EOF formatting only in newly added root files (12 files). Original XPR, original kit and original generated metadata were excluded. No test/assertion/expected behavior was weakened. The next gate will rerun the complete required suite and both whitespace checks. No new backlog task was selected.


---

<!-- entry:9575f90a9d40170b265498db076bdee12034aa576c8890a55555e2eca5efb146 -->

# Final bootstrap result — T001 completed

## Verified result and corrections

T001 completed after bounded attempt 2. Final receipt: evidence/runs/T001/attempt-2-20261015T052535290129Z.json. All five required commands returned exit 0:

- python -B scripts/test_harness.py: 26 tests, 10.445 seconds, OK.
- python -B scripts/preflight.py: metadata/Python/Git readiness only.
- python -B scripts/harness.py validate: valid 43-task acyclic plan/state.
- git diff --check.
- git diff --cached --check.

The first failed whitespace gate remains intact at evidence/runs/T001/attempt-1-20261015T052429061951Z.json; see the prior diagnosis. No test was weakened. Final logs capture complete output, exact interpreter path, start times, Python version and starting Git commit.

evidence/preservation.json confirms all 23 original files and every ZIP member still match their baseline SHA-256. Exactly two dated reports exist. No XPR/RTL/XDC source integration occurred during bootstrap.

## CLI and workflow evidence

evidence/cli_smoke.json records actual production CLI smoke commands and output. status, next and daily --supervised returned 0. daily without supervision returned the expected refusal (2). begin T002 returned the expected daily-quota refusal (2). verify.py lint returned NOT RUN (125), because no real RTL check or source exists. These negative results prove refusal behavior; they do not count as RTL PASS.

Persistent state: T001 completed, active null, attempts T001=2, daily claim 2026-10-14=T001, project in_progress. There are 1/39 mandatory tasks completed, 38 mandatory tasks pending, plus 4 disabled optional tasks. T002 is next for planning only today. There is no owner approval record, preexecution authorization, scheduler or remote push.

## Final evidence files added after the initial inventory

- evidence/report_entries/bootstrap-correction.json
- evidence/report_entries/bootstrap-completed.json
- evidence/runs/T001/attempt-1-20261015T052429061951Z.json
- evidence/runs/T001/attempt-2-20261015T052535290129Z.json
- evidence/preservation.json
- evidence/cli_smoke.json

Root source/docs listed earlier, the report entry JSON and both dated report files are the complete bootstrap work; build/.tmp/.baseline remain project-local ignored artifacts. Code and engineering evidence will be committed now, then the actual commit ID appended to these same reports.

## Handoff instruction after success

Do not resume T001 as unfinished and do not begin T002 on 2026-10-14. On the next eligible day, read all entries in this report and inspect the clean Git baseline. Run the attended daily command, then begin T002 only when eligible. Prepare exact architecture/reset/bus/ISA/board decisions and stop at owner review. Board identity and Vivado executable path are still requested from the owner. Actual sandbox setup and explicit scheduling authorization remain prerequisites to unattended work. All CPU, RTL simulation, formal, FPGA timing/hardware and ASIC results are NOT RUN.


---

<!-- entry:0f3a18dd2762f5b03dea0835f254020777eccf793e341d72d529e601cc528fc8 -->

# Committed delivery and exact file manifest

Engineering implementation/evidence commit: 049e3f93b2a6d1225971ccf95f6e380cf935558b, branch engineering/bootstrap. Parent/baseline: 8f16054b24a9d50021f8a805f7f0d78435206daa. The implementation commit passed gates before commit; Git working tree was clean immediately afterward. This addendum records the already-existing engineering commit and therefore lives in a later documentation-only commit. Obtain the final documentation commit with git log -1 --format=%H -- docs/daily/2026-10-14_technical.md. No history was amended and no remote was configured or pushed.

The 44 added engineering files in that commit are exactly:

- .gitignore
- .harness/checks.json
- .harness/environment.json
- .harness/state.json
- AGENTS.md
- Makefile
- README.md
- docs/ARCH_AUDIT.md
- docs/ARCH_SPEC.md
- docs/BACKLOG.json
- docs/CAREER_PORTFOLIO.md
- docs/CODEX_LOOP.md
- docs/DECISIONS.md
- docs/ENVIRONMENT_BOUNDARY.md
- docs/GETTING_STARTED_CN.md
- docs/PROJECT_BASELINE.json
- docs/PROJECT_CHARTER.md
- docs/PROJECT_STRUCTURE.md
- docs/REFERENCES.md
- docs/TOOLCHAIN.md
- docs/VERIFICATION_PLAN.md
- docs/daily/2026-10-14_technical.md
- docs/daily/2026-10-14_zh-CN.md
- evidence/bootstrap_inspection.json
- evidence/cli_smoke.json
- evidence/daily/README.md
- evidence/daily/T001.md
- evidence/preservation.json
- evidence/report_entries/bootstrap-completed.json
- evidence/report_entries/bootstrap-correction.json
- evidence/report_entries/bootstrap-initial.json
- evidence/runs/T001/attempt-1-20261015T052429061951Z.json
- evidence/runs/T001/attempt-2-20261015T052535290129Z.json
- evidence/toolchain.json
- prompts/BOOTSTRAP_PROMPT.md
- prompts/DAILY_CODEX_PROMPT.md
- prompts/DAILY_RUN.md
- prompts/WEEKLY_REVIEW_PROMPT.md
- scripts/daily.ps1
- scripts/harness.py
- scripts/preflight.py
- scripts/report.py
- scripts/test_harness.py
- scripts/verify.py

This addendum also creates evidence/report_entries/bootstrap-delivery.json and updates the same two dated reports. It changes no source, state, backlog, acceptance criterion or verification result. Only documentation whitespace checks are necessary after this addition. No second primary task began. All earlier failed-gate findings remain in this handoff and the Chinese report.

Manual next-session command from C:/RV32I_Edge_SoC: python -B scripts/harness.py daily --supervised. T002 is next, subject to the existing 2026-10-14 quota and owner architecture review. Unattended scheduling remains disabled. Owner actions still needed: board model, Vivado executable location, later actual sandbox configuration and any dependency/scheduling authorization.
