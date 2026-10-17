# RV32I Edge SoC engineering contract

The official writable workspace includes the existing Vivado project. The owner
authorized in-place development. Inspect before editing and preserve recoverability.
`riscv_edge_soc_codex_kit/` is the untouched original kit; use root-level tooling.

Before each session read the latest `docs/daily/*_technical.md`, this file,
`docs/ENVIRONMENT_BOUNDARY.md`, `docs/ARCH_SPEC.md`, `docs/VERIFICATION_PLAN.md`,
`docs/BACKLOG.json`, `.harness/state.json`, and `docs/CODEX_LOOP.md`.

- Run `python -B scripts/harness.py daily --supervised` for an attended session.
  Inspect Git status and recover the active task before choosing another one.
- Select exactly one dependency-ready task per America/Los_Angeles calendar day.
  Use `begin ID`, implement its scope, then `finish ID --evidence PATH`.
  At most three verification attempts per task; preserve failures and never weaken
  checks. Missing tools/checks are NOT RUN and cannot pass a task.
- Keep generated files, dependencies, caches, temporary files and logs here.
  No global configuration changes, external downloads, pushes, host scheduling,
  destructive Git operations, source deletion, or FPGA programming without owner
  authorization. Do not read unrelated personal data or secrets.
- This session is unrestricted. The harness is not a security sandbox. Do not run
  unattended automation until actual runtime sandbox and approval controls have
  been configured and inspected. A configuration file alone is not enforcement.
- Use explicit-width SystemVerilog, `always_ff`/nonblocking for state and
  `always_comb`/blocking for combinational logic; no unintended latches, fabric
  clocks, or unsynchronized inputs. RTL changes need independent self-checking
  tests with replayable seeds.
- Architecture, ISA, memory map, reset/flush priorities, target and clock domains
  require owner review before implementation changes. Never call `approve`,
  `reopen`, or `enable` on the owner's behalf. Flags are workflow acknowledgments,
  not authentication or enforcement.
- Before stopping, create/update exactly two dated Markdown reports under
  `docs/daily/`, even on failure/blocked days. Append same-day findings; retain
  earlier findings. Record commands, exit codes, versions, commits, gaps and next
  session instructions. Never erase prior-day reports.
- Review the diff, run gates and `git diff --check`, commit inspected task files
  locally, then stop. No second task after success.
- Distinguish simulation, formal, synthesis, timing, hardware and ASIC evidence.

Bootstrap T001 used the quota on 2026-10-14. For later sessions use the actual
America/Los_Angeles date and persistent daily_claims, not that historical date.
No CPU RTL is to be implemented before T002 owner review and T003 toolchain gates.
