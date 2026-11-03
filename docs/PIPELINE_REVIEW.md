# T018 executable pipeline milestone review

Prepared November 2, 2026 (America/Los_Angeles). **Owner approved November 2.**
This is the L2 directed pipeline milestone, not final CPU/SoC completion.
All six required commands passed on formal attempt 1; the harness now records
`awaiting_review`. Results and actual receipt identities follow below.

## Reviewed implementation and architectural boundary

The owner approved architecture v0.2 at T002 and the L1 reference milestone at
T012. Their historical proposal fields remain unchanged; acceptance is recorded
in `.harness/state.json` and owner-review receipts. Architecture contract SHA256:
`403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03`.
The target remains Basys 3 / xc7a35tcpg236-1, one core clock, synchronous active
high core reset, little endian, IALIGN32 and the initial nine-code fault-halt EEI.
Later interrupts require the separate T044/T045 architecture and verification.
No architectural interfaces, ISA, map, priorities, clocks or reset policy change
in T018; production RTL is byte-identical to the T017 baseline commit `b30b152`.

`rtl/core/pipeline_cpu.sv` contains the executable `pipeline_core` module.
`rtl/core/pipeline_core.sv` contains reusable stage storage, not another CPU.
The pipeline is independent of `reference_core.sv` and shares the separately
tested decoder, ALU, GPR, branch and LSU components.

| State / path | Behavior to review | Evidence developed |
|---|---|---|
| IF and answered-fetch queue | One unanswered request, stable offered PC; three answered instruction slots feed decode; no cache or prediction | T015/T016/T017 |
| ID and EX | GPR reread/bypass; nearest eligible older result, no not-ready load forwarding; held operands capture transient WB data | T006/T013/T014/T015 |
| MEM | At most one data request; younger stages wait; successful response acceptance controls memory effects | T009/T015/T017 |
| WB | One ordered successful retirement or sticky precise fault; no retirement of faulting/younger instructions | T015/T016/T018 |
| Arbitration | reset > oldest fault > memory hold > redirect > load-use > advance, with age eligibility | T015/T016/T017 |
| Redirect and halt | Kill younger buffered/decode work; preserve and drain a previously offered/accepted stale fetch | T016/T017 |

Retirement exposes order64, PC/instruction/next-PC32, GPR write flag/index5/data32,
memory valid/write flags, original byte address32, byte enables4, lane-positioned
write data32 and full aligned response word32. The separate sticky fault exposes
PC32, instruction32, code4 and tval32. Instruction and data buses have separate
valid/ready request and response channels; data request includes address32,
write flag, data32 and byte enables4. Reset suppresses acceptance and retirement.
No external port changed in T018. Detailed interfaces and arbitration rationale:
PIPELINE_REGISTERS.md, FORWARDING.md, LOAD_USE.md, CONTROL_FLUSH.md, BACKPRESSURE.md.

## Independent comparison and reproducibility

`dv/reference/rv32_iss.py` executes from initialized program/data bytes. It does
not import DUT RTL enums/expressions or the assembler's hand-written expected
results. `stimulus_images` deliberately ignores all expected-result rows.
`test_pipeline_iss.py` corrupts every such row and requires the ISS result to
remain identical, alongside literal parser and rejection tests.

`scripts/retire_checks.py --unit backpressure` runs the actual XSim pipeline
backend, then compares every ordered successful retirement field, each precise
fault, x1..x31 and 32 terminal RAM words per case. The ISS RAM sample is the
128-byte region at 0x10000; this is not an independent full-RAM dump. The SV
scoreboard separately checks the complete 64KiB RAM and each bus/effect/retire
association, request stability, at-most-one outstanding, bounded progress,
absence of post-halt effects and old-fetch drain. x0 accesses/faults are covered
by instructions and dedicated unit checks; no stored x0 word is inferred.

Both `core` and `backpressure` are explicit backend choices tied to distinct
task/profile/tag identities. Default `core` preserves the T011 reference check;
pipeline output must use the exact BACKPRESSURE tags. Empty, malformed/X-valued,
extra, reordered or mutated events fail the comparison. Each actual seed is
replayed through three comparator negatives: actual bit flip, empty trace and
extra actual event. The XSim backend also executes corrupt-expected and empty
input negative simulations; a marker cannot override a failed process.

Four configured seeds: **1, 7, 101, 20261102**. Each has the 21 deterministic T016
programs, preserving per-case collision checks, and the same 21 programs under
variable IF/D timing. This is random bus timing/data, not random instruction
generation. Required ISS bins are all 40 instruction families and all nine
fault codes; ECALL/EBREAK contribute fault termination rather than successful
retirements. Scalar input-vector counts must not be added to retirement counts.

From the project directory:

```powershell
python -B scripts/verify.py lint
python -B scripts/verify.py test-pipeline
python -B scripts/verify.py test-retire
python -B scripts/verify.py regress
git diff --check
git diff --cached --check
```

`test-pipeline` retains T013 stage storage tests and adds seven pipeline ISS
policy tests plus the actual four-seed ISS comparison. `test-retire` preserves
the independent reference-core comparison. `regress` includes all 14 existing
targets and replays the pipeline ISS route as well. The task's `finish` runs
all six commands and records every status/exit/argv. Tool versions remain
Python3.9.13, Git2.48.1.windows.1, tzdata2026.2 and Vivado/XSim2025.2 build6299465.
Builds, logs, waves, argument files, vectors and normalized traces stay local.

## Evidence boundaries, retained failures and review decisions

T013 storage passed79,022 vectors; T014 forwarding144,424; T015 pending-load
detector74,624 plus128 actual dependency retirements; T016 control502 retirements;
T017 bus stress2,008 retirements/168 scenarios. Those are scoped workloads, not
aggregate unique instruction coverage. The regression's nine scalar/storage
targets total1,185,178 vector comparisons; memory-model49,276 edges and reference
324 retirements are separate measurements.

T015 attempt1 hit the45s CPU synthesis timeout; retained inputs demonstrate no
RTL/oracle/check weakening for its bounded120s CPU-only retry. T017 attempt1
retains a native Vivado exit crash on the unchanged ALU after completion; nonzero
exit correctly failed lint, identical attempt2 passed. Neither failure was
converted into a pass or erased. Native crash cause remains undetermined.

Bus-stress elapsed cycles include case setup/fill, waits and halt/drain. They
are workload/progress telemetry, not steady-state CPI, a reference/pipeline
speedup, clock-period proof or Fmax. The100MHz board target has no routed timing
evidence yet. Non-project synthesis lint checks elaboration/structure, not
implementation timing or physical functionality. The existing XPR/XDC and kit
remain unchanged and recoverable.

Before approval review: independent actual trace equality and negatives;
load-use/store data/JALR and held-WB refresh; memory hold versus redirect and
older fault versus younger store; stale fetch error killed during redirect;
stable offered fetch through halt; separation of observed and expected evidence.
The owner should accept these L2 results and the following explicit remaining
gaps before continuing to T019.

Still required: constrained-random instructions T019, dedicated assertions T020,
coverage closure T021, in-flight reset/stall T022, selected formal T023, final
core DV review T024, full ISA/EEI tests T041, SoC/peripherals/CDC/boot, physical
FPGA validation with owner programming approval, routed timing/power T043,
interrupt architecture/verification T044/T045 and scoped ASIC evidence. No
compiler-based architectural suite, formal proof, routed timing, physical board
execution, interrupt implementation or ASIC signoff is claimed here. Runtime
remains unrestricted and attended; unattended scheduling awaits real isolation.

After successful gates the harness leaves T018 **awaiting_review**. AGENTS.md
and BACKLOG.json reserve owner approval; do not approve it or begin T019 without
the owner's explicit authorization. Exact results and recoverable review-package
identity is recorded in the review-ready receipt after the local package commit.

## Actual T018 acceptance evidence

Formal receipt: `evidence/runs/T018/attempt-1-20261103T041420187535Z.json`.
All six commands listed above executed and returned exit0/PASS. The full
14-target regression also reran the actual pipeline ISS path; it is a replay of
the same four workloads, not another set of unique programs. No T018 attempt
failed. `harness.py validate` returned exit0/valid true with no daily task limit;
T013 through T018 participated today, sequentially. Project status remains in
progress: 17 mandatory tasks completed, T018 awaiting review, later work pending.

| Seed | Retirements | Faults | IF request stalls | D request stalls | Max D age | Workload cycles |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 502 | 42 | 433 | 153 | 32 | 5293 |
| 7 | 502 | 42 | 496 | 122 | 32 | 5711 |
| 101 | 502 | 42 | 467 | 137 | 32 | 5387 |
| 20261102 | 502 | 42 | 564 | 150 | 32 | 5370 |

The independent comparison matched **12,760 ordered events**: 2,008 retirements,
168 fault terminations, 5,208 GPR words and 5,376 terminal RAM sample words across
168 scenarios. Each seed matched3190 events and hit all49 required ISS bins.
All12 actual-trace mutation experiments were rejected, as were the real backend
corrupt-expected/empty simulations. Existing deterministic per-case collision
guards and full-RAM/protocol/drain checks also passed under the shared backend.
No known functional mismatch was observed for these workloads.

Exact compact receipts under `evidence/toolchain_runs/`:

- `lint-20261103T041420582387Z.json`:29 checks/16 commands; positive synthesis
  probes have zero errors/warnings; the injected latch was explicitly rejected.
- `pipeline-iss-20261103T042029369266Z.json`:30 checks/5 commands, four independent
  comparisons; backend `backpressure-20261103T042031646117Z.json`23 checks/12 commands.
- `pipeline-iss-20261103T042343356224Z.json`: full-regression replay, same counts;
  backend `backpressure-20261103T042345559175Z.json`.
- `pipeline-20261103T042011920063Z.json` and `pipeline-20261103T042326041952Z.json`:
  original stage-storage tests retained,79,022 vectors each replay,17 checks/10 commands.
- `retire-20261103T042052921665Z.json` and `retire-20261103T042308057438Z.json`:
  reference-core ISS checks retained,324 retirements/22 scenarios per replay,
  20 checks/5 commands. Reference retirement is a separate workload.
- `backpressure-20261103T042532198543Z.json`: closing stress-target replay.

The finish receipt includes exact argv, timestamps, stdout/stderr, statuses,
exit codes and nested full-regression output. Backend receipts retain pinned
versions, initialization vectors, WDB waveforms, Tcl/argument files and source
hashes. ISS receipts retain exact observed/expected/corrupt trace hashes and
failure diagnostics for all mutations. `evidence/t018-review-audit-2026-11-02.json`
verifies new source/artifact hashes, previous file preservation, report prefixes
and all23 original project files. Git retains the baseline and every task commit.

This package requests acceptance of the directed L2 scope and its explicit
remaining gaps. It does not request an architecture revision or permission to
program hardware, download/install tools, schedule unattended work or push Git.

## Owner acceptance, November 2

The owner explicitly answered "Approve T018 and authorize that command" for
`python -B scripts/harness.py approve T018 --confirm-owner-review`. Before
executing, the reviewed package `de07a80`, this document's submitted SHA256
`7146b4d148d8bc32101fa45a7f68d3ba54ecd005cbdaff690a18e84427285a73`, and every
review-ready/source-audit hash were verified unchanged. The exact command
returned PASS/exit0; T018 is completed and T019 may begin from a clean commit.
Authorization and raw command evidence: `evidence/owner_reviews/T018-2026-11-02.json`
and `T018-2026-11-02-command.json`. Earlier pending-state statements describe
the submitted review; the scope, measurements, exclusions and evidence remain
the accepted package. This acknowledgment grants no additional execution scope.
