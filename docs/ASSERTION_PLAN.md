# T020 executable pipeline assertion plan

Completed November 4 on attempt2; all five gates PASS, including full17-target
regression. Prepared from clean T019 commit af52c5f. No production RTL, architecture, reset
priority, bus behavior, target, XPR or XDC change is made.

`dv/assertions/core_properties.sv` is a simulation monitor using immediate
SystemVerilog assertions in a rising-edge `always_ff`, with explicit prior-edge
history for temporal rules. This is executable assertion simulation, not a
concurrent-SVA engine test or formal proof. No `bind` or untested SVA feature
support is assumed. It is instantiated explicitly in `tb_assertions.sv`.

| IDs | Observations and rule | Isolated violation IDs |
|---|---|---|
| P_X0_A/B | Actual DUT RF address/data on each read port: address0 implies data0, including WB bypass. No constant x0 probe is used. | 1,2 |
| P_RETIRE_ORDER | Successful retirement has no simultaneous fault and order equals the next counter, starting0 after reset. | 3 |
| P_RETIRE_DEST | Enabled GPR destination is nonzero; disabled write has canonical zero index/data. | 12 |
| P_RESET_QUIET | During reset, I/D request-valid and response-ready are zero. | 4 |
| P_RESET_STATE | At the edge following a reset edge, all architectural GPR storage, stage-valid, protocol/queue/PC/order and trace/fault state are zero. | 5 |
| P_I_STABLE | A prior stalled I request remains valid with identical address through acceptance. | 6,8 |
| P_D_STABLE | A prior stalled D request remains valid with identical original address, data, byte mask and write bit. | 7,9 |
| P_I/D_SINGLE | An accepted request cannot replace an outstanding request, including the response consume edge. | 15,16 |
| P_I/D_RESPONSE | A response handshake requires a previously accepted outstanding request, with no same-edge new request. | 13,14 |
| P_FAULT_STICKY | A prior fault remains asserted with identical PC/instruction/code/tval; no retirement, data request or data response acceptance follows. | 10,11 |

At clock edge n the monitor samples pre-NBA DUT outputs. Reset history checks
the state produced by edge n-1, including the first released edge. This avoids
incorrectly demanding that registered outputs clear before the reset edge's NBA
updates. Request gating is combinational and checked during reset immediately.
Reset cancels monitor pending/stall/fault/order history, matching the reviewed
shared-reset local protocol. Counters accumulate across scenarios to demonstrate
nonvacuity; they are initialized simulation state, not synthesis hardware.
The first rising edge establishes history by asserted reset. The test runner
requires positive reset/read/retire/stall/fault/request witnesses on every seed.

The positive bench is an inspected copy of the T019 actual pipeline bench with
only monitor wiring, property witnesses, top name and trace tags added. All old
collision/progress/full64KiB-RAM/effect/retirement/drain/error checks remain.
It reuses the exact same independently ISS-generated programs and six seeds:
1,7,101,20261102,314159,271828;50 cases/seed,14,458 total expected retirements.
These are replays of T019 programs, not new unique random coverage. The module
observes actual DUT ports and internal RF/reset state without changing the DUT.

`tb_property_negative.sv` drives the same compiled monitor in isolation. A legal
control must pass;16 separate runs deliberately violate one named property.
Each must emit exactly its intended assertion ID, never the control marker or
an undetected-injection marker. A raw simulator exit0 alone cannot pass a negative
or positive run; timeout/crash/missing/wrong/duplicate diagnostics fail. Raw
exit0 or1 is acceptable only for the exact intended assertion violation. The
negative scope proves monitor sensitivity, not an injected RTL defect.

Six independent acceptance-policy tests exercise misleading diagnostics,
timeouts/native crashes, seed/count binding, zero/duplicate witnesses, required
property families and preservation of original bench guards. The actual runs,
not text-policy tests, establish that the simulator executes the assertions.

Reproduce from the project root:

```powershell
python -B scripts/verify.py test-sva
python -B scripts/harness.py finish T020 --evidence evidence/daily/T020.md
```

Formal task gates retain lint and test-sva and add full17-target regression for
the shared manifest/registry addition. Three attempts, synthesis budgets,
120-second unit-backend maximum,30-second positive XSim limit and10-second
isolated-run limits remain finite. All artifacts and waveforms stay in build/;
compact hashed receipts remain in evidence/toolchain_runs/.

Scope limits: no claim of all internal flush/progress assertions, comprehensive
unknown-bit checking, concurrent SVA, full protocol liveness, in-flight-reset
closure, exhaustive crosses, formal proof, FPGA timing, physical hardware or
ASIC evidence. Existing directed collision guards/ISS/fullRAM checks complement
these assertions. T021 defines coverage, T022 stresses reset during transactions,
and T023 must execute selected formal properties separately.

## Actual direct simulation (full regression pending)

Parent receipt `assertions-20261104T233152349767Z.json`: PASS, 57 checks/24 commands.
Actual backend `assertions-20261104T233154686994Z.json`: PASS29 checks/14 commands.
One legal isolated control and all16 intended assertion violations passed their acceptance checks;
all injected `$fatal` runs returned raw exit0, demonstrating why exact diagnostic checks matter.

| Seed | Reset edges | x0 A | x0 B | Retirements | I hold edges | D hold edges | Sticky-fault edges | I requests | D requests |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 150 | 12888 | 17166 | 2408 | 3459 | 593 | 357 | 2841 | 411 |
| 7 | 150 | 12969 | 17266 | 2402 | 3578 | 549 | 353 | 2839 | 410 |
| 101 | 150 | 13400 | 17662 | 2428 | 3600 | 545 | 362 | 2884 | 414 |
| 20261102 | 150 | 13311 | 17415 | 2390 | 3784 | 628 | 382 | 2839 | 410 |
| 314159 | 150 | 13152 | 17262 | 2414 | 3646 | 643 | 355 | 2863 | 413 |
| 271828 | 150 | 13162 | 17533 | 2416 | 3739 | 592 | 356 | 2870 | 408 |

Counts are sampled edges/events, not independent property proofs. Reset count includes repeated
between-case reset edges; fault counts are sticky-fault sampled edges, not unique faults.
All T019 program, fullRAM, protocol, collision and injected corrupt/empty checks remain.
Lint passed29checks/16commands; full17-target regression is still running.

## Final completion evidence

T020 completed November4 on attempt2/3, all five gates PASS exit0: lint/test-sva/full17-target regress/both whitespace. Receipt evidence/runs/T020/attempt-2-20261104T234039076194Z.json. No source/seed/check/timeout changes for retry; prior storage corrupt-input XSim nativeexit4294967295 retained in attempt1/failed_sources archive. Same failed negative passed unchanged on replay pipeline-20261104T234949813411Z.json. Direct assertion parent assertions-20261104T234621440634Z.json and final replay assertions-20261104T235312687397Z.json each PASS57checks/24commands; backend29/14. All four direct/replay assertion executions identical: six seeds,900 reset samples,78882/104304 actual x0 A/B samples,14458 retirements,21806/3550 I/D stall checks,2165 sticky-fault samples,17136/2466 request acceptances;16 isolated intended violations each rejected plus legal control. These are repeated programs and sampled edges, not new coverage/formal proofs. Full regression retains old independent ISS/fullRAM/collision/negative gates. Completion audit56receipts/711artifacts/61sources binds exact current/index candidates and first31-input archive; preservation661 historical files/two report prefixes/23 originals. Production RTL/architecture/old benches/XPR/XDC/kit unchanged. Six acceptance-policy tests PASS; earlier report append lock refusal exit1 retained in narrative, deferred until finish without bypass. Versions unchanged Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. State21/41 mandatory completed, active null; query actual next T021. Review diff/whitespace, commit inspected files locally, record commit and require clean baseline before begin T021. Runtime unrestricted attended only; no downloads/install/push/scheduling/programming or timing/hardware/ASIC claims.
