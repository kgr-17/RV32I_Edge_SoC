# T016 control and age-directed acceptance

This milestone tests the pipeline_core wiring introduced with dependency
integration; it does not revise the approved ISA, priority or bus contract.
The directed suite reuses all eleven reference-program scenarios, five load-use
scenarios and adds five concrete control/age cases (21 total per seed).

Cases16/17 defer a legal taken BEQ while an older load waits, then kill a younger
store or illegal instruction. Case18 forwards a just-loaded JALR base, clears
bit0, redirects and verifies its link through a dependent readback. Case19 places
a younger store behind an older illegal-instruction WB fault; no request/effect
or retirement may escape. Case20 jumps from ROM word0xfffc to0x20 while the
sequential speculative fetch enters inaccessible0x10000; that fetch error must
drain/discard and cannot replace the target program's ECALL termination.

The actual SV bench requires each designated case to hit its collision, not
merely global nonzero coverage. It counts qualified redirects, redirects deferred
by memory hold, WB-fault-suppressed stores, killed fetch errors and load hazards.
It compares complete ordered retirement metadata, final RAM, sticky faults and
accepted/resolved instruction transaction accounting after drain. Original
request stability, one-outstanding, wrong-answer/empty and progress guards remain.
It permits previously offered fetches to drain after halt and rejects new fetch
creation. This is an actual pipelined DUT, not a token-only controller fixture.

Seeds1/20261102 use IF response1 and data12..15 with data request backpressure.
All forty instruction and nine fault families are included in the hand-assembled
suite; independent arbitrary-binary pipeline ISS comparison remains T018.
Four generator checks cover unique scenario IDs, required categories, ROM-end
case presence and retirement counting. Reused hand-assembly/helper sources are
hash-bound extra inputs. Data/stimulus replay is not a formal or full ISA proof.

Required gates: verify.py lint and test-control through harness finish T016.
Existing production RTL is unchanged at preparation. Save actual per-case
collision counts and source/vector/WDB/Tcl/argv evidence. Random response timing,
long stress/reset, formal, timing, hardware and ASIC remain separate milestones.

Attempt1 passed: 251 retirements/21 scenarios per seed (502/42 total), all70
declared program bins, four generator tests and actual corrupt/empty rejection.
Input rows1,249 per seed are not retirement counts. Simulations2.563/2.500s,
progress-and-drain cycles2,204/2,218. Each seed made14 qualified redirects.
Case16 deferred17/17 cycles, case17 deferred12/15, case18 load-JALR stalled16/13,
case19 suppressed one store, case20 drained one killed fetch error. All per-case
nonvacuity checks pass. Lint29 checks/16 commands and full13-target regression
passed. Production RTL is unchanged from T015; see evidence/daily/T016.md.
