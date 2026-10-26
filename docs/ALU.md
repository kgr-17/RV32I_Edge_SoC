# T005 combinational ALU

`alu` consumes `rv32_pkg::op_t op_i` and two 32-bit operands `a_i/b_i`.
It produces `result_o[31:0]` and `supported_o`. No clock/reset/state is present.
The caller selects register/immediate/PC operands. Arithmetic wraps modulo 2^32;
overflow is not a trap. Signed and unsigned less-than return exactly 0 or 1.
All shifts use `b_i[4:0]`; SRA/SRAI propagate the sign bit, SRL/SRLI fill zero.

Supported selectors are the 19 ADDI..AND enum entries (IDs 19..37): ADD/ADDI,
SUB, SLL/SLLI, SLT/SLTI, SLTU/SLTIU, XOR/XORI, SRL/SRLI, SRA/SRAI, OR/ORI,
AND/ANDI. Other selectors produce zero with supported=0, a local unit diagnostic
rather than an architectural illegal-instruction event. Address/PC additions may
use OP_ADD after caller operand selection. LUI passthrough, branch comparison,
target handling, memory/retirement and faults belong to later units.

The unchanged approved v0.2 contract and its pinned
[RV32I manual](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html)
govern behavior. No ISA or external core interface changed.

Verification commands are `python -B scripts/verify.py lint` and
`python -B scripts/verify.py test-alu`. The independent Python oracle uses
unbounded integer arithmetic followed by modulo reduction, multiplication/floor
division for shifts, signed integer comparisons and direct bitwise truth rules.
It imports no RTL. Six fixed oracle tests anchor overflow, sign comparisons,
shift masking/sign fill, bitwise behavior, unsupported selectors and aliases.

Per seed, stimuli exhaust the 64-value signed small domain (-32..31) crossed
for every selector, cross 17 full-width edges, exercise every shift amount with
four different ignored upper-bit patterns, add 1,024 random pairs per supported
selector and challenge all 45 unsupported six-bit selectors. Shuffled rows
exercise default clearing between unrelated operations. Bench checks all 32
result bits plus support flag after 1 ns and requires exact nonzero count.
Actual wrong-answer and empty-file runs must fail acceptance.

`scripts/unit_checks.py` is reusable unit DV infrastructure. It checks configured
inputs, pinned versions, declared hit bins, exact simulator completion, clean
diagnostics, waveform presence and source hashes. It uses project-local generated
Tcl, vectors, argument files and WDBs under `build/units/alu-*`; full evidence is
`evidence/toolchain_runs/alu-*.json`. Manifest replay seeds are 1 and 20261025.
Five unit-driver policy tests and the retained acceptance-policy tests supplement
DUT comparisons. `regress` now includes test-alu as well as decoder/fixture DV.

This proves only the ALU unit's checked behavior. Formal, complete execution,
pipeline, routed timing, physical hardware and ASIC evidence remain separate.
