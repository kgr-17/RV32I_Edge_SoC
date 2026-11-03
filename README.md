# RV32I Edge SoC

Status: T002 architecture v0.2 approved by the owner; T003 toolchain gates passed
on October 23 after the authorized reopen. The argument-file repair passed:
61 Python tests, two seeded fixture simulations (268 vector checks), fixture
synthesis/structural lint and all five injected failure checks. Exact evidence is
in evidence/daily/T003.md. T004 decoder/package also passed on October 23 under
an explicit one-time owner exception: all 40 mnemonics, 287,618 vector checks
across two seeds, independent oracle tests and real decoder synthesis lint.
See [decoder interface and reproduction](docs/DECODER.md) and evidence/daily/T004.md.
T005 ALU passed on October 25 with 234,804 vector checks. T006 register-file
automation passed on attempt 2 and was explicitly approved by the owner:
[interface and review checklist](docs/REGFILE.md). Expanded unit regression passed
1,185,178 vectors across fixture, decoder, ALU, register file, branch, LSU,
stage storage, forwarding and hazard detection.
T007 branch/jump unit passed 253,936 vectors; T008 load/store formatting passed 89,744.
T009 memory behavior models passed 49,276 seeded edges and 11 tests;
T010 nonpipelined reference CPU passed 324 directed retirements in 22 scenarios.
T011 independent ISA comparison matched those retirements and terminal GPR/RAM
samples. T012's [L1 baseline report](docs/VERIFICATION_REPORT.md) was explicitly
approved by the owner on November 2. T013 stage storage passed 79,022 clocked
vectors at widths 1/32/129; T014 forwarding passed 144,424 comparisons.
T015 pipeline dependency integration matched 128 retirements; T016 control matched
502 retirements across 42 scenarios. T017 randomized bus waits passed four seeds,
2,008 retirements across 168 scenarios, with IF/data request stalls and 32-edge
data waits observed. The first attempt's native Vivado exit crash is retained;
the identical second attempt passed. T018's independent pipeline ISS comparison
and all six gates passed on attempt1; the [pipeline review](docs/PIPELINE_REVIEW.md)
is awaiting owner acceptance. Across four seeds,12,760 ordered retirement/fault/
GPR/RAM sample events matched, including2,008 successful retirements. Random
instruction/reset/formal and final ISA/EEI closure, FPGA implementation, hardware
and ASIC results remain future milestones.

The existing `RV32I_Edge_SoC.xpr` is the active Vivado project. Its configured part
is `xc7a35tcpg236-1`. The owner confirmed a Digilent Basys 3. Top module, RTL and
constraints are not yet configured in the XPR; the core units are verified with
reproducible non-project scripts. Vivado 2025.2 was located and its batch
startup/target-part catalog verified; local paths are in `.harness/toolchain.json`.

From PowerShell in `C:\RV32I_Edge_SoC`:

```powershell
python -B scripts/preflight.py
python -B scripts/test_harness.py
python -B scripts/harness.py status
python -B scripts/harness.py daily --supervised
```

The last command prepares an attended Codex session. Read the returned handoff
and `prompts/DAILY_RUN.md`, then work through ready tasks sequentially. The owner
removed the one-task-per-day cap on October 23. Verify, report and commit each
task before the next; keep one active task and honor all review gates. It does not
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
