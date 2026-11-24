# RV32I Edge SoC — resume and STAR project summary

**Project:** Five-stage RV32I CPU, bare-metal Edge SoC and reproducible FPGA
verification flow. **Platform:** Digilent Basys 3, Artix-7
`xc7a35tcpg236-1`. **Period:** October–November 2026, ongoing.

This document translates the repository's engineering evidence into resume
bullets and interview stories. Metrics describe the exact scopes in the linked
reports. Select bullets that match the work you can explain and demonstrate;
do not combine repeated seed replays into additional unique coverage.

The current hardware issue is disclosed throughout: the board produces
`IRQ PASS`, but a controlled reset capture has three extra leading bytes. T032
physical acceptance remains open. Formal proof was explicitly skipped, and
ASIC implementation has not run.

## 1. Ready-to-adapt resume bullets

### RTL / FPGA design emphasis

- Implemented a five-stage RV32I pipeline with forwarding, load-use interlocks,
  age-ordered faults, control-flow flush and ready/valid memory backpressure;
  integrated 64 KiB ROM, 64 KiB RAM, UART, GPIO and a timer on a Basys 3 SoC.
- Closed the 100 MHz FPGA timing target, improving reported routed setup slack
  from **−5.092 ns to +0.123 ns (+5.215 ns)** through pipeline-control, memory
  addressing and implementation-flow repairs; final implementation used
  **3,291 LUTs, 2,554 FFs and 32 BRAM tiles**, with **zero DRC violations**.
- Implemented a reviewed **14-CSR subset**, six CSR instruction forms, precise
  trap entry/MRET and timer delivery through machine-external interrupts;
  verified integration with independent models, nine positive firmware/scenario
  runs and production UART divisor 868.
- Developed a reproducible synthesis/place/route flow with source/checkpoint
  hashing, bounded native jobs, complete setup/hold/CDC/power reports and
  conditional bitstream generation; preserved failed inputs and native logs.

### Design verification emphasis

- Built an independent retirement/reference comparison and streaming scoreboard
  that matched **14,458 successful retirements across 300 scenarios and six
  deterministic seeds**, including **11,446 random-only retirements**.
- Closed a directed project RV32I/EEI matrix covering **40 base instruction
  families and nine fault classes**, with **6,364 matched retirements across
  632 scenario runs**, while explicitly separating finite testing from certification.
- Expanded the registered regression inventory from **16 to 28 targets**
  (**12 additions / 75% growth**) and retained real faulty-RTL, trace-corruption,
  malformed-input and timeout controls to prevent false passes.
- Verified pipeline memory waits across **168 scenarios / 2,008 retirements /
  four seeds**, including **32-edge data waits**, held-operand correctness,
  stale-fetch drain, wrong-path suppression and exactly-once effects.

### Engineering automation / debugging emphasis

- Created a persistent, sequential engineering harness spanning **45 tasks**
  (**41 mandatory, four optional**) with dependency/review gates, a three-attempt
  finish budget, recoverable state and paired technical/Chinese handoff reports.
- Added bounded native-process management with **120-second per-tool** limits,
  registered composite budgets up to **600 seconds**, Windows process-tree
  cleanup and immutable command/exit/source/artifact receipts.
- Brought the approved image onto physical hardware, captured real interrupt
  firmware output, isolated a **three-byte reset-related UART prefix**, and
  reproduced a plausible reset-chatter failure mechanism without filtering
  observations or claiming completed board acceptance.

## 2. Quantitative improvement ledger

| Area | Baseline | Recorded result | Defensible interpretation |
|---|---|---|---|
| Setup timing | Initial routed WNS −5.092 ns | Final WNS +0.123 ns | **5.215 ns slack improvement** at the unchanged 10 ns target |
| Setup violations | Initial report: 3,241 failing endpoints | Final report: 0 failing endpoints | Transition from failing implementation to scoped setup closure; endpoints need not map one-to-one |
| Regression inventory | 16 registered targets at T019 | 28 at T043 | **+12 targets / +75% inventory**, not 75% more coverage or runtime speed |
| Routing completion | Failed implementation was not acceptable | 5,892/5,892 routable nets, 0 errors | All required routing completed in the accepted implementation |
| FPGA fit | Target capacity: 20,800 LUT / 41,600 FF / 50 BRAM tiles | 3,291 LUT / 2,554 FF / 32 BRAM | 15.82% / 6.14% / 64% utilization; these are final resource figures, not an area-reduction baseline |
| Random architectural DV | Directed prefix retained | 14,458 retirements, 300 scenarios, 6 seeds | 11,446 retirements belong to the added random-only programs |
| Directed ISA scope | Explicit RV32I/EEI requirements | 40 families, 9 faults, 632 scenario runs | Finite requirement-driven evidence; no external certification implied |
| Failure detection | A completion marker alone was insufficient | 36 streaming-scoreboard mutations and 18 comparator mutations rejected in the T019 evidence | Tested rejection paths rather than assuming the checker works |
| Board diagnosis | Mixed presses and unqualified LED observations | Controlled capture: `ff 49 f2` + one complete success line | A more specific reproducible symptom; still an unresolved hardware acceptance failure |

Calculations: `0.123 - (-5.092) = 5.215 ns`; `(28 - 16) / 16 = 75%`.
Do not describe a crossing-zero slack change as a percentage improvement. No
measured CPI, IPC, benchmark throughput, energy efficiency or maximum-frequency
improvement has been established.

## 3. STAR story — pipeline implementation and integration

**Situation.** The project needed an executable five-stage CPU, rather than a
collection of individually tested arithmetic and decode blocks. Correctness had
to survive data hazards, variable memory timing and wrong-path instructions.

**Task.** Integrate IF/ID/EX/MEM/WB behavior under the reviewed RV32I, reset,
memory and fault contracts, with observable ordered retirement suitable for an
independent architectural comparison.

**Action.** Implemented valid-carrying stage storage and explicit-width control,
nearest-eligible forwarding, load-use stalls and held-operand handling. Resolved
branches/jumps with wrong-path invalidation and stale-fetch drain. Separated
accepted memory requests, successful response effects and later retirement so
that a held instruction could not duplicate writes or retire twice. Preserved
instruction age when faults competed with memory holds and redirects.

**Result.** The memory-wait milestone checked **2,008 retirements across 168
scenarios and four seeds**, including long stalls and **32-edge data waits**.
The owner-reviewed pipeline milestone subsequently passed all six registered
gates on its first finish attempt. The integrated SoC retained the same bus
contracts while adding memories and peripherals.

**Evidence:** [pipeline review](docs/PIPELINE_REVIEW.md),
[backpressure contract](docs/BACKPRESSURE.md),
[T017 results](evidence/daily/T017.md).

**Interview focus:** Explain why an older WB instruction may retire once while
MEM stalls younger stages, why a flushed accepted fetch still needs draining,
and why a memory effect is not necessarily the same cycle as its retirement.

## 4. STAR story — independent architectural verification

**Situation.** A CPU can print a success message while hiding wrong-path writes,
stale operands, incorrect byte lanes or duplicated transactions. A checker
derived from the RTL could reproduce the same mistake instead of detecting it.

**Task.** Compare actual retired behavior against an independent architectural
model, retain replayable failures and demonstrate that negative cases fail.

**Action.** Used an independent Python ISA interpreter driven by initialized
instruction/data bytes. Compared ordered retirement, fault and architectural
state records. Added a streaming effect ledger, literal anchor tests, bounded
random programs, exact seed retention and terminal-state checks. Deliberately
corrupted GPR, RAM and retirement records; rejected empty, extra, reordered or
truncated observations. Preserved actual simulator failures rather than accepting
a printed completion marker.

**Result.** The T019 run matched **33,658 ordered events**: **14,458 retirements,
300 faults, 9,300 GPR words and 9,600 RAM sample words**. Six seeds covered
**48 added random program runs** alongside the retained directed prefix;
**11,446 retirements** came from those random-only programs. All **36 streaming
mutations** and **18 comparator mutations** in the recorded scope were rejected.

**Evidence:** [random verification](docs/RANDOM_VERIFICATION.md),
[T019 acceptance](evidence/daily/T019.md),
[independent reference model](dv/reference/rv32_iss.py).

**Interview focus:** The effect ledger and ISA interpreter are complementary
checks, not two independent full ISA models. Distinguish the checked RAM sample,
the separately tested complete RAM behavior, and coverage inferred from finite
programs. Replaying a seed confirms reproducibility without creating new coverage.

## 5. STAR story — RV32I/EEI requirement closure

**Situation.** An ALU or arithmetic-only instruction smoke test cannot establish
the declared CPU behavior. FENCE, illegal encodings, access faults, misalignment
and instruction-age interactions needed explicit expected behavior.

**Task.** Build a traceable directed matrix for all 40 base mnemonics and the
project's execution environment, including cases often missed by small cores.

**Action.** Exercised FENCE drain semantics, ECALL/EBREAK, x0 memory accesses,
JALR alignment, untaken-branch hypothetical targets, malformed instruction
encodings and bus errors. Compared actual traces with independent expectations
and preserved the original collision tests. Added nonvacuity witnesses and
mutations so that merely enabling a test could not count as exercising it.

**Result.** The accepted directed matrix recorded **46,812 independently matched
ordered events**, including **6,364 successful retirements**, across **632
scenario runs**. It covered **40 instruction families**, **nine fault classes**
and **23 semantic requirements**. The first nonvacuity failure remained in the
history and the repaired stimulus passed on the second finish attempt.

**Evidence:** [ISA compliance matrix](docs/ISA_COMPLIANCE_MATRIX.md),
[T041 evidence](evidence/daily/T041.md).

**Interview focus:** Describe the selected execution environment rather than
claiming generic privileged compliance. The later CSR/trap revision was reviewed
separately; its existence does not retroactively expand the initial matrix.

## 6. STAR story — FPGA timing and implementation closure

**Situation.** An initial routed design failed the 100 MHz target with **−5.092 ns
setup WNS** and **3,241 failing endpoints**, alongside retained BRAM/control DRC
findings. Simulation success alone could not establish a usable FPGA image.

**Task.** Reach real routed setup/hold closure and clean DRC on the fixed Artix-7
part while preserving the architectural contracts and all independent checks.

**Action.** Inspected native critical paths and preserved failed source/report
snapshots. Factored serialized CSR and pipeline-control paths, parallelized
branch target preparation, removed redundant invalid-payload control dependencies,
and simplified registered pending-state RAM addressing. Kept reset distribution
clocked and validated invariants with real faulty variants. Split implementation
into bounded checkpoints and checked predecessor/source hashes through synthesis,
placement, physical optimization, routing and report generation. Did not reduce
the clock target, hide native warnings or introduce broad timing exceptions.

**Result.** The final accepted implementation achieved **+0.123 ns setup WNS**
and **+0.013 ns hold slack**, with **zero failing endpoints**, **zero DRC
violations** and **5,892 fully routed nets**. Setup slack improved by **5.215 ns**.
Resource use was **3,291 LUTs / 2,554 FFs / 32 BRAM tiles / 36 IOBs**. All six
registered T043 gates and two whitespace checks passed; the owner approved the
package. Twenty-one failed preparation archives remain available.

**Evidence:** [FPGA report](docs/FPGA_PPA.md),
[machine-readable manifest](evidence/fpga/manifest.json),
[repair chronology](evidence/daily/T043.md).

**Interview focus:** Setup and hold margins are small. New RTL, tools or placement
require fresh closure. The 0.084 W vectorless estimate has low confidence and
must not be presented as measured board power or an efficiency improvement.

## 7. STAR story — SoC firmware, traps and timer interrupts

**Situation.** The reference execution environment originally halted on faults.
The final SoC needed reviewed resumable traps and timer interrupts while
preserving the legacy configuration and peripheral semantics.

**Task.** Implement the scoped architectural revision and demonstrate precise
entry/return, context preservation and actual bare-metal firmware execution.

**Action.** Added the reviewed 14-CSR subset, six CSR instruction forms and MRET.
Serialized state-changing CSR/return operations and drained older work before
interrupt admission. Routed the timer through machine-external cause 11 while
keeping the timer's original reload bit meaning. Built a separate IRQ image,
checked compiler/image bindings and used independent CSR, timer, bus, retirement
and serial models. Preserved the legacy image and tests.

**Result.** The final interrupt gate recorded **144 checks / 74 command records**,
including **nine positive firmware/scenario runs**, replayable seeds **1** and
**20261107**, production UART divisor **868**, and actual faulty RTL variants.
Each seed's standalone corpus included **6,424 CSR** and **526 timer vectors**.
The scoped physical image was programmed successfully and produced real
`IRQ PASS` output; full physical reset/UART acceptance remains unresolved.

**Evidence:** [interrupt contract](docs/INTERRUPT_SPEC.md),
[implementation report](docs/INTERRUPT_REPORT.md),
[final IRQ gate receipt](evidence/toolchain_runs/interrupts-20261108T211417593073Z.json),
[firmware](sw/interrupt_smoke.S).

**Interview focus:** The timer uses machine-external interrupts, not a standard
64-bit `mtime/mtimecmp` platform. This is a documented subset, not a complete
privileged implementation. A UART marker alone cannot establish every trap or
CSR behavior; the simulation comparisons provide the detailed internal evidence.

## 8. STAR story — reproducible engineering and failure recovery

**Situation.** A long hardware project spans tool runs, interrupted sessions,
multiple review gates and changing source snapshots. Unrecorded retries can lose
the relationship between a result, its exact inputs and its owner approval.

**Task.** Make engineering work resumable and auditable without pretending that
a Python wrapper provides a security sandbox or that skipped checks passed.

**Action.** Added persistent backlog/state, dependency-based selection, one active
task, explicit review/start gates and a three-attempt finish budget. Captured
commands, versions, exit codes, seeds, waveforms and source/artifact hashes.
Used project-local outputs, process-tree timeout cleanup and recoverable Git
checkpoints. Appended paired technical and Chinese reports and retained failed
attempts. Expanded the regression without removing prior targets.

**Result.** The harness tracks **45 tasks**: **41 mandatory and four optional**.
The regression grew **16 → 28 targets (+75%)**. The final T043 integrity audit
checked **45 tool receipts**, **three linked data reports**, **189 source files**
and **2,644 artifact hashes**, including **32 protected baseline files**. Native
jobs are bounded at **120 seconds** and registered composites at **600 seconds**.
As of this summary, **35 mandatory tasks are completed**, **one is explicitly
skipped**, and **five remain unfinished**; progress is not inflated by counting
the skip as PASS.

**Evidence:** [engineering loop](docs/CODEX_LOOP.md),
[backlog](docs/BACKLOG.json),
[T043 integrity audit](evidence/fpga/final-audit-2026-11-15.json).

**Interview focus:** Workflow acknowledgments are not authentication. The current
runtime has unrestricted filesystem permissions; unattended operation is not
enabled. Repository state and documentation do not create an OS security boundary.

## 9. STAR story — honest physical-board debugging

**Situation.** The board printed the expected success text, but repeated button
presses, uncertainty about status LEDs and unexpected bytes could make a casual
bring-up look more complete than the evidence supported.

**Task.** Establish device/image identity, obtain truthful physical observations
and isolate the symptom while keeping the physical acceptance rule unchanged.

**Action.** Bound the approved bitstream to the selected JTAG device and matched
the UART interface through its shared USB parent. Recorded native programming,
raw UART bytes, timestamps and owner reset/DONE observations. Preserved empty,
multi-message and framing-error captures. Separated a quiet 30-second passive
observation from a controlled held-reset release. Compared ideal and representative
chatter behavior in an actual-top simulation using the unchanged strict decoder.

**Result.** The controlled physical capture isolated **13 bytes**: prefix
**`ff 49 f2`** plus the **10-byte `IRQ PASS\r\n`** message, in one burst. The
whole capture remains **FAIL**. Simulation demonstrated a plausible mechanism:
ideal release decodes exactly, reset chatter rejects with `SOC_UART_FRAMING`,
and the final stable-reset message is correct. A **20 ms / 2,000,000-clock**
release-qualification proposal was prepared for owner review, not implemented
or claimed as a verified fix.

**Evidence:** [physical diagnostic](evidence/hardware/reset-release-diagnosis-2026-11-21.json),
[proposed correction](docs/RESET_RELEASE_REVIEW.md),
[passing diagnostic simulation](evidence/toolchain_runs/reset-uart-diagnostic-20261122T021545951186Z.json).

**Interview focus:** State what the physical trace proves, what it does not prove,
and why ignoring a prefix would weaken the acceptance oracle. The switch waveform
has not been measured, and no conclusive sole-cause attribution is claimed.

## 10. Claim boundaries and interview checklist

Use these distinctions when presenting the project:

| Accurate claim | Avoid claiming |
|---|---|
| 100 MHz routed timing target met for the accepted source snapshot | Measured maximum CPU frequency or benchmark speedup |
| Real board programming and IRQ text observed | Completed physical board signoff |
| Independent finite ISA/retirement checks | Exhaustive correctness or external RISC-V certification |
| Formal explicitly skipped with owner acknowledgment | Formal proof passed |
| 32 BRAM tiles used in the final FPGA implementation | ASIC area, silicon power or tapeout readiness |
| 75% increase in registered regression targets | 75% increase in coverage, defect detection or development productivity |
| A plausible reset-chatter mechanism reproduced in simulation | A physically measured root cause or completed 20 ms fix |
| A prepared manual self-hosted workflow | A successful GitHub-hosted full regression |

Before an interview, be prepared to walk through a load-use stall, an older fault
competing with a younger store, the one-outstanding bus protocol, CSR/MRET
serialization, the worst routed timing path, one retained failure and the exact
scope of the physical UART issue. Those explanations are stronger than adding
unmeasured performance claims.
