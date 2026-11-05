# T022 selected shared-reset and timing stress

Completed November4 on attempt1; all five gates and full19-target regression PASS.
Prepared from clean T021 completion commit3156aa0. No production RTL, architecture,
old bench, XPR/XDC or kit change.

Four replayable seeds1,314159,20261104,424242. The exact first51 T021 cases are
retained for each seed. Two seed values are new random instruction streams;
the other two replay existing streams. Nine appended directed cases yield60
scenarios/seed: seven selected reset windows share one idempotent program, and
two programs target the five T021 cross gaps. Initial images/expected rows come
from the independent ISS; literal tests anchor key effects and reset replay.

| Case/mode | Required actual reset boundary |
|---|---|
|51/1|I offer sampled stalled at a prior edge, still valid/unaccepted|
|52/2|I request accepted, pending for at least two sampled cycles|
|53/3|D offer sampled stalled, still valid/unaccepted|
|54/4|D request accepted, pending for at least two cycles|
|55/5|D response offered for consumption; shared reset cancels before that edge|
|56/6|Successful store response has committed RAM, but store has not retired|
|57/7|EBREAK sticky fault observed for at least two quiet cycles|

The reset program is LUI(base),ADDI(5),SW(5),LW(same location),ADDI(result+1),
EBREAK. Every actual store must use literal address0x10000/data5/mask1111.
Pre-reset retirements are checked by the SV scoreboard against independent
expected fields. They are not emitted in the post-reset architectural stream;
the exact pre-reset count is logged in STRESS_RESET telemetry and waveforms.
The trace parser compares the complete post-reset R/F/G/M stream with the ISS.
A separate unit test demonstrates identical post-reset expectations whether
the idempotent store had committed before reset or not; the oracle never learns
arbitrary wrong effects from the DUT's actual image.

Reset asserts at a falling edge. Both protocol endpoints cancel pending work,
response signals clear, and the core receives two rising reset edges. On each,
all architectural GPR/core protocol/trace/fault state and handshake gating are
checked. Full64KiB modeled RAM must retain an exact snapshot. Modes1..5 require
the original0xa5a5a5a5 word; modes6/7 require committed5. Mode6 explicitly requires
two preceding retirements and zero memory retirements, proving effect-before-
retirement retention rather than rolling back the committed response effect.
After shared reset, fetch/retire restart at0 and the same program completes;
discarded responses cannot leak effects or retirement into the new epoch.

This is a CPU plus fabric-model integration test. RAM/ROM retention is modeled
by the agent; it is not evidence of synthesized memory RTL or physical BRAM.
Only shared reset is supported. Isolated core reset against a live agent is
outside the reviewed protocol. I-response backpressure/reset phase exhaustiveness,
all asynchronous pin timings, every redirect/reset collision and formal reset
proof remain outside these seven finite windows.

Before reset, I responses wait8..11 cycles and D responses32..47 cycles from a
seeded LFSR. Offered I/D windows deliberately hold ready low. After reset, normal
seeded bus waits resume. Each reset is required once per case, with seed/scenario/
mode, pre-retired count, pending I/D, committed store and fault fields checked.
The first51 cases retain their original timing. A20000-active-iteration case bound
(plus the fixed reset edges),
finite tool budgets and three task attempts remain unchanged.

Case58 uses a priming load to queue an ALU-produced load address, then a loaded
address consumed by another load. It requires new EX-forward/WB-forward/load-
blocked load witnesses. Case59 primes the fetch queue then holds an older SW
while an illegal token occupies EX; four forced store-offer stall edges require
both illegal/MEMhold and illegal/Doffer crosses. Old assertions and every existing
collision/retirement/fullRAM/drain/negative guard remain. The finite49-bin T021
inventory must all be hit across stress seeds, with zero excluded hits; that is
not exhaustive instruction, operand, state-space or whole-core DV closure.

The actual negative RESET_LEAK=1 flips modeled RAM during the first mid-run
reset. The precise reset-retention checker must reject it with a nonempty
waveform; arbitrary timeout/native crash/wrong diagnostic cannot pass. Existing
actual corrupt-expected and empty-file runs remain. Seven policy/generator tests
cover replay/prefix, literal anchors, bounded cases, retained-store idempotence,
reset telemetry, negative diagnostic acceptance and old guard preservation.

Reproduce `python -B scripts/verify.py test-stress`; formal finishT022 uses
evidence/daily/T022.md and runs lint/test-stress/full19-target regression/both
whitespace checks. Shared coverage checker gains only explicit --unit stress;
its default coverage behavior remains. Exact STRESS trace tags and a new backend
are registered. All versions/outputs/hashes remain project-local; no package,
global configuration, scheduling, publication or FPGA programming is involved.

## Direct actual simulation (full regression pending)

Direct stress-report-20261105T004045013330Z.json PASS36 checks/6 commands;
actual stress-20261105T004047217431Z.json PASS23 checks/12 commands.
Four seeds match9,840 main retirements/240 faults/7,440 GPR words/7,680 RAM
words =25,200 main events. SV separately checks52 pre-reset retirements, and
all28 selected reset windows have exact positive boundary witnesses. Each seed
logs pre-reset counts0/0/2/2/2/2/5 for modes1..7; modes6/7 retain committed5,
earlier modes retain0xa5a5a5a5. All four committed-but-unretired boundaries have
exactly two earlier retirements and no retired memory transaction. No RTL change
was needed. RESET_LEAK=1 was rejected by the precise retention diagnostic with
raw XSim exit0 and a nonempty waveform; arbitrary native exit cannot pass.

Finite coverage inventory:49/49 reachable crosses observed across stress seeds,
zero uncovered in that inventory,15 exclusions retained/no excluded hits.
All40 ISA families/nine faults per seed and16 actual report mutations pass.
Original T021 corpus still has its historical five gaps; these additional stress
programs supply the missing evidence. No exhaustive/code/toggle/physical proof.

| Seed | Main retirements | Main events | Reset windows | Pre-reset retirements | Reachable crosses hit |
|---|---:|---:|---:|---:|---:|
| 1 | 2457 | 6297 | 7 | 13 | 46 |
| 314159 | 2463 | 6303 | 7 | 13 | 49 |
| 20261104 | 2483 | 6323 | 7 | 13 | 48 |
| 424242 | 2437 | 6277 | 7 | 13 | 46 |

Direct report: evidence/coverage/2026-11-04_20261105T004045013330Z.json. Full19-target regression pending.

## Final completion evidence

T022 completed November4 on attempt1, all five gates PASS exit0: evidence/runs/T022/attempt-1-20261105T003605460319Z.json; lint/test-stress/full19-target regress/both whitespace. No DUT/architecture/old SV/XPR/XDC/kit changes. Direct stress-report-20261105T004045013330Z.json and replay stress-report-20261105T004829102060Z.json PASS36checks/6commands; actual backend23/12. Four seeds1/314159/20261104/424242,60 cases each. Main9840R+240F+7440G+7680M=25200events; SV separately checks52 pre-reset retirements,28 exact reset windows, modes1..7 per seed preR0/0/2/2/2/2/5. Accepted I/D work canceled; modes6/7 retain committedstore5, other windows retain0xa5a5a5a5; mode6 proves no store retirement before reset, all post-reset order0 starts. Actual RESET_LEAK=1 rejected with exact retention diagnostic/rawexit0/nonempty waveform. Seven Python policies,16 actual report mutations and old corrupt/empty negatives pass. Aggregate finite49/49 reachable crosses hit/no uncovered and15 exclusions unhit; focused load/illegal cases supply five T021 gaps, without changing T021 historical results or claiming exhaustive coverage. Direct/replay reset and assertion witnesses identical, not new coverage. Two new random seeds add16 random programs; original seed streams replayed, original51 cases/seed preserved. Completion audit32receipts/402artifacts/66sources; preservation814 historical files/two same-day prefixes/23 originals. CPU+fabric-model selected-reset simulation only, no memory-RTL/formal/routed timing/physical/ASIC proof. Versions unchanged. State23/41 mandatory complete, active null, actual next expectedT023. Review diff/whitespace and local commit; query actual next before begin. T023 must execute selected formal with real prover/solver, missing tools NOT RUN; no download/install without owner. Next session read latest handoff and required contract files, daily --supervised and recover active task. Unrestricted runtime remains attended only.
