# T014 nearest-older forwarding

`forwarding_unit` is a combinational dual-operand selector, not a CPU controller.
Consumer valid and per-source uses flags qualify rs_a/rs_b. Unused, invalid and
x0 sources produce zero value/source/blocked metadata. Nonzero used operands
start from captured/RF values. Two candidate producers must be older than the
consumer; EX/MEM is newer than MEM/WB. Only valid enabled nonzero destinations
match. Caller write qualifiers must exclude faulting/killed instructions.
WB validity/write must describe completed data, including returned loads.

Newest matching EX/MEM non-load result wins; otherwise a matching completed WB
result wins; otherwise use captured data. An EX/MEM load is NEVER forwarded,
even if an address or speculative data is present. Its match returns zero,
source=3 and blocked=1, suppressing an older WB match for the same register.
Using the older value would violate instruction age. The controller must stall
such a consumer; zero is an invalid placeholder, not an executable operand.
Selectors: 0=captured/RF, 1=EX/MEM, 2=MEM/WB, 3=wait. A/B decisions are independent.

No destination-write qualification of the CONSUMER is applied: a load to x0
still needs address forwarding and later access/fault effects. These rules cover
ALU, store payload, branch comparison and JALR base when their source-use flags
are wired correctly. No integration or instruction retirement is implemented
here. Held-source refresh after a transient WB event remains a controller duty:
capture forwarded data while held or reread RF on resume, as the reviewed spec
requires. T015 and later pipeline integration must test this explicitly.

The independent Python oracle builds a set of older producer records, selects
the greatest age, then checks availability. It does not import RTL enums or
parse the DUT. Seeds 1/20261102 sweep all 32^3 source/EX/WB identities with
both EX load states; B uses a complementary source to check independence.
Every 8-bit qualification combination crosses selected identity edges, with
walking/complement data and random inputs. Required bins include both operand
paths, newest-over-older collisions, load shadowing and opposite dual sources.
Four anchored tests plus actual corrupted-expected/empty simulations are gates.
Direct SV checks all 70 result/selector/blocked bits. The bounded-pin synthesis
probe independently captures all four value inputs and observes both decisions.

Replay verify.py lint and verify.py test-forwarding through harness finish T014.
Source/vector/WDB/Tcl/argument hashes and exact pins/seeds/counts are retained.
This is functional selector and structural synthesis evidence. Full pipeline
load-use/stall/redirect/precise fault behavior, formal, timing, physical hardware
and ASIC results remain separate future milestones. No ISA/clock/map revision.

Acceptance passed attempt 1: seeds 1/20261102 each 72,212 vectors, total 144,424;
all 21 declared bins and four oracle tests, wrong-expected/empty rejection pass.
Per seed 65,536 identity/load crosses, 2,048 qualifier crosses, 528 walking-data,
4,096 random and four anchors. Simulations 2.922/3.172 s. Lint 25 checks/14
commands, forwarding probe 19.734 s with zero warnings/errors. Full eleven-target
regression passed, with all scoped source/vector/WDB/Tcl/argv hashes retained.
See evidence/daily/T014.md; these are selector tests, not pipelined retirements.
