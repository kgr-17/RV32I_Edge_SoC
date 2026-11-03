# T017 replayable bus-wait stress

No production RTL or prior tests change at preparation. The new test retains
T016's original 21 deterministic cases as an exact stimulus prefix (including
per-case collision requirements), then repeats them with IDs21..41 under seeded
timing. Four seeds1/7/101/20261102 exercise the actual pipeline DUT.

The second pass varies IF request readiness with forced short low windows and
response latency1..4. Data requests see random/forced low-ready windows; each
scenario's first accepted data transaction waits32 edges and subsequent responses
vary1..32. Producers hold snapshot valid/data/error until handshake. Runtime
requirements include nonzero IF/D request stalls and observed32-edge data wait.
Only answered fetch buffering is permitted; at most one unanswered bus request.

Complete retirement/order, full RAM, sticky faults, existing offered-request
stability/duplicate/progress checks and halt/redirect fetch drain stay enabled.
The first21 deterministic cases keep all original nonvacuity checks. Random
timing replay need not reproduce every same-cycle collision, but must produce
the exact same architectural event sequence and memory effects. No deterministic
check was removed to make randomized timings pass. Shared reset-in-flight and
long randomized instruction generation remain later T019/T022 scope.

Four program checks validate prefix preservation, unique IDs, seed replay/data
variation, expected counts and retained bins. Actual corrupt-expected/empty
simulations and source drift/hash guards remain. Helpers are explicit hashed
inputs. Replay verify.py lint/test-backpressure through harness finish T017;
then inspect real per-seed timing/collision counts and preserve all artifacts.
Independent pipeline ISA closure is T018; formal/timing/hardware/ASIC are distinct.

## November 2 verification result

Formal attempt 1 retained a native Vivado ALU-process exit crash after completed
synthesis/DRC and the pass marker. The nonzero process exit correctly failed
lint; all four functional seeds passed. No checks, sources, timeouts or vendor
configuration changed for attempt 2, which passed all required commands.

Each seed completed 42 scenarios and 502 successful retirements: 168 scenarios,
2,008 retirements total. Seeds 1/7/101/20261102 observed IF request stalls
433/496/467/564 and data request stalls 153/122/137/150 respectively. Each
observed a maximum accepted-data response age of 32 edges. Complete artifacts,
negative runs and retry provenance are in evidence/daily/T017.md. Input rows
also include initialization and case boundaries; they are not retirements.
