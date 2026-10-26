# T011 independent retirement comparison

`dv/reference/rv32_iss.py` is a standalone RV32I 2.1 interpreter of program
bytes under the reviewed v0.2 fatal-halt EEI. It imports no RTL metadata, decode
tables, operation enums, T010 expected records, ALU/LSU or bus-model helpers.
Instruction fields are extracted arithmetically. Signed integers, arithmetic
multiply/divide shifts and byte conversion implement independent semantics.
All forty mnemonics, exact reserved-field rejection, ignored FENCE fields,
JALR bit-zero clearing, alignment before mapping, x0 access effects and nine
fault codes follow the previously reviewed contract. No privileged extension.

The sparse byte image covers ROM/RAM; fetch only ROM, loads ROM/RAM, stores RAM.
Unmapped/MMIO accesses error in this bounded environment; peripherals remain
later milestones. Optional word error injection tests access-fault behavior.
`step()` returns Retirement or a sticky Fault. Faulting instructions have no
retirement/GPR/memory effects; reset preserves committed memory. `run(limit)`
requires a real termination and rejects a progress timeout. Architectural stores
are atomic with the ISS event; the real fabric's response-handshake effect point
is separately monitored in the SV bench, not falsely equated with the trace.

`dv/reference/retire.py` loads only instruction/data initialization from replay
inputs. It explicitly discards T010's hand-authored expected retirement rows
and expected fault fields. The ISS executes bytes to derive every ordered
retirement field, fault and final state. The SV bench now exports actual sampled
CORE_RETIRE/FAULT records, x1..x31 storage values and 32 final RAM words in
0x10000..0x1007f. x0 has no stored word; its behavior is checked through existing
unit/program tests and disabled write metadata. The SV scoreboard independently
checks all 64 KiB RAM against its original directed expectations. No trace state
is read from the DUT to generate ISS expectations.

`scripts/retire_checks.py` pins versions, launches actual XSim through the core
backend and reads its hash-bound command outputs. For each seed (1/20261026)
it compares a nonempty complete ordered event stream, including terminal GPR/RAM
samples, against independently executed ISS results. Wrong order, extra/missing
events or any field mismatch fail. It saves actual/expected/corrupted traces,
hashes, versions, sources, coverage and per-scenario counts under build/T011 and
compact evidence/toolchain_runs/retire-*.json. Bit-flipped actual trace, empty
trace and extra event must all be rejected for every actual simulation seed.

Ten anchored Python tests exercise literal machine words, signed shift/load,
lanes, x0 fault effects, alignment priority, JALR clearing, forbidden extensions,
FENCE fields, sticky/reset behavior, bounded progress, discarded hand expectations
and comparator mutations/order/state checks. These tests are distinct from real
RTL execution. No zero-test or missing-tool pass is permitted.

Required replay: harness finish T011 --evidence evidence/daily/T011.md runs
verify.py lint, verify.py test-retire and both whitespace checks. The regression
entrypoint includes test-retire as a real target. Existing production RTL and
architecture remain unchanged. This is independent directed reference-core
comparison, not randomized program closure, formal proof, pipeline correctness,
full ISA certification, routed timing, physical hardware or ASIC evidence.

Acceptance passed on attempt 2 with unchanged sources: ten Python tests and
17 comparison checks/5 commands, real backend 17 checks/10 commands. Two seeds
each compare 866 ordered events: 162 retirements, 11 faults, 341 GPR and 352 RAM
words. Totals 324/22/682/704, all 49 declared ISS operation/fault bins. Three
trace mutations per seed were rejected. Lint passed 21 checks/12 commands.
Attempt 1's native Vivado exit crash on the unchanged branch probe was correctly
rejected despite a success marker; full failed receipt/log text and identical
source hashes remain retained. No test/filter/tool-setting change for retry.
