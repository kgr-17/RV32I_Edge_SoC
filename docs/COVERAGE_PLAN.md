# T021 measured functional coverage

Completed November4 on attempt2; all five gates and full18-target regression PASS.
Prepared after T020 completion commit1dd0f88. Five reachable coverage gaps remain.
This task defines a finite coverage inventory and reports gaps; it does not
declare verification closure or an arbitrary100% goal. T024 remains owner review.
No production RTL/architecture/old benches/XPR/XDC change is made.

The actual `tb_coverage.sv` pipeline bench retains every T020 assertion, reset/RF
probe and T019 collision/progress/fullRAM/retirement/drain/error guard. It replays
the same six seeds, retains all50 original cases byte-for-byte, and appends one
directed jump/MEM collision as case50 (51 total per seed). Added counters sample actual EX-stage
signals at rising edges, not inferred co-occurrence from final program success.

Instruction inventory: all40 reviewed RV32I families and nine initial EEI fault
classes must be present in every seed after full actual R/F/G/M trace equality
with the independent ISS. ECALL/EBREAK are terminal faults, not successful
retirements. This is finite family coverage, not official architectural tests.

Cross inventory: eight EX groups (ALU/upper,load,store,branch,jump,FENCE,SYSTEM,
illegal/fetch-fault) times eight features =64 bins. Features are valid EX sample,
EX/MEM forwarding, MEM/WB forwarding, unresolved-load blocked operand, older
MEM hold, simultaneous I offer stall, simultaneous D offer stall, and a taken
legal redirect deferred by older MEM hold with operands available. Classification
uses observed EX instruction opcode plus illegal/fetch-fault qualification;
individual instruction-family coverage independently uses matched ISS execution.
Counters include repeated held edges and speculative/killed instructions. They
are microarchitectural samples, not distinct instructions or committed effects.
In particular, deferred_redirect measures the taken/aligned branch-unit predicate
with mem_hold and both operands unblocked. It counts a redirect candidate even
if an older fault kills that work; it is not a count of committed redirects.
Only the independent matched retirement stream establishes architectural control
flow. Operand-value distributions, branch-condition crosses and exhaustive lane
crosses are outside this finite matrix and remain coverage scope gaps.

Exactly15 structural exclusions have explicit reasons: FENCE/SYSTEM/illegal
tokens do not enable register operands, so their EX/WB forwarding and load-blocked
crosses are excluded (9); only branch/jump can redirect, excluding deferred
redirect for the other six groups (6). The decoder and forwarding code were
inspected for these conditions. An observed excluded hit FAILS the collector;
it cannot be discarded. These are structural justifications, not formal proofs.

The remaining49 crosses are in the inventory. Reachability means no architectural
or structural reason currently excludes them; it does not promise every finite
program hits them. Every group's EX sample, every feature somewhere and both
branch/jump deferred-redirect crosses are mandatory positive witnesses per seed.
Other unhit reachable crosses are reported explicitly with zero counts; they
are verification gaps for later stimulus/closure review, never relabeled as
unreachable. All40 ISA families/nine faults remain mandatory per seed.

The collector requires64 unique, seed-bound, nonnegative actual bins, exact
configured seed set, vectors/source hashes, successful actual trace producer,
full ISS equality, and positive real assertion witnesses. It writes a timestamped
JSON under evidence/coverage/ with every bin, count, exclusion and remaining gap.
Direct/full-regression runs are distinct receipts but repeat existing programs.
No code/toggle/FSM coverage percentage is claimed.

Eight policy/generator tests challenge incomplete/duplicate/wrong-seed telemetry, hidden
excluded hits, required opcode/feature/cross loss, explicit uncovered-bin retention
and preservation of all old guards/assertion instantiation. On each actual seed,
four altered report inputs (missing bin, excluded hit, missing forwarding feature,
missing required ISA family) must be rejected;24 report mutations total. These
test the collector, not an injected DUT defect. Existing actual corrupt-expected
and empty simulations remain required, with exact markers/diagnostics/waveforms.

Reproduce:

```powershell
python -B scripts/verify.py coverage
python -B scripts/harness.py finish T021 --evidence evidence/daily/T021.md
```

Manifest adds one instrumented actual pipeline backend. The shared trace parser
adds only exact COVERAGE tags, preserving every old prefix/default. Registry
adds coverage to the full18-target regression; original lint/coverage gates remain
and T021 also requires full regression. No timeout, seed, check or attempt limit
is weakened. Runtime remains unrestricted and attended; outputs stay project-local.
In-flight reset/formal/SoC/IRQ/routed timing/physical FPGA/ASIC require later work.

## Preserved first failure and stronger stimulus

Attempt1 `T021/attempt-1-20261104T235927222071Z.json` passed lint/whitespace but
failed direct and full-regression coverage on missing jump/deferred_redirect.
Actual six-seed functional backends passed; the independent parent matched
seed1 trace before failing its coverage requirement. Actual branch/jump witnesses:
seed1 62/0,7 59/0,101 62/19,20261102 75/25,314159 68/46,271828 49/0.
The direct/refreshed parents both retain the failure. Archive31 exact source
inputs and12 vector/waveform hashes in evidence/failed_sources/T021/attempt-1/.

The requirement is retained. New case50 initializes RAM to0xa5, executes LUI,
priming LW, older SW, JAL over a wrong-path store, ADDI consuming the link, then
EBREAK. Its I responses use deterministic minimum latency and both D responses
wait32 edges. All old cases retain their input bytes/timing logic; no seed is
replaced. A per-case guard requires increased jump/MEM witness, so random hits
elsewhere cannot mask a vacuous new scenario. Literal anchors check PCs
0/4/8/12/20, link16, dependent17, loaded0xa5a5a5a5, successful store word4=0
and wrong-path word8 retained0xa5a5a5a5. Expected totals now14,488 retirements/
306 cases/34,072 ordered events; actual repaired results pending attempt2.
The added six runs replay one new directed program, not new random programs.

## Repaired direct simulation (full regression pending)

Direct `coverage-report-20261105T001819254615Z.json` PASS39 checks/5 commands;
actual backend `coverage-20261105T001821458684Z.json` PASS29/14. Six seeds match
14,488 retirements/306 faults/9,486 GPR words/9,792 RAM words =34,072 events.
All49 ISA family/fault bins per seed, real assertion witnesses and24 report
mutations pass; actual corrupt/empty simulations rejected. Every new directed
case50 passes its explicit nonvacuity guard. Global jump/MEM sampled witnesses
are32/32/56/57/78/32 for seeds1/7/101/20261102/314159/271828.

Aggregate64 matrix rows:44 of49 reachable hit,5 reachable gaps,15 justified
exclusions retained and no excluded hits. Per-seed hit counts41/41/44/42/44/40;
per-seed gaps8/8/5/7/5/9. These totals are a finite inventory, not DV closure.

| Remaining reachable gap | Disposition |
|---|---|
| load / ex_forward | Keep visible; add focused stimulus during later stress/closure work. |
| load / wb_forward | Keep visible; add focused stimulus during later stress/closure work. |
| load / load_blocked | Keep visible; add focused stimulus during later stress/closure work. |
| illegal_fetch_fault / mem_hold | Keep visible; add focused stimulus during later stress/closure work. |
| illegal_fetch_fault / d_offer_stall | Keep visible; add focused stimulus during later stress/closure work. |

Source report: `evidence/coverage/2026-11-04_20261105T001819254615Z.json`. Full18-target regression still pending.
No zero bin is reclassified or removed. In particular the load-base invariant
in random programs leaves load-address producer dependencies unexercised.

## Final completion evidence

T021 completed November4 on attempt2, all five gates PASS exit0 including lint/coverage/full18-target regress/both whitespace: evidence/runs/T021/attempt-2-20261105T001339775353Z.json. First mandatory jump/MEM coverage failure preserved with31-input archive/12 artifact hashes. Repair retained all original50-case bytes/seeds/requirements and appended case50 with priming LW/olderSW/JAL and per-case positive witness. Repaired direct coverage-report-20261105T001819254615Z.json and replay coverage-report-20261105T002535232641Z.json PASS39checks/5commands each; actual backends29/14. Both compare14488R+306F+9486G+9792M=34072events, all40ISA families/nine faults per seed, real assertion witnesses,24 report mutations plus actual bad/empty negatives. Added six runs of one new directed program;48 original random programs unchanged. Aggregate64 crosses:44/49 reachable hit,5 uncovered,15 structurally excluded with zero excluded hits. Gaps remain load/{ex_forward,wb_forward,load_blocked} and illegal_fetch_fault/{mem_hold,d_offer_stall}; retain for focused stress/closure stimulus, no DV closure or100% claim. Jump/MEM witnesses32/32/56/57/78/32. Completion audit60receipts/724artifacts/64current sources and4 first-version receipts bound to archive; preservation736 historical files/two report prefixes/23 originals. All production RTL/architecture/old SV/XPR/XDC/kit unchanged; parser adds only exact COVERAGE tag. Eight policy/generator tests pass. Versions unchanged Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. State22/41 mandatory complete, active null; next expectedT022, query before begin. Review diff/whitespace, commit inspected files and record commit. Next session read latest handoff/required contract files, daily --supervised, recover active task; no unattended execution under unrestricted runtime, install/download/push/scheduling/FPGA programming or formal/timing/hardware/ASIC claim.
