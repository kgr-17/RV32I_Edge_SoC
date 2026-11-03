# T013 stage storage contract

`rtl/core/pipeline_core.sv` currently contains `rv32_pipeline_stage` and
`pipeline_registers`: storage building blocks, not an executable ISA core.
The final pipeline top and reviewed CPU bus/retirement interface are integrated
in following milestones. T013 does not replace or modify reference_core.

Five independent indices IF=0, ID=1, EX=2, MEM=3, WB=4 each store one valid bit
and an opaque WIDTH-bit payload. WIDTH must be positive; default is 32.
The same clock drives every stage. Data/control are synchronous core-domain
signals. Upstream data selection/transform and transfer bookkeeping belong to
the later controller; this bank does not autonomously move one stage to another.

At the rising edge: reset or selected clear inserts a bubble and zero metadata;
otherwise hold retains state; otherwise capture valid_i/payload_i, with invalid
input storing zero metadata. clear wins over local hold. clear_i means an
ALREADY ARBITRATED kill/bubble, not a raw redirect. Later control must first
enforce reviewed reset > oldest_fault > memory_hold > redirect > load_use >
advance. In particular it must defer redirect clear under older memory hold;
this local register priority does not revise global architectural policy.

Outputs mask valid and payload to zero while reset is high; actual state reset
is synchronous. A pulse entirely between edges masks observations but does not
erase stored tokens. Payload is always zero for a bubble. Independent controls
allow WB to clear after its one consume while younger stages remain held; the
later controller must generate that event and prevent repeated retirement.

The independent Python ledger records capture tokens and clear/reset/bubble
tombstones; holds add no event. It derives pre/post expected state from the last
event per stage. Seeds 1/20261102 test all 32^3 clear/hold/valid mask combinations,
full 129-bit walking/complement payloads and holds, reset collisions, 32
between-edge pulses, WB drain with front held, and 4,096 random transitions.
SV compares before and after every edge across five stages at WIDTH 1,32,129,
including invalid metadata zeroing and immediate reset masking/retention.
Four anchored oracle tests and actual wrong-expected/empty-vector simulations
are required. Every declared functional bin must be hit; no percentage inferred.

The bounded-pin synthesis probe independently captures all five 32-bit input
words and exposes every stored bit plus validity through a mux. Required gates
are verify.py lint and test-pipeline via harness finish, with source/seed/vector/
WDB/Tcl/argv hashes. Generated outputs stay under build. This proves scoped
stage storage behavior in simulation and structural synthesis; not forwarding,
load-use, redirect age handling, memory protocol or full pipeline ISA execution.
Formal, routed timing, physical FPGA and ASIC results remain separate future work.

Acceptance passed on attempt 1. Each seed checked 39,511 rows: 32,768 control
crosses, 1,290 walking payloads, 1,290 held payloads, 32 reset crosses, 32 short
reset pulses, 4,096 random transitions and three startup/drain rows. Total
79,022 clocked vectors, with before/after comparison at all three widths.
All 39 declared bins, four oracle tests and actual corrupt/empty simulations pass.
Synthesis probe command 19.078 s, zero warnings/errors; lint 23 checks/13 commands.
Full ten-target regression also passed. See evidence/daily/T013.md for exact
source/vector/WDB/argv receipts. These are register-bank tests, not ISA retirements.
