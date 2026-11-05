# T024 simulation DV closure review

Status: AUTOMATED GATES PASS on attempt 2; AWAITING OWNER REVIEW, 2026-11-04.
Baseline b45d043 contains the owner's explicit T023 skip and guarded workflow.
This package concerns the reviewed v0.2 five-stage CPU and local fabric model.
It does not approve SoC/peripherals, interrupts, routed FPGA, hardware or ASIC.

## Owner exception and decision

The owner explicitly requested: "yes, make this task mark as skip. and work on
others". T023 is skipped, with formal verification NOT RUN and zero formal tasks.
The original attempt remains intact; no proof or completed task is claimed.
Authorization: evidence/owner_reviews/T023-skip-2026-11-04.json, bound by
BACKLOG.owner_skip_policy and state.owner_skips. Only T023 is covered.
This lowers verification assurance relative to the original formal requirement.
T024 and final owner review must acknowledge the missing formal evidence.
The formal drafts remain available for a future owner-directed revisit.

The requested T024 decision, with fresh gates now passed, is whether the scoped CPU
simulation evidence is sufficient to proceed to T025's SoC/board planning with
this exception. It is not final system signoff or authority to install tools,
program the FPGA, push code, schedule unattended work or change architecture.

## Architecture and observed interfaces

Owner-reviewed architecture identity remains
403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03.
No ISA, clock, target, reset priority, map, production RTL, XPR or XDC change is
made by T024. The existing XPR is still empty of integrated SoC sources/top;
reproducible non-project checks exercise actual units/core modules.

One synchronous core clock; reset > oldest eligible fault > older memory hold >
redirect > load-use > advance. Local I/D each permit one accepted unanswered
transaction, stable valid/payload until acceptance, response latency >=1 edge,
no consume-edge replacement. D address is original byte EA; byte enables apply
to reads and writes. Successful response acceptance commits effects; WB retire
comes later. Reset cancels unfinished shared-endpoint work and preserves already
committed modeled memory. Faults terminate precisely and remain sticky.

Successful trace fields include64-bit order, PC/nextPC/instruction, GPR enable/
destination/data and original memory address/mask/read/store metadata. Fault
termination is separate. Independent comparisons check every event in order,
terminal x1..x31 and32 RAM words; SV checks complete64KiB RAM plus memory-effect,
request/response and retirement accounting. These are project trace ports, not
RVFI/certification. The independent ISS imports no RTL semantics; it is the same
ISA oracle reused by comparator/scoreboard, not two independent ISA interpreters.

## Requirement/evidence inventory

Counts below are expected scoped totals from established programs. Fresh T024
receipts will be bound before review. Replays do not add unique coverage.

| Scope | Traceable acceptance evidence |
|---|---|
|T004..T014 scalar/storage units|Independent corner/encoding/bypass/lane/hold/priority tests; retained unit baseline1,185,178 vector comparisons|
|T009 memory agent|49,276 seeded protocol edges, reset cancellations and exact accept/response/effect accounting; model evidence|
|T010/T011 reference core|324 successful retirements/22 cases across two seeds, complete independent event/GPR/RAM sample comparison|
|T015..T018 actual pipeline|Dependency, held-WB refresh, wrong-path suppression, precise older faults and killed offered-fetch drain; four-seed ISS total2,008 retirements/168 cases|
|T041 directed ISA/EEI|All40 base families/nine fault codes,23 semantic requirements,6,364 retirements/632 cases; FENCE waits/effects and valid-address I/load-x0/store errors|
|T019 random programs|Six seeds/14,458 retirements/300 scenarios, including48 random runs and11,446 random-only retirements;40 random-only families per seed|
|T020 assertions|Actual RF x0 ports, retirement order/canonical destination, reset, offer stability, one-outstanding responses and sticky faults; six positive seeds and16 isolated intended violations|
|T021 finite coverage|64 EX group/feature rows,49 reachable and15 justified exclusions; original corpus hits44, reports five gaps|
|T022 stress|Four seeds1/314159/20261104/424242;9,840 main retirements/240 cases;52 pre-reset retirements checked in SV;28 selected reset windows; added programs hit all49 reachable crosses|
|T023 formal|OWNER-SKIPPED/NOT RUN, zero formal tasks; explicit missing-assurance exception|

## Negative tests and failure history

Real corrupt-expected and empty-input XSim runs remain in actual unit/core
backends. XSim `$fatal` can exit0, so exact failure diagnostics and missing success
markers are required. Actual random traces undergo36 streaming scoreboard and18
comparator mutations per six-seed execution. Assertion negatives must emit their
specific property ID; arbitrary fatal/native failure cannot satisfy them. Coverage
report mutations expose missing bins/features/ISA or hidden excluded hits. Stress
RESET_LEAK=1 must trigger exact modeled-RAM retention failure with a waveform.

Known recovered issues remain available, not erased: T015 initial synthesis
timeout followed by finite120s CPU budget; T017/T019 native Vivado exit failures;
T020 native XSim failure before a required negative diagnostic, identical retry
passed; T041 FENCE nonvacuity stimulus strengthened with priming load; T021 missing
jump/MEM overlap on three seeds fixed by dedicated case50 and positive per-case
witness. First-source archives and raw failed attempts remain committed. Native
tool failure causes remain undetermined. Fresh required functional failures,
missing checks, stale sources or missing artifacts must block this review.

## Fresh gate and evidence policy

T024 retains lint, full19-target regression and explicit coverage, and adds workflow
policy checks plus a closure collector. The collector reads only the authoritative
current T024 attempt journal, requires all preceding argv/order/status/exit codes
to pass, validates all19 regression child records, and follows their actual receipt
references. It never searches for an older passing run. Referenced tool records
must start after this attempt, pass all checks and match source/tool/artifact
hashes. Both regression and explicit coverage runs must be present. A canonical
hash of completed prefix commands binds the snapshot without hashing a mutable
running journal as if finished. Final audit rechecks that prefix after finish.

Five collector-policy tests challenge missing/reordered/NOT RUN gates, stale or
failed tool records, source/tool drift and nested metadata parsing. Current
controller tests additionally reject forged/tampered owner skips and lost history,
and retain successor/final human review. These tests are infrastructure evidence.
Fresh simulation gates establish CPU results; neither substitutes for formal.

Commands:

```powershell
python -B scripts/harness.py finish T024 --evidence evidence/daily/T024.md
```

Gate order: workflow-policy, lint, regress, coverage, test-dv-closure, working and
staged whitespace. Max3 task attempts; all failures remain. If all pass, the
harness stops at awaiting_review. Only the owner may authorize the specific T024
approval command after inspecting this completed package. T025 is not started
before that approval. No formal tool installation is needed for the skipped task.

## Remaining limits

No formal proof, exhaustive operand/state/reset/cross closure, full protocol
liveness or clock-domain proof. Seven reset windows use falling-edge assertions
and a shared fabric model; no isolated core reset against live memories. Stress
covers the finite49-bin inventory, not all possible microarchitectural scenarios.
Random data accesses fit the low128-byte RAM window; full RAM is separately SV
checked, with independent terminal sampling and observed store effects.
No official RISC-V compiler test suite/certification or C firmware toolchain result.
No SoC/MMIO/interrupt/board constraint/routed timing/power/hardware/ASIC signoff.
Those remaining mandatory milestones and owner execution/review gates remain.
Current runtime is unrestricted and attended only; the harness is not a sandbox.

## Retained T024 first attempt and bounded runtime repair

Attempt1 `evidence/runs/T024/attempt-1-20261105T024017738840Z.json` reports
PASS/FAIL/PASS/PASS/FAIL/PASS/PASS: policy/lint/regression/coverage/collector/
whitespace. All19 functional regression targets and explicit coverage passed.
Reference-core lint timed out at45s even though synthesis/DRC had zero warnings
or errors and emitted the exact success marker; process cleanup observed exit0.
TIMEOUT is still FAIL. The collector correctly refused the failed prefix rather
than using an older pass. Archive101 source inputs and160 generated report/list
hashes: evidence/failed_sources/T024/attempt-1/.

Only this probe's finite wall-clock allocation changes45->90s, using the existing
per-design mechanism and120s cap. Pipeline CPU120s, other default45s, actual
diagnostic/negative/functional checks, seeds, task3attempt limit and all other
gates remain. No RTL/architecture/clock/timing-constraint change. Attempt2 reran
every required gate with current manifest hashes and passed.

## Final results and owner review

Final task receipt:
`evidence/runs/T024/attempt-2-20261105T025313197475Z.json`.
All seven gates PASS, exit 0: workflow-policy, lint, full regression, explicit
coverage, test-dv-closure, working-tree whitespace and staged whitespace.
Workflow tests: 43 controller, 16 architecture and 5 execution-budget tests plus
architecture consistency. Closure-policy tests: 5. Lint: 29 checks/16 commands.
Full regression: all 19 registered subcommands passed. No check is waived.

Collector receipt:
`evidence/toolchain_runs/dv-closure-20261105T030748742605Z.json`.
It binds 32 current tool receipts across all 27 required profiles, both coverage
runs, replayable seeds, exact comparison totals above and the formal exception.
`evidence/t024-review-audit-2026-11-04.json` validates 66 receipts, 984 artifacts,
71 current source hashes and the completed journal prefix after finish. The
first failed lint and collector remain failures; archived source bindings are
used only to preserve their provenance. Pre-gate task evidence snapshots remain
in `evidence/prepare/T024-gate-evidence-2026-11-04.json`.

The final preservation audit retains 886 earlier files after excluding the
documented config/loop runtime repair and README status update, the complete historical L1 report prefix,
both daily report prefixes and all 23 original baseline files. No architecture,
RTL, XPR, XDC or kit file changed. Simulation success and synthesis lint do not
establish routed timing or physical hardware operation.

Please review the architecture/interfaces, independent comparison scope, negative
tests, bounded runtime repair, remaining limits and explicit T023 NOT RUN
exception. T024 remains awaiting_review, with no active task. Progress remains
23 completed mandatory milestones plus one owner-skipped, out of 41. T025 has
not begun. If accepted, explicitly authorize this owner-reserved command:

```powershell
python -B scripts/harness.py approve T024 --confirm-owner-review
```

Approval acknowledges this scoped simulation package and the missing formal
proof. It releases T025 planning; later architecture and execution review gates
remain required. Until that authorization, resume by reading the latest technical
handoff and required contract files, running daily --supervised, inspecting Git
and this review package. Do not rerun finish, self-approve or begin T025.
