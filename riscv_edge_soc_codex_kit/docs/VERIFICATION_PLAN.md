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
