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
was explicitly approved by the owner on November2. Across four seeds,12,760 ordered retirement/fault/
GPR/RAM sample events matched, including2,008 successful retirements. Random
instruction/reset/formal and final core DV closure, FPGA implementation, hardware
and ASIC results remain future milestones. T041's [directed ISA/EEI matrix](docs/ISA_COMPLIANCE_MATRIX.md)
passed all five gates on attempt2 and was owner-approved November2:6,364 retirements/632
scenario runs, all40 families/nine fault classes, explicit FENCE and bus-error
evidence. The first nonvacuity failure and strengthened stimulus are preserved.
T019 random programs and the streaming scoreboard completed November4 on
attempt3: all five gates passed unchanged, including full16-target regression.
Six seeds matched14,458 retirements/300 scenarios, with11,446 random-only
retirements and36 streaming defect rejections. The native exit failure and
owner-requested shutdown interruption remain preserved. T020's executable
assertions completed on attempt2: all17 regression targets passed, six seeds
exercised real pipeline invariants and all16 isolated violations were detected.
The first regression's XSim native launch failure is preserved. See
[assertion scope and evidence](docs/ASSERTION_PLAN.md). T021 coverage completed
on attempt2 with all18 regression targets passing. A directed JAL/MEM case
filled a mandatory collision gap;44 of49 reachable crosses were observed,
five remain explicitly uncovered, and15 structural exclusions are documented.
See [coverage inventory and gaps](docs/COVERAGE_PLAN.md). T022 completed on its
first attempt with all19 regression targets passing:9,840 main retirements,
52 pre-reset retirements and28 selected shared-reset windows checked. Added
stress programs hit the five prior gaps (49/49 in the finite cross inventory),
and the injected retention leak was rejected. See [stress scope](docs/STRESS_VERIFICATION.md).
T023 selected formal verification was explicitly owner-skipped on November4;
its original NOT RUN125 record and zero executed formal tasks remain preserved.
See [formal limits and owner exception](docs/FORMAL_LIMITS.md). Progress is29
completed mandatory milestones plus1 owner-skipped, out of41. T024 simulation
DV review passed all seven gates on attempt2, including the full19-target
regression, and was explicitly owner-approved November4, acknowledging missing
formal proof. See [DV review package](docs/DV_CLOSURE.md). T025 board shell/XDC
completed on attempt2:962 vectors, exact negative checks and actual36-port/10ns
constraint/DRC inspection. See [board scope and limits](docs/BOARD_CONSTRAINTS.md).
T026 completed November6 on attempt3: real RV32I/ILP32 boot image, four independent
72-retirement model boots,66,250 primitive-memory RTL vectors and actual16ROM+16RAM
BRAM inference. See [firmware and memory evidence](docs/FIRMWARE_MEMORY.md). The
first mapping warnings and later native Vivado exit crash remain preserved.
Compiled CPU/SoC execution is pending T031.
T027 completed November6 on attempt2: UART TX and sending-side MMIO passed
247,940 native simulation rows, three negative controls and warning-free
synthesis lint. See [UART TX scope and evidence](docs/UART_TX.md).
T042 completed on attempt1:752306 RX edge rows plus the unchanged247940 TX replay,
three negative controls, two collision mutations and actual two-stage synchronizer
inspection. See [combined UART evidence](docs/UART_RX.md). Board execution remains pending.
T028 completed on attempt1: synchronized GPIO and timer MMIO, 9295
native edge rows, three input negatives and three actual RTL fault detections.
See [GPIO/timer contracts and evidence](docs/GPIO_TIMER.md). Full CDC remains T029.

The existing `RV32I_Edge_SoC.xpr` is the active Vivado project. Its configured part
is `xc7a35tcpg236-1`. The owner confirmed a Digilent Basys 3. The XPR now selects
`basys3_top` with the T025 diagnostic shell and selected board constraints. CPU/SoC
wiring is pending T031; this shell only demonstrates synchronized board I/O. Core
units are verified with reproducible non-project scripts. Vivado 2025.2 was located and its batch
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
