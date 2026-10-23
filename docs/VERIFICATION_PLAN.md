# Active verification acceptance additions (2026-10-14)

Original hierarchy is retained below. Selected formal verification (T023), full
RV32I/EEI behavior (T041), UART RX (T042), routed FPGA timing/power (T043),
physical authorized hardware validation and ASIC block evidence are mandatory.
An MVP subset is an intermediate milestone only. No final compliance, timing,
hardware or ASIC claim follows from a harness test. Architecture remains draft.

Traceability: each BACKLOG task names its acceptance criteria, required files
and executable commands. Evidence/daily/ID.md maps each criterion to actual logs.
Missing registry targets or inputs return NOT RUN, not a zero-test PASS.

# DV and validation plan

## Verification hierarchy (do not collapse these)

1. Unit directed tests: ALU, decoder, regfile, branch unit, memory align/sign extension, UART, timer.
2. Integration directed: simple instruction programs; pipeline hazards; handshake backpressure; wrong-path flush; x0 stability.
3. Independent architectural reference: Python ISA interpreter or Spike for an explicitly matching subset; compare **retired instruction events/state**, not just final program printout. A model copied verbatim from RTL is insufficient.
4. Random constrained: valid instruction sequences; deterministic seeds, reproduce failures; memory wait-state randomization, flush/stall interactions.
5. Assertions: no unexpected commit, stable request under `valid&&!ready`, x0 invariant, flush kills younger, no duplicate request, bounded eventual progress with stated assumptions.
6. Coverage: functional op groups, branch taken/not, forward source, load-use, memory wait cycles, lane/size, backpressure × redirect; list unhit bins and exclusions.
7. Optional bounded formal: properties on ALU, handshake adapter, small FIFO, x0; proofs are scope/bound dependent, no whole-core signoff claims.
8. Official architectural tests: ACT4 requires matching machine model, linker script, macros, toolchain and enough architectural behavior. Architectural tests do **not** replace microarchitectural DV.
9. FPGA validation: physical board image, firmware hash, UART transcript, actual Vivado implementation/clock/constraints/critical path, reproduce steps. Simulator pass is not physical validation.
10. ASIC flow: synthesis/STA/DRC/LVS reports as applicable; results contingent on library/PDK/corners/constraints. GDS generation ≠ silicon tapeout.

## Minimum stage pass policy

| Stage | Must demonstrate |
|---|---|
| ALU | corner values signed/unsigned, arithmetic shift, zero/overflow behavior as RV32I defines |
| Core functional | self-checking compiled test for every supported instruction group |
| Pipeline | RAW EX/MEM, load-use, store data hazard, JALR, taken/not taken branches, consecutive stalls, reset after stall |
| DV closure | randomized seed list + fault-reproduction command + coverage report; zero known failures for scoped tests |
| FPGA | binary hash, console result, board pin constraints, resources/timing summary |
| ASIC | one module first; distinguish unit-module results from complete CPU data |

## Test report schema

- commit SHA, tool versions, command, target, time, seed, exit status, pass count, fail count, skipped, waveform location, interpretation.
- Explicit label `NOT RUN` if missing tools/licenses/hardware; never transform skipped into pass.
- CI smoke test for every commit; nightly regressions only after tests exist and have known runtime. External free CI limits respected.

## Coverage caution

Do not set an arbitrary 100% target without defining measurable coverpoints. Track reachable vs unreachable bins, requirements traceability, and defect injection/mutation experiments where feasible.


## T002 architecture v0.2 requirement traceability (2026-10-16)

The submission is proposed, not owner-approved. These are required future tests;
every RTL/FPGA/ASIC row below is NOT RUN. Documentation consistency checks are a
separate gate and cannot satisfy these implementation criteria.

| Requirement | Backlog tasks | Required independent evidence |
|---|---|---|
| R-RESET | T006, T022, T029 | Synchronous reset clears architectural/core protocol state; shared reset cancels outstanding local transactions. |
| R-ISA | T004, T005, T007, T008, T012, T041 | All 40 base instructions, legal HINTs and chosen EEI behavior are traced to independent tests. |
| R-X0 | T006, T020, T023 | x0 stays zero; loads targeting x0 still perform access and fault/side effects. |
| R-RF | T006 | Two combinational reads, one retirement-edge write, same-cycle WB-to-ID bypass. |
| R-MEM | T009, T017, T026 | One outstanding request per bus, stable stalled payload, no duplicate acceptance, synchronous responses. |
| R-LANES | T008, T028 | Byte enables and lane shifts match original byte effective address; misalignment faults before request. |
| R-FETCH-KILL | T016, T017 | Redirect/fault kills stale fetch results while preserving already-offered request stability. |
| R-FWD | T014 | Nearest valid older result wins; no x0/invalid/load-not-ready forwarding. |
| R-LOAD-USE | T015, T017 | Dependent consumer waits until a legal WB bypass exists; store data and branch/JALR operands included. |
| R-HOLD | T017, T022 | MEM wait holds younger stages but WB retires at most once; no stale operand after extended stall. |
| R-REDIRECT | T007, T016 | EX resolves branches and jumps; taken misaligned target faults; wrong-path effects never commit. |
| R-FAULT | T011, T020, T041 | Oldest precise fault wins; faulting/younger instructions do not retire or issue memory effects. |
| R-STORE-ORDER | T017, T020, T041 | Store/read-side effects occur once at successful response acceptance, only after older faults are excluded. |
| R-RETIRE | T011, T018, T019 | One ordered successful retirement event, stable metadata, separate sticky fault observation. |
| R-FENCE | T041 | Conservative full I/O/read/write drain, including ignored future FENCE fields; no younger effect before completion. |
| R-MAP | T025, T026, T028 | ROM/RAM/MMIO regions and access permissions agree with linker and fabric; unmapped access errors. |
| R-UART | T027, T042 | TX/RX 8N1, clock-enable timing, synchronization, backpressure, framing/overrun and partial access semantics. |
| R-CDC | T029 | One core/SoC clock; synchronized reset release and external inputs, documented CDC reports. |
| R-CLOCK | T025, T030, T043 | 100 MHz board source and 10 ns constraint, with routed setup/hold evidence required separately. |
| R-TOOLCHAIN | T003 | Real executable lint and simulation gates and pinned versions; missing checks cannot pass. |
| R-CLOSURE | T024, T032, T039, T040 | DV, physical FPGA and ASIC evidence remain distinct and final owner review remains mandatory. |
| R-IRQ | T044, T045, T032 | Later interrupt support requires a separately approved trap/CSR revision, precise timer interrupt verification and authorized hardware evidence. |

T002 only: python -B scripts/check_arch_spec.py and
python -B scripts/test_arch_spec.py validate the proposed artifact's structure and
negative mutations (including overlap, invalid boot region, port drift, missing
instruction, wrong target, self-approval, bad response latency and fault collision).
They do not execute a DUT, reference ISA model, formal engine or EDA implementation.
Owner review remains mandatory after those checks. No arbitrary coverage percentage
is inferred from these Python checks.

For future instruction/EEI tests compare successful retire events and separate
fault termination events. Correlate each successful memory response with exactly
one later memory retire entry; detect early store effects before older faults,
wrong-path MMIO consumption, stale fetch error propagation, and repeated WB
retirement during MEM wait. A model copied from DUT expressions is not an oracle.

Future negative tests must include:
- false branch with a misaligned hypothetical target; JALR bit-zero clearing;
- load to x0 with memory error and side effect; illegal vs legal HINT/FENCE fields;
- reset while request is offered, accepted and response-stalled;
- older fault vs younger store, and older redirect vs younger fetch/decode fault;
- back-to-back ready changes, lane masks, each UART error/consume collision;
- stale operands after a long memory hold and a completed producer's WB event.

Toolchain compatibility and simulator execution are T003 and later work. Do not
substitute the current contract tests for a missing lint/simulation gate.

## T004 decoder unit evidence (2026-10-23)

T002 was approved in the recorded owner review; its historical proposal fields
remain intact. T003 passed earlier today. Under an explicit T004-only same-day
exception, T004 passed required lint and test-decode on attempt 1. Decoder
synthesis had zero errors/warnings and passed latch/black-box/structural checks.
The independent mask-table oracle and encoder drove 143,809 vectors per seed
(1 and 20261023), 287,618 total; all 57 metadata bits were compared. Fifteen
acceptance-policy tests and six oracle tests passed, in addition to thirty
controller tests at the exception checkpoint. Wrong-expected-bit and empty-file
negative simulations were rejected. No scoped functional defect was found.

See DECODER.md and evidence/daily/T004.md for the unit interface, exact receipts,
coverage group definitions and replay commands. R-ISA decode classification is
tested; R-X0/R-FENCE execution, retirement, precise faults, full ISA compliance,
formal, timing, physical hardware and ASIC results remain future evidence.
The composite regress command now routes to both fixture and decoder checks;
this combined entrypoint has not been rerun solely for its routing addition.
