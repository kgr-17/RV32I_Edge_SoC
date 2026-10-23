# RV32I Edge SoC

Status: T002 architecture v0.2 approved by the owner; T003 toolchain gates passed
on October 23 after the authorized reopen. The argument-file repair passed:
61 Python tests, two seeded fixture simulations (268 vector checks), fixture
synthesis/structural lint and all five injected failure checks. Exact evidence is
in evidence/daily/T003.md. T004 opcode/immediate decoding is the next eligible
day's task. No CPU RTL, FPGA
implementation, hardware validation or ASIC results exist yet.

The existing `RV32I_Edge_SoC.xpr` is the active Vivado project. Its configured part
is `xc7a35tcpg236-1`. The owner confirmed a Digilent Basys 3. Top module, RTL and
constraints are not yet configured. Vivado 2025.2 was located and its batch
startup/target-part catalog verified; local paths are in `.harness/toolchain.json`.

From PowerShell in `C:\RV32I_Edge_SoC`:

```powershell
python -B scripts/preflight.py
python -B scripts/test_harness.py
python -B scripts/harness.py status
python -B scripts/harness.py daily --supervised
```

The last command prepares an attended Codex session. Read the returned handoff
and `prompts/DAILY_RUN.md`, then perform exactly one eligible task. It does not
start a model, run an infinite loop, install a scheduler, or run RTL by itself.
`scripts/daily.ps1` is a PowerShell convenience entrypoint with the same purpose.
Python is the supported native Windows interface; Make targets are optional
aliases and were not executed because Make is not on PATH.

Read `docs/ENVIRONMENT_BOUNDARY.md`, `docs/CODEX_LOOP.md`, the latest technical
handoff under `docs/daily/`, and `docs/BACKLOG.json`. The v0.2 architecture proposal
and explicit decisions are in `docs/ARCH_SPEC.md` and `docs/ARCH_REVIEW.md`; the
companion `docs/ARCH_CONTRACT.json` has consistency/mutation checks. Their proposal
fields are preserved as the reviewed submission; owner acceptance is recorded in
`.harness/state.json` and `evidence/owner_reviews/T002-2026-10-17.json`.
The backlog has 45 tasks: 41 mandatory, 4 optional,
including the required later interrupt architecture and verification milestones.

Original work is recoverable from baseline Git commit
`8f16054b24a9d50021f8a805f7f0d78435206daa` and a local hash-verified backup
documented in `docs/PROJECT_BASELINE.json`. The original engineering kit remains
unchanged in `riscv_edge_soc_codex_kit/`; root-level files are the active versions.

This bootstrap session has unrestricted filesystem access. Unattended execution
is disabled pending actual sandbox/approval configuration. No tools, packages or
IP were downloaded/installed and no FPGA was programmed. Previously authorized
official documentation reads are recorded in evidence/t002_sources.json.
