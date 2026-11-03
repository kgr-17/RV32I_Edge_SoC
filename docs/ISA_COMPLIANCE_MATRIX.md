# T041 directed RV32I / initial EEI review matrix

November 2, 2026, America/Los_Angeles. **All five gates passed; owner approved November 2.**
Formal attempt2 passed after retaining the first nonvacuity failure. This matrix covers the declared
40-instruction RV32I 2.1 core and owner-approved v0.2 fault-halt EEI. It records
finite directed tests and their limits; it is not RISC-V certification, exhaustive
proof, privileged-ISA support, or final SoC/hardware signoff.

Architecture identity remains SHA256
`403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03`.
T002 architecture and T018 pipeline owner approvals are recorded. T018's approval
acknowledgment is commit `bf52dd4`; no new architecture change is proposed here.
Production RTL, ports, ISA, map, reset/flush priorities, clocks, XPR/XDC and the
original kit remain unchanged. T041 priority185 precedes T019 priority190;
the previous handoff's T019-first assumption was rejected by the harness and
corrected, without bypassing selection or starting two tasks.

## Instruction matrix

Every row requires an actual executable-pipeline trace matched to the independent
ISS, including successful retirement metadata or the specified precise fault.
All 40 instruction-family bins and nine diagnostic codes are required per seed.
The independent model does not consume the hand-written expected rows. The
hand generator separately checks every expected retirement/fault against that
model before actual RTL execution; this tests the stimulus as well as the DUT.

| Instruction | Directed semantics / corner classes |
|---|---|
| LUI | Upper immediate, negative/high bits, x0 harmless destination |
| AUIPC | PC addition, upper immediate, last-ROM-word result wrap, x0 |
| JAL | Link, redirect/kill, aligned target, misalignment fault, negative target wrap |
| JALR | Link, loaded source, immediate sign, bit0 clear before alignment, 32-bit addition wrap |
| BEQ | Taken/not taken, bad target only on taken branch |
| BNE | Taken/not taken, bad target only on taken, bounded backward loop |
| BLT | Signed negative/positive relation; taken/not-taken misalignment |
| BGE | Signed relation including negative boundary; target qualification |
| BLTU | Unsigned high-bit relation; target qualification |
| BGEU | Unsigned high-bit relation; target qualification |
| LB | Every byte lane, sign extension, high-address final byte, x0 access fault |
| LH | Both aligned lanes, sign extension, high boundary, alignment before map |
| LW | Raw word, data dependence, ROM reads, RAM last word, wrapped address, x0 error |
| LBU | Every byte lane, zero extension, final byte, x0 error |
| LHU | Both aligned lanes, zero extension, alignment priority, x0 error |
| SB | Each lane, shifted payload/mask, dependent store payload |
| SH | Each aligned halfword, masks, misalignment fault before any request |
| SW | Full word, dependency, ROM/unmapped/error faults with no failed byte effects |
| ADDI | Positive/negative immediate limits, result wrap, NOP and x0 HINT |
| SLTI | Signed comparison with -2048/-1/0/1/2047 |
| SLTIU | Sign-extended immediate compared unsigned |
| XORI | Sign-extended immediate and six-value operand set |
| ORI | Sign-extended immediate and six-value operand set |
| ANDI | Sign-extended immediate and six-value operand set |
| SLLI | Amount0/1/31, shifted-out bits; invalid upper encoding rejected |
| SRLI | Logical zero-fill at0/1/31, invalid upper encoding rejected |
| SRAI | Signed right shift at0/1/31, valid funct7 and illegal alternatives |
| ADD | Six-value operand cross, carry/wrap, dependent readback, x0 |
| SUB | Six-value operand cross, borrow/wrap, signed boundaries, x0 |
| SLL | Six-value cross, low-five-bit shift mask including32 |
| SLT | Six-value signed cross including80000000/7fffffff/ffffffff |
| SLTU | Same cross interpreted unsigned |
| XOR | Bitwise cross, high bits and x0 |
| SRL | Unsigned logical shift with masked register amount |
| SRA | Arithmetic shift with masked register amount |
| OR | Bitwise cross and x0 |
| AND | Bitwise cross and x0 |
| FENCE | Older delayed SW, then FENCE, then younger LW/SW; all ignored fields tested |
| ECALL | Exact encoding, code8/tval0, older store completes, younger store killed |
| EBREAK | Exact encoding, code9/tval0, older store completes, younger store killed |

ALU integration values are0,1,ffffffff,80000000,7fffffff,32, with all36 pairs
for all ten register operations; immediate extremes and shifts supplement them.
Existing unit evidence provides larger scalar/decoder/LSU spaces, but cannot be
substituted for the new integration runs. This is finite corner coverage.

## EEI and encoding matrix

The original42 T018 cases and all their collision/nonvacuity checks remain an
exact stimulus prefix. New116 cases bring each seed to158 scenarios and1587
expected successful retirements originally; the preserved first attempt lacked
the EX-stage FENCE-wait witness. The strengthened stimulus below has1591
retirements and8799 input rows per seed, with the same158 scenario IDs.
Seeds1,7,101,20261102 are replayable. The23 named semantic requirements and
per-seed scenario IDs are exported in a machine-readable evidence/isa matrix.

| Requirement | Test behavior and acceptance |
|---|---|
| FENCE drain / ignored fields | Cases42..45 use0000000f,0ff0000f,8330000f,ffff8f8f. A priming LW fills the fetch queue; FENCE must wait in EX behind older SW. All four cases need positive EX-wait count, exactly four successful memory effects (two older and two younger) and no younger effect before FENCE retirement. Ignored rd/rs1/fm/pred/succ do not write/read GPRs or make the instruction illegal. |
| Legal HINTs | LUI/AUIPC and all register/immediate ALU operations with rd=x0 remain harmless; canonical NOP; source GPRs read back unchanged. |
| Illegal M/CSR/system | All eight M funct3 operations, six CSR forms, MRET/WFI/SFENCE-like encodings and nonexact ECALL/EBREAK fields terminate code1. No extension is silently enabled. |
| Illegal fields/extensions | Bad branch/JALR/load/store/shift/register/FENCE funct fields, FENCE.I, compressed/zero/all-ones, atomic and floating encodings terminate code1 with original instruction tval. |
| Alignment before map | LH/LHU/LW and SH/SW misalignments in valid RAM and unmapped space terminate code4/6 before any data request; loads use rd=x0 too. |
| Branch target alignment | All six branches taken to a two-byte-only target fault code2; each corresponding not-taken branch completes normally. JAL/JALR cases also check links are suppressed on misalignment. |
| Access and wrap | Data ROM read allowed, ROM write fault, inaccessible address errors; 32-bit address/target arithmetic, negative JALR immediate, bit0 clearing and last-word boundaries. |
| In-range bus error | Case46: instruction error at ROM0 reports instruction0/code3. Case47: LW x0 at RAM10000 errors code5. Case48: SW to the same valid RAM errors code7 and changes no bytes. Explicit error-word metadata configures the ISS; the SV bus independently drives these errors. |
| Precise termination | Fault PC/instruction/code/tval compared; faulting instruction never retires/writes; older work completes and younger memory is suppressed; sticky halt and old fetch drain preserved. |

Codes1..9 are project diagnostics, not privileged mcause. Misalignment precedes
map/error checking. ECALL/EBREAK provide fatal termination until reset in this
reviewed EEI. Failed stores have no byte effects; loads to x0 still access/fault.
FENCE conservatively orders older memory/I/O responses and younger effects under
one-outstanding buses, even when fm/pred/succ would otherwise request less. The
test memory is ROM/RAM; actual peripheral behavior is separately verified later.

## Execution and evidence policy

`dv/integration/test_isa_complete.py` supplies hand expectations and eight tests.
`tb_isa_complete.sv` instantiates the actual pipeline, retaining complete ordered
retirement, full64KiB RAM, request stability/one-outstanding, duplicate/effect
accounting, bounded progress, sticky fault and killed-fetch drain checks. The
four FENCE cases use deterministic fast IF to force the required collision;
the remaining new cases use variable bus timing with a first32-edge data wait.
All original42 timing modes and requirements stay unchanged.

`retire_checks.py --unit isa_complete` additionally compares the independent
ordered retirement/fault trace, all31 stored GPRs and32 terminal RAM sample
words per case. The sample covers128 bytes at10000; boundary effects are also
carried in complete memory retirement records, and full RAM is checked by SV.
Three actual-trace mutations per seed plus real corrupt-expected/empty XSim runs
must fail. XSim raw exit0 cannot override a fatal diagnostic or missing marker.

`isa_complete_checks.py` rejects missing/stale/newest-failed comparisons, wrong
source/contract/backend hashes, missing families/faults/seeds/state/mutations,
and missing/duplicate/zero-wait/malformed FENCE runtime evidence. It saves the
40+9 family/fault matrix,23 semantic requirements, actual FENCE telemetry and
source/vector/wave/normalized-trace identities. Four matrix-policy and six
inherited acceptance-policy tests supplement the actual comparisons.

The new ISA backend receives a finite120s aggregate child budget for four larger
program sets, within the existing runner cap. Per-XSim30s, version timeouts,
all diagnostics/negatives, three task attempts and process-tree cleanup are
unchanged. No timeout or missing check can pass. Existing backends keep60s.

From the project root, formal finish runs:

```powershell
python -B scripts/verify.py lint
python -B scripts/verify.py test-isa-complete
python -B scripts/verify.py regress
git diff --check
git diff --cached --check
```

The full regression was added to T041's required commands because shared trace
parsing/checker/manifest changes need old-backend validation. Both original
required targets remain; the regression now has15 targets including this suite.
Versions remain Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2
build6299465. Actual exit codes, receipts, seeds, trace/wave paths and results
are appended below. Sources and artifacts remain project-local.

Preparation evidence includes a failed `-m unittest` import of the new checker:
the sibling scripts directory was missing from that invocation's import path.
Added the explicit project-local path; its four policy tests now pass. The
failure remains under evidence/prepare; no RTL, test expectation or gate changed.

Formal attempt1 retained: lint and both whitespace checks passed; the new ISA
target and full regression failed the same case42 FENCE nonvacuity guard. All11
retirements/three memory effects in that failed case match the independent ISS,
but FENCE arrived in decode after a memory hold froze empty EX. This was not an
EX-wait witness. Archived33 exact first inputs and failure waveform/vector hashes
under evidence/failed_sources/T041/attempt-1. Added an older priming LW to each
FENCE case so the answered-fetch queue fills before SW/FENCE; retained the
positive EX-wait requirement and younger-effect prohibition. Exact effects
change3 to4 because there is one added older read, not a loosened threshold.
Removed an accidental FENCE-seen assignment from expected-row parsing; only
actual retirements set that monitor. No production RTL, original42 scenarios,
timeout, fault expectation, seed, diagnostic filter or prior test changed.

## Review limits and next step

The selected ISA and EEI remain the approved local contract; no extra extensions
or privileged software support are implied. Official compiler-based architectural
suites are NOT RUN (no matching compiler/test adapter installed or downloaded).
No RISC-V certification or exhaustive encoding/state proof is claimed. Random
instruction generation T019, assertions/coverage/reset/formal T020..T024,
SoC/MMIO/interrupt T044/T045, FPGA implementation/timing/physical validation and
ASIC remain separate mandatory milestones. In-flight shared-reset testing is
T022; case-boundary resets here cannot close it. Warm reset/CDC policy is unchanged.

After all required commands pass, T041 requires owner review of this finite
matrix and EEI results before T019 may begin. Do not self-approve or change the
architecture to accommodate a failing test. Unrestricted runtime still permits
attended work only; no unattended scheduler or hardware programming is enabled.

## Actual acceptance results

Formal receipt `evidence/runs/T041/attempt-2-20261103T050224175926Z.json` records
all five commands PASS/exit0: lint, test-isa-complete, full15-target regression
and both whitespace checks. State is **awaiting_review**, attempt2, active null;
18/41 mandatory tasks are completed, with T041 awaiting the owner's acceptance.
The first failed attempt and exact33-source archive remain preserved. No
production RTL repair, seed/diagnostic/timeout reduction or waived gate was used.

| Seed | Cases | Retirements | Faults | Ordered events | FENCE EX-wait edges for cases42/43/44/45 |
|---|---:|---:|---:|---:|---|
| 1 | 158 | 1591 | 158 | 11703 | 27 / 31 / 23 / 4 |
| 7 | 158 | 1591 | 158 | 11703 | 6 / 13 / 17 / 9 |
| 101 | 158 | 1591 | 158 | 11703 | 12 / 1 / 31 / 2 |
| 20261102 | 158 | 1591 | 158 | 11703 | 3 / 8 / 16 / 27 |

Total **46,812 independently matched ordered events**:6,364 successful
retirements,632 faults,19,592 GPR words and20,224 RAM sample words across632
scenario runs. Each seed hit all49 required instruction/fault bins and all23
semantic requirements. All16 FENCE witnesses have positive EX wait (230 edges
total) and exactly4 successful effects, with no premature younger effect.
All12 in-range injected I/load/store-error cases match; failed stores preserve
RAM. All12 actual-trace mutations and real corrupt-expected/empty XSim negative
runs were rejected. Original42-case collision, full-RAM, protocol, progress and
halt/drain requirements remain passing. No scoped functional mismatch was found.

The ISA target executes28 Python policy/generator/oracle tests, actual XSim and
the independent checker. Direct receipts under `evidence/toolchain_runs/`:

- `lint-20261103T050224552732Z.json`:29 checks/16 commands, zero errors/warnings
  for positive probes and deliberate latch rejection.
- `isa_complete-20261103T050657756425Z.json`:23 checks/12 commands, four
  positive seeds plus real negatives,8799 input rows/seed (not instruction count).
- `isa-complete-20261103T050655578975Z.json`:30 checks/5 commands, actual ISS
  equality, normalized trace hashes and mutation diagnostics.
- `isa-matrix-20261103T050719949524Z.json`:132 checks; matrix
  `evidence/isa/2026-11-02_matrix-20261103T050719949524Z.json` binds all
  40 instruction rows,9 fault rows,23 semantic requirements and runtime telemetry.
- Full-regression replay: `isa_complete-20261103T051158213476Z.json`,
  `isa-complete-20261103T051156053418Z.json`, `isa-matrix-20261103T051220312513Z.json`
  and `evidence/isa/2026-11-02_matrix-20261103T051220312513Z.json`; same counts.

Repeats are not extra unique instruction coverage. Workload cycles
14445/14903/14595/14557 include waits, resets between cases and halt/drain; no
steady-state CPI, Fmax or physical timing claim follows. Versions, exact argv,
exit codes, stdout/stderr, vectors, waves, Tcl, argument files and source hashes
are retained in the nested receipts. The preservation audit and review-ready
receipt bind this document and the recoverable local Git package before approval.

Owner review should focus on FENCE ordering/ignored fields and its actual EX
witness, precise fault age/effect rules, x0 accesses, illegal instruction policy,
alignment precedence, boundary arithmetic, independent-vs-hand expectations,
the retained failed attempt and the explicit certification/SoC/formal/reset gaps.
Accepting this scoped directed matrix permits the next eligible task to proceed;
query the harness (T019 is currently expected) rather than assuming a task order.

## Owner acceptance

The owner explicitly answered "Approve T041 and authorize that command" for
`python -B scripts/harness.py approve T041 --confirm-owner-review`. Before
execution, every review-ready and source-audit hash matched package `9f37135`,
including submitted document SHA256
`cba59ddc6c18257e7b3f7c52640e57dfec0c36f7f82db9c90733c00c850478c2`.
The authorized command returned PASS/exit0; T041 is completed. An actual `next`
query selected T019. Exact authorization/raw-command receipts are
`evidence/owner_reviews/T041-2026-11-02.json` and its `-command.json` companion.
Earlier pending-state text describes the submitted review. Scope, limits,
measurements and preserved failures remain the accepted package. This approval
grants no tool-installation, scheduling, programming or architecture-change scope.
