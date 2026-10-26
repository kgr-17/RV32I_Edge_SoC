# T007 branch and jump unit

`branch_unit` is combinational: op_t, PC, rs1, rs2 and decoded 32-bit immediate
produce target[31:0], taken, misaligned and supported. Supported operations are
BEQ/BNE, signed BLT/BGE, unsigned BLTU/BGEU and unconditional JAL/JALR.
Targets wrap modulo 2^32. Branch/JAL use PC+immediate; JALR uses rs1+immediate
and clears bit zero before the four-byte alignment test.

An untaken branch outputs target=0/misaligned=0 even if its hypothetical target
would be misaligned. Unsupported operation IDs output all zeros. A taken bad
target retains taken=1 and the target value, with misaligned=1: taken describes
the condition, not permission to redirect. The caller must create an age-ordered
instruction-address fault and suppress a bad redirect. Link PC+4, sequential
PC advance, valid/flush and precise retirement remain caller responsibilities.
No fault halt, memory request, register write or pipeline state occurs here.
This follows unchanged approved v0.2 and the pinned RV32I 20240411 manual.

Independent Python tests use predicate tables, signed integer conversion,
unbounded integer arithmetic/modulo and division rounding for JALR masking.
They cover all comparisons, both outcomes, both alignments, small signed domains,
full-width edges, all I immediates for JALR, walking/boundary JAL offsets,
PC wrapping and random irrelevant operands. Tests include false branches with
misaligned hypothetical targets, and odd JALR sums becoming aligned after
bit-zero clearing. Seeds 1/20261025 replay exact vectors. Six anchored oracle
tests and actual wrong-answer/empty-file rejection supplement all-output checks.

Lint uses `branch_lint_top`, a synthesis probe that captures the four independent
operand words through a 32-bit port. This retains unrestricted independent DUT
values while keeping probe pin count bounded; functional DV instantiates the
combinational unit directly. Probe registers are not CPU architectural state.
The gate remains real synthesis plus strict warnings/latch/black-box/structural
checks, not routed timing. No original XPR/XDC/package/ALU/RF RTL is changed.

Required commands: python -B scripts/verify.py lint and test-branch. Registered
regress includes branch DV. The generic driver saves source hashes, generated
Tcl/argv/vector/WDB hashes, versions, exact counts and coverage. Results belong
in evidence/daily/T007.md, the timestamped receipts and today's same two reports.
