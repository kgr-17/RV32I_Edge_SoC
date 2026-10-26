# T010 nonpipelined reference CPU

`reference_core` implements the previously reviewed v0.2 core port contract
without a pipeline or prefetch. All forty RV32I mnemonics decode through the
retained decoder; the tested RF/ALU/branch/LSU units are instantiated unchanged.
One clock, active-high synchronous reset, PC=0, zeroed GPRs and initial fatal
fault-halt EEI follow the approved contract. No new CSR/interrupt/ISA extension.
This reference DUT is separate from T011's independent Python ISA interpreter.

Seven controller states: FETCH_REQ, FETCH_RSP, EXECUTE, DATA_REQ, DATA_RSP,
COMMIT and HALTED. Each bus allows one accepted outstanding transaction.
An offered request stays valid/stable until accepted, except shared reset.
Responses are consumed only in their wait state. There is no same-edge request
replacement, no speculative effect and no younger instruction behind a fault.
Core/memory shared reset cancellation is required; a non-reset live fabric is
outside v0.2. Protocol waiting and reset races receive further T022 coverage.

Execution latches next PC, destination value and memory metadata. Misaligned
control/data accesses fault before an inappropriate request. JALR clears bit 0;
false branches ignore hypothetical misalignment. Data bus uses original byte
address, lane strobes and shifted store payload; reads return aligned raw words.
Loads to x0 still perform access/error handling. Successful data responses
precede the one COMMIT event; actual memory effects belong to the fabric at that
response handshake. Stores never write GPRs. FENCE full-drains naturally because
this sequential machine has no concurrent older/younger memory operations.

COMMIT writes a nonzero destination and emits one retirement event with the
reviewed 64-bit order and complete PC/insn/GPR/memory metadata. Inactive trace
metadata is zero. Faults emit no retirement, set sticky code/PC/insn/tval and
halt until reset. Instruction-access faults carry insn=0. No outstanding fetch
exists to kill on redirect in this no-prefetch microarchitecture. Later pipeline
logic must implement the reviewed age/flush/drain semantics explicitly.

`dv/integration/test_core_smoke.py` hand-assembles directed programs and explicit
expected retirement/fault records, using independent encoders and arithmetic.
It does not decode/execute an arbitrary program as an ISA oracle. Three anchored
Python tests validate encodings, replay/coverage and the checked negative field.
Seeds 1/20261026 vary data and reproducible bus delays. Eleven scenarios cover
all forty families, both outcomes of all branches, bad hypothetical targets,
JAL/JALR links and bit-zero clearing, reset GPR reads/x0, lane masks, signed loads,
ROM loads, stores, memory actions to x0 and all nine fatal fault codes.

The SV bench compares every retirement field/order and sticky fault, checks
request stability, one outstanding/no duplicate acceptance, latency 1..4 and
bounded progress. Memory has reviewed ROM/RAM permissions; byte writes happen
only on successful response acceptance. Every successful memory response must
match one memory retirement; final full RAM and halt inactivity are checked.
This standalone SV fabric is independently written; the Python T009 model is
not connected to XSim here. MMIO remains unsupported by this test fabric.

The common unit driver supports a full-program wrong-expected-bit input: retain
the entire program, flip first scenario's expected fault tval, and require the
specific CORE_MISMATCH fault diagnostic. This prevents a truncated-input rejection
from masquerading as an expected-value comparison. Existing single-row units
retain their previous negative stimulus. Two new driver policy tests check both
modes. Actual empty-file rejection remains required. Parser records count inputs;
they are not retirement counts. CORE_TOTAL/coverage report actual scenario and
retirement totals separately. WDB, inputs, exact source/Tcl/argv hashes retained.

Required gates: harness finish T010 --evidence evidence/daily/T010.md invokes
verify.py lint, verify.py test-core and both whitespace checks. A capture/mux
probe exposes every core output using bounded FPGA pins for structural synthesis.
This is not the final top, full FPGA implementation, timing closure or hardware.
Full independent ISS comparison, pipeline, ISA/EEI closure, formal, interrupts,
routed FPGA and ASIC evidence are later mandatory milestones. No compliance or
project-completion claim follows from directed reference-core execution.

Acceptance passed on attempt 1: all four outer gates, 21 lint checks/12 commands,
reference-core synthesis command 32.562 s with zero warnings/errors and structural
checks passing. Seven driver policy and three program tests passed. Two positive
XSim runs each parsed 716 input records and matched 162 retirements/11 faults
(324 retirements and 22 scenarios total), in 1,265/1,250 modeled progress cycles
plus separate reset/halt checks. Simulations took 2.500/2.469 s. All 64 declared
bins hit. Actual wrong fault tval and empty input were rejected. The source,
wave/input/Tcl/argument hashes and exact results are in evidence/daily/T010.md.

T011 adds actual retirement/fault and terminal GPR/RAM trace export to this
bench, without production RTL or protocol-monitor changes. The separate ISS
ignores these directed expected rows and independently compares execution and
terminal samples; see ISS.md and evidence/daily/T011.md. Full RAM still has the
original SV scoreboard. This strengthens directed evidence, not ISA certification.
