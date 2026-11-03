# T015 load-use integration

`hazard_unit` intersects actually used consumer source IDs with a valid enabled
nonzero pending load destination. Either source can hold the consumer until
the load leaves MEM and completed WB data can forward. Unused operands, x0,
invalid instructions and disabled/non-load producers do not interlock.

`pipeline_cpu.sv` adds an executable `pipeline_core` under the already reviewed
external ports, retaining the separate reference DUT. It reuses decoder, ALU,
RF, branch, LSU, stage storage and forwarding components. IF tracks one offered/
accepted request. Up to three already-responded words buffer in order before
decode; this is an internal fetch-response FIFO, not a cache or extra outstanding
bus transaction. Its burst after a long hold exposes real adjacent dependencies.
ID reads current RF (including retiring WB bypass), EX resolves operands and
computes results/fault tokens, MEM performs one original-address transaction,
WB emits one ordered retirement or precise sticky fault. No architecture revision.

While MEM waits, younger work holds and older WB drains once. A matching load
holds EX through its response edge, inserts no younger MEM work, then releases
when WB data is available. EX refreshes held captured operands on qualified
transient EX/WB bypass, preventing stale operands after the source disappears.
Stores take effects in the fabric only at successful response acceptance.
The request-sent flag prevents reissue; a WB fault gates younger data requests.

Reset clears pipeline/fetch/protocol/trace/fault/GPR state. Redirect arbitration
defers to older memory hold/fault. Queued younger work is killed; an offered or
accepted stale fetch keeps stable payload and drains/discards before target
fetch. Halt similarly drains prior offered fetches and initiates no new ones.
These control/bus paths are necessary wiring here; dedicated collision/stress
acceptance remains T016/T017, with full independent pipeline closure at T018.

The pure detector has independent set-intersection vectors and four anchors.
Actual pipeline tests hand-assemble five scenarios with explicit full retirement
expectations and final-state checks: both operands dependent, held WB refresh,
load-to-store payload, x0 destination and replayable random data chains.
Instruction request ready and response latency=1 make FIFO bursts deterministic;
data ready varies and responses wait 12..15 edges. The bench requires nonzero
actual hazard and held-WB-refresh cycles, compares every retirement field/order,
checks complete RAM, stable requests, no duplicate acceptance/commit and fault/
stale-fetch drain. Corrupt-expected and empty-file simulations must fail.
Four program tests and shared driver policy tests supplement actual execution.

The program generator reuses only hand-assembly helpers, not DUT semantics.
Their bytes are explicit extra hashed driver inputs; missing helpers are NOT RUN.
The pipeline bench was derived from the inspected reference fabric and extended
for speculative fetch drain; the reference bench/CPU remain unchanged. The new
probe captures independent bus inputs and observes every approved core output.

Required gates: verify.py lint and test-hazards via harness finish T015. Generated
source/vector/WDB/Tcl/argv hashes and exact versions/counts are retained locally.
This milestone does not sign off all pipeline instructions, control collisions,
random timing/reset, formal, timing, hardware or ASIC. Full later gates remain.

First attempt functional checks passed: each seed 64 pipeline retirements across
five cases, actual hazard cycles 177/161 and held-WB refresh twice per seed.
The detector checked 37,312 rows per seed. Lint correctly failed at the former
45-second full-pipeline synthesis timeout before mapping completed. Exact first
inputs/logs are retained. RTL/expectations remain unchanged for retry; bounded
per-design CPU synthesis allowance is now 120 and aggregate lint 600, with all
warnings/structural/timeout-failure and process-tree cleanup checks retained.
Other synthesis defaults remain 45. See CODEX_LOOP.md and T015 evidence.

Acceptance passed attempt 2 with unchanged RTL/expectations. Full pipeline probe
completed in 37.969 s under the explicit budget with zero diagnostics; lint29
checks/16 commands passed. Pure detector 74,624 total comparisons, pipeline128
retirements/ten scenarios, hazards177/161 and held-refresh2/2, all required
negative runs pass. The retry ran79 Python tests including runtime bounds,
real descendant kill and existing harness/acceptance tests. Full twelve-target
regression passed; exact counts, source hashes and artifacts are in T015 evidence.
