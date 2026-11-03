# T019 replayable random instructions and architectural scoreboard

Prepared November 2; actual RTL results pending formal gates. T041 owner
approval acknowledgment is committed9415b4b; T019 began from that clean baseline
after querying actual first-eligible selection. No ISA/EEI, ports, map, reset,
priority, clock or production RTL change is made.

Six seeds:1,7,101,20261102,314159,271828. Each preserves the exact42-case T018
prefix and its existing deterministic collision and randomized bus checks, then
adds eight constrained random programs, IDs42..49. There are48 random program
runs, in addition to252 retained-prefix scenario replays.

The generator emits initialized ROM and128 bytes of RAM. x1 remains the RAM
base; x30/x31 are reserved for forward JALR and bounded loops. Destinations vary
over x0 and x2..x28. All register/immediate ALU families, load/store widths,
branches and AUIPC are forced on random operands before a shuffled60-template
bag exercises ALU, memory/load-use, branch fallthrough, JAL/JALR wrong paths,
bounded backward loops, ignored FENCE fields, RAW chains and upper immediates.
Data addresses remain within the low128-byte RAM window and naturally aligned.
Branches skip at most one legal instruction; unconditional jumps can skip an
illegal instruction or store. Loop counters are1..4. Programs terminate with
ECALL/EBREAK, alternate by case, within10000 ISS steps and2048 SV expectations.
No random rejection/reseeding or silent skipped program is allowed.

The ISS, independent of RTL, executes initialized bytes to supply SV expected
rows. It is the same ISA oracle used by the retirement comparator and streaming
scoreboard, not two separately implemented ISA oracles. The earlier hand-derived
prefix remains a complementary anchor. Expectations are never imported from
RTL enums or decoder output. Seeds, exact input bytes, source hashes and actual
observed traces are retained for replay. The generator has five tests for replay,
variation, prefix preservation, random-only family/template coverage, unique
cases, bounded termination and unmodified initialization.

`dv/reference/scoreboard.py` consumes actual R/F/G/M events in order. Each R/F
advances the ISS once and compares complete architectural metadata. A separate
observed-effect ledger applies GPR writes and lane-qualified stores, requiring
its complete sparse ROM/RAM image and32 GPR values to equal the oracle after
every retirement. Terminal x1..x31 and32 RAM words must match both views, with
exact dump order and one sticky-fault event. Empty/incomplete/extra events fail;
once failed, a scoreboard cannot resume as a pass. This effect ledger is not an
independent full-RAM dump from the DUT: SV separately checks all64KiB RAM and
response/effect/retire accounting. Random accesses fit the sampled window.

Six anchored scoreboard tests cover literal committed register/memory state,
fault/GPR/RAM corruption, ordering, missing/duplicate words, sticky rejection,
empty/scenario/extra-event errors. On every actual seed, six injected errors
must be rejected by the streaming scoreboard: retirement data bit, terminal
GPR bit, RAM bit, empty trace, dropped retirement and extra event. Deterministic
mutation descriptors and exact diagnostics are saved with each scoreboard
artifact, allowing replay from the original observed trace. The existing three
actual-trace comparator mutations and real corrupt-expected/empty XSim runs
remain required; a raw XSim exit0 cannot override a fatal diagnostic.

The actual random-only eight cases must hit all40 instruction families in each
seed, independently of prefix coverage. The scoreboard records their actual
matched operations, retirements, loads/stores and terminal-state counts. This
is finite family coverage, not exhaustive operand/cross/state-space closure;
T021 must define and audit broader reachable coverage explicitly.

Pre-simulation expected counts (input rows include initialization/boundaries):

| Seed | Total retirements | Random-only retirements | Cases | Input rows |
|---|---:|---:|---:|---:|
| 1 | 2408 | 1906 | 50 | 6596 |
| 7 | 2402 | 1900 | 50 | 6590 |
| 101 | 2428 | 1926 | 50 | 6616 |
| 20261102 | 2390 | 1888 | 50 | 6578 |
| 314159 | 2414 | 1912 | 50 | 6602 |
| 271828 | 2416 | 1914 | 50 | 6604 |

`scripts/retire_checks.py --unit random` binds the actual random pipeline backend,
RANDOM trace tags, independent comparator, streaming ledger and error injections.
The aggregate child budget is120s within the existing runner cap; individual
XSim30s and old backend60s budgets/three task attempts remain unchanged. All
outputs stay project-local; no tools or packages are installed/downloaded.

Formal finish runs lint, test-random, full16-target regress and both whitespace
checks. Full regression was added to T019's original lint/test-random commands
because shared parsing/checker/manifest changes require old-route validation.
No original acceptance check is removed. Test-pipeline/retire/ISA suites retain
their defaults and negatives. Versions remain Python3.9.13/Git2.48.1.windows.1/
tzdata2026.2/Vivado-XSim2025.2 SW6299465.

Preparation evidence/prepare/T019-20261103T055031Z.json records6 scoreboard and
5 generator tests PASS. Those Python results cannot substitute for actual RTL
gates. Formal results, source/artifact evidence and local commit will be appended
after execution. In-flight reset, assertion/coverage/formal closure, SoC/MMIO,
interrupts, certification, timing, physical FPGA and ASIC remain separate work.

First formal attempt retained: functional random suite and full16-target
regression PASS; lint FAIL because Vivado crashed on exit after successful
register-file synthesis/DRC. The raw nonzero exit is not waived. Six actual
seeds matched14458 retirements (11446 random-only) and all36 streaming defects
were rejected. No RTL/source/check/tool/timeout change for identical attempt2.
See evidence/daily/T019.md and t019-native-crash-2026-11-02.json for exact receipts.

Owner requested shutdown during attempt2. Verification was cancelled and no
project verification processes remain. T019 is saved as an unfinished active
task: two attempts reserved, one finish attempt remaining. The second running
journal/partial lint are retained with an explicit interruption companion in
evidence/t019-shutdown-checkpoint-2026-11-02.json. No pass/completion inferred.
Resume T019 from the dated technical handoff before selecting any other task.
