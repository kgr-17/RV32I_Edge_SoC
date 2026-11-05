# L1 reference-core baseline for owner review

Status: AUTOMATED GATES PASS; OWNER APPROVED 2026-11-02. Baseline date 2026-10-26
America/Los_Angeles. Engineering baseline commit 5814768. T001..T011 are
completed, including recorded T002 architecture and T006 register-file reviews.
The architecture submission's historical PROPOSED label is preserved; its
recorded owner review authorizes v0.2. No architecture revision is proposed here.

## Scope and decision requested

Review the directed, nonpipelined RV32I reference-core baseline and permission
to progress to T013's already specified five-stage implementation. This gate
does not declare the SoC complete or authorize tool downloads, scheduling,
global configuration, FPGA programming or a new ISA/clock/memory/reset policy.

The reviewed part is xc7a35tcpg236-1/Basys 3. Existing XPR/XDC/kit are unchanged;
reproducible non-project Tcl performs synthesis/structural lint. These are not
final top-level implementation, routed timing, physical board or ASIC results.

## Instruction-family traceability

All rows below have actual XSim execution and independent ISS event/state
comparison in T011's two seeds (1/20261026), not just decoder classification.
The fresh T012 matrix check repeats source/artifact integrity checks after new
test-core/test-retire runs. Its JSON has per-instruction/per-fault/per-seed hits.
Counts include executed fault-producing attempts; ECALL/EBREAK deliberately
terminate without retirement. Parser initialization/control rows are not tests
of instruction execution and are never added to retirement counts.

| Family | Instructions | Directed evidence |
|---|---|---|
| Upper | LUI, AUIPC | constants and PC-relative result |
| Jump | JAL, JALR | redirect, links/readback, bit-zero clearing, bad target |
| Branch | BEQ, BNE, BLT, BGE, BLTU, BGEU | taken/false signed/unsigned; false bad hypothetical target |
| Load | LB, LH, LW, LBU, LHU | lanes, signed/unsigned, ROM/RAM, x0 access/error |
| Store | SB, SH, SW | selected bytes, neighbor preservation, response/retire correlation |
| Immediate ALU | ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI | wrap, compare, shift and GPR readback |
| Register ALU | ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND | signed/unsigned edges, low-five shift, readback |
| Ordering | FENCE | ignored future fields; sequential full drain |
| Environment | ECALL, EBREAK | distinct sticky fault termination, no retirement |

Nine fault codes are exercised: illegal instruction; instruction address/access;
load address/access; store address/access; ECALL; breakpoint. Faulting instructions
do not retire or change GPRs/memory. Inaccessible redirected fetch reports target
PC and insn=0. Fault payload remains stable through the post-halt checks.

## Evidence already established and fresh gate plan

T011 passed on attempt 2 after one native Vivado exit crash with identical
source retry; the failed receipt/log remains retained. Independent comparison
matched 324 retirements, 22 faults, 682 terminal x1..x31 values and 704 RAM words
(1,732 ordered events), with all 49 ISA/fault bins. Ten ISS/comparator tests and
per-seed wrong-bit/empty/extra-event injections passed. Core bench also checks
all 64 KiB RAM against independent directed expectations. See [ISS](ISS.md),
[reference core](REFERENCE_CORE.md) and [T011 evidence](../evidence/daily/T011.md).

Unit regression retains 887,108 comparisons across fixture/decoder/ALU/RF/branch/
LSU. Python memory models passed 49,276 edges/11 tests, with 8,654 accepts exactly
7,487 completions plus 1,167 reset cancellations. These counts describe different
scopes and must not be summed. Repeated seed runs are replay, not unique coverage.

T012 required commands: verify.py lint, test-core, test-retire, and newly added
test-isa-directed, plus both Git whitespace gates. The last target actually
executes dv/integration/test_isa_directed.py: six rejection-policy tests, pinned
approved architecture identity, fresh source hashes, complete 40/9 row matrix,
seed/state/event/mutation checks and revalidated actual/expected trace artifacts.
It cannot replace a missing simulator run or silently use an older passing run.
T012 passed attempt 1: all four checks and both whitespace gates, exit 0. The
six baseline-policy tests passed and all 40/9 matrix rows have nonzero hits for
both actual seeds. Exact fresh results and per-row counts are recorded below.

## Limits and required later milestones

These directed programs are hand-assembled machine words. A RISC-V GCC/C
firmware compilation flow has NOT RUN; no compiler was downloaded/installed.
Random instruction programs/long sequences, full RV32I/EEI closure (T041),
pipeline forwarding/stalls/flush/precise age priority, reset in every in-flight
phase, selected formal, UART TX/RX and SoC peripherals, IRQ/CSR revision, firmware,
implementation/constraints/CDC/routed timing/power, physical hardware and ASIC
evidence remain mandatory future work. No RISC-V certification is claimed.

The independent ISS shares the reviewed specification and stimulus bytes; it
imports no RTL semantics or hand expectations. Terminal ISS comparison samples
the touched 128-byte RAM window; the original SV scoreboard checks full RAM.
x0 has no stored word and is exercised through unit and program behavior.
Protocol models, RTL simulation, structural synthesis, formal, routed timing,
hardware and ASIC remain distinct evidence categories.

Known resolved issues: retained T006/T008 synthesis warning repairs, T009 drain
bound/receipt serialization fixes. Known tool issue: one native exit access
violation, cause undetermined, identical bounded retry passed. No failing DUT
or model comparison remains within the recorded scope. This is not a statement
about unexecuted later tests. Runtime is unrestricted; unattended stays disabled.

## Owner review checklist

- Confirm the L1 scope/evidence and remaining mandatory gaps above are understood.
- Review byte-address/strobe/effect-point, x0, reset and sticky fault contracts in
  REFERENCE_CORE.md, MEMORY_MODELS.md and ISS.md; no architecture change proposed.
- Inspect T012 receipt, dated 40/9 matrix and source-bound comparison evidence.
- Approve T012 only after review; the harness must retain awaiting_review until
  the owner's acknowledgment. AGENTS.md reserves the approval command to the owner.

No owner approval is created by this document or the matrix generator.

## Owner acknowledgment applied 2026-11-02

The owner explicitly replied "Approve T012 and authorize that command" to the
review of commit 4591b78. The specified approval command was executed on resume,
exit 0. The approved report bytes were hash-checked before this acknowledgment
was appended; the original submission and all pending-review language below
remain historical provenance. See evidence/owner_reviews/T012-2026-11-02.json
and its command receipt. T012 is completed. No broader approvals are inferred.

## Fresh T012 acceptance and per-seed matrix

Receipt: [T012 attempt 1](../evidence/runs/T012/attempt-1-20261026T235342501556Z.json).
Lint: [21 checks / 12 commands](../evidence/toolchain_runs/lint-20261026T235342875952Z.json).
Core: [directed run](../evidence/toolchain_runs/core-20261026T235633405759Z.json).
ISS: [independent comparison](../evidence/toolchain_runs/retire-20261026T235648507780Z.json),
[actual backend](../evidence/toolchain_runs/core-20261026T235650639871Z.json).
Matrix: [source/artifact-validated JSON](../evidence/l1/2026-10-26_matrix-20261026T235705641875Z.json).
Validator: [six tests and actual collection](../evidence/toolchain_runs/isa-directed-20261026T235705641875Z.json).

Both seeds repeat the established 324 retirements/22 faults and compare 682
GPR / 704 sampled RAM words. All mutations, complete event/state counts and
source/backend/trace hashes passed. This is replay of the same directed suite.

| Instruction | Seed 1 executions | Seed 20261026 executions |
|---|---:|---:|
| LUI | 14 | 14 |
| AUIPC | 1 | 1 |
| JAL | 3 | 3 |
| JALR | 2 | 2 |
| BEQ | 2 | 2 |
| BNE | 2 | 2 |
| BLT | 2 | 2 |
| BGE | 2 | 2 |
| BLTU | 2 | 2 |
| BGEU | 2 | 2 |
| LB | 12 | 12 |
| LH | 7 | 7 |
| LW | 5 | 5 |
| LBU | 4 | 4 |
| LHU | 2 | 2 |
| SB | 8 | 8 |
| SH | 4 | 4 |
| SW | 4 | 4 |
| ADDI | 71 | 71 |
| SLTI | 1 | 1 |
| SLTIU | 1 | 1 |
| XORI | 1 | 1 |
| ORI | 1 | 1 |
| ANDI | 1 | 1 |
| SLLI | 1 | 1 |
| SRLI | 1 | 1 |
| SRAI | 1 | 1 |
| ADD | 1 | 1 |
| SUB | 1 | 1 |
| SLL | 1 | 1 |
| SLT | 1 | 1 |
| SLTU | 1 | 1 |
| XOR | 1 | 1 |
| SRL | 1 | 1 |
| SRA | 1 | 1 |
| OR | 1 | 1 |
| AND | 1 | 1 |
| FENCE | 1 | 1 |
| ECALL | 2 | 2 |
| EBREAK | 1 | 1 |

| Fault code / name | Seed 1 events | Seed 20261026 events |
|---|---:|---:|
| 1 ILLEGAL_INSN | 1 | 1 |
| 2 INSTR_ADDR_MISALIGNED | 2 | 2 |
| 3 INSTR_ACCESS_FAULT | 1 | 1 |
| 4 LOAD_ADDR_MISALIGNED | 1 | 1 |
| 5 LOAD_ACCESS_FAULT | 1 | 1 |
| 6 STORE_ADDR_MISALIGNED | 1 | 1 |
| 7 STORE_ACCESS_FAULT | 1 | 1 |
| 8 ECALL | 2 | 2 |
| 9 BREAKPOINT | 1 | 1 |

Tools: Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2, Vivado/XSim 2025.2
SW6299465. Approved architecture SHA-256: 403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03.

T012 remains awaiting_review; mandatory completion is 11/41. No owner approval
was generated. After review, the owner acknowledgment is
`python -B scripts/harness.py approve T012 --confirm-owner-review`.
T013 is not begun until that review closes and the Git baseline is clean.


## T024 current simulation DV review (November4)

The complete L1 report above is preserved as historical owner-approved evidence.
Current five-stage CPU simulation DV review is docs/DV_CLOSURE.md. T019..T022
passed their scoped gates; T023 was explicitly owner-skipped with formal NOT RUN,
not a proof or completed verification task. T024 fresh workflow/lint/full19-target
regression/coverage/collector gates are pending. Its owner review is distinct from
T012 approval. No production architecture/RTL/XPR/XDC change or system signoff.

T024 final result: all seven gates PASS, exit 0 on attempt 2
(`evidence/runs/T024/attempt-2-20261105T025313197475Z.json`). All 19 registered
regression targets passed, plus explicit coverage and fresh evidence collection.
The collector binds 32 current receipts across 27 profiles. Final audit checks
66 receipts, 984 artifacts and 71 current sources. Scoped results remain
pipeline 2,008 retirements, ISA 6,364, random 14,458, stress 9,840 main plus
52 pre-reset retirements/28 reset windows; finite stress coverage 49/49 reachable.
Repeated runs do not expand coverage claims. The first 45-second reference-core
lint timeout and rejected closure remain failed; only its bounded runtime changed
to 90 seconds before the complete retry. See [full review](DV_CLOSURE.md).
T024 is awaiting owner review, T025 unstarted; formal remains owner-skipped/NOT
RUN. Simulation and synthesis lint provide no routed timing/hardware/ASIC proof.

## Owner approval recorded 2026-11-04

T024 owner approval recorded 2026-11-04: explicit reply Approve T024 and authorize the command; verified every review-ready package hash before executing python -B scripts/harness.py approve T024 --confirm-owner-review, PASS exit0. Owner/command records evidence/owner_reviews/T024-2026-11-04{,-command}.json bind reviewed cfe2910 package and missing formal acknowledgment. T024 completed; state owner_reviews acknowledges T023, which stays skipped/NOT RUN/attempt1. No original receipt changed. Progress24/41 mandatory completed plus1 owner-skipped; next dependency-ready T025 board top/pinmap/XDC/100MHz constraints, no active task. Commit approval/docs/reports first, query actual next and begin T025 from clean baseline. Reviewed architecture hash403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03 unchanged. Actual runtime unrestricted/never, attended only. No unattended automation/install/download/push/scheduler/programming or formal/timing/hardware/ASIC result.
