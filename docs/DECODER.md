# T004 decoder unit interface

`rtl/core/rv32_pkg.sv` precedes `rtl/core/decoder.sv` in source order.
The module is purely combinational: `insn_i[31:0]` -> `decode_o` of type
`rv32_pkg::decode_t`. It has no clock, reset, pipeline state or side effects.
This is the first production RTL unit, not a complete CPU.

| Packed field | Bits | Meaning |
|---|---:|---|
| op | 56:51 | Explicit six-bit operation enum: ILLEGAL=0, supported operations 1..40 in approved contract order. |
| imm | 50:19 | Reconstructed 32-bit immediate; rules below. |
| rs1 | 18:14 | Source index when uses_rs1; otherwise 0. |
| rs2 | 13:9 | Source index when uses_rs2; otherwise 0. |
| rd | 8:4 | Actual nonzero destination when writes_rd; otherwise 0. |
| uses_rs1 | 3 | Instruction reads the first operand, including x0. |
| uses_rs2 | 2 | Instruction reads the second operand, including x0. |
| writes_rd | 1 | A nonzero GPR destination exists. |
| illegal | 0 | Unsupported/reserved encoding; every other field is 0. |

I/S immediates sign-extend 12 bits. B sign-extends the 13-bit byte displacement,
including its zero low bit; J similarly sign-extends 21 bits. U preserves the
upper 20 instruction bits and supplies 12 zeros. SLLI/SRLI/SRAI expose only the
zero-extended five-bit shift amount; the operation enum selects arithmetic
versus logical shift. R, FENCE, ECALL and EBREAK expose immediate 0.

All 40 mnemonics in architecture v0.2 are classified. Every required funct3 and
funct7 is checked. SYSTEM accepts only exact ECALL/EBREAK words. Other SYSTEM,
M/A/F/D/C, FENCE.I, CSR, unknown major opcodes and reserved shift encodings are
illegal. Legal instructions with rd=x0 remain legal; notably LW x0 still has
OP_LW and uses_rs1. Consumers must derive memory actions from op, never from
writes_rd. FENCE ignores rd/rs1/fm/pred/succ exactly as reviewed; its operation
requires a later serializing full drain. No memory ordering is implemented here.

The source of ISA behavior is the owner's pinned
[RV32I 2.1 manual, 20240411](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html)
and the unchanged approved `ARCH_SPEC.md`/`ARCH_CONTRACT.json`. No new external
core, IP, package or tool was imported. Four-state unknown instruction inputs
are outside the binary instruction interface; exact simulation comparisons
reject unknown DUT outputs for every supplied binary vector.

## Verification and reproduction

```powershell
python -B scripts/verify.py lint
python -B scripts/verify.py test-decode
python -B scripts/verify.py regress
```

The first two are T004's required gates, executed by harness finish. `regress`
now includes both the original infrastructure fixture and the decoder gate.
No fixture vector is sent to the decoder. `config/rtl_checks.json` separates
production lint-only designs from fixture simulation designs; unregistered RTL
still produces NOT RUN. Lint uses real Vivado synthesis, latch/black-box rejection
and LUTLP-1/MDRV-1 checks. It is not timing closure or comprehensive static lint.

`dv/unit/test_decoder.py` is an independent flat mask/value oracle, not a parse
or translation of the RTL case tree. It constructs legal instructions from
original immediate/register values and compares expected metadata against the
oracle before emitting them. Six Python tests check fixed instruction words,
disjoint encodings, exact approved inventory, illegal metadata, load-to-x0 and
ignored FENCE fields. Generated stimuli exhaust I/S and B immediate spaces for
each relevant operation, every shift amount and all OP/OP-IMM funct7/funct3 pairs.
They include walking U/J bits, both signs/boundaries, all register indices and
zero-register forms, FENCE ignored fields, SYSTEM reserved fields, all major
opcode/funct3 pairs, explicit excluded encodings and random words/legal inputs.
The two replay seeds are 1 and 20261023. Rows are shuffled to exercise default
clearing across unrelated operations. Per-operation and stimulus-group hit
counts are recorded; these are not code coverage or full ISA execution coverage.

`tb_decoder.sv` compares all 57 output bits with case inequality after 1 ns per
vector, rejects malformed/empty input and wrong counts, and emits one exact
seed/count completion marker. `scripts/decode_checks.py` requires the marker,
clean diagnostics and successful process status, plus nonempty waveforms. Two
actual negative simulations corrupt one expected bit and supply an empty file;
both must be rejected. Commands, versions, vectors, counts, coverage and hashes
are saved in `evidence/toolchain_runs/decode-*.json`; build artifacts live under
`build/T004/decode-*`. The gate uses the existing bounded Windows Job Object
runner and XSim argument-file transport.

Formal, execution/retirement, pipeline, bus/exception ordering, full SoC
synthesis, implementation, timing, physical hardware and ASIC remain separate
future evidence. Unit synthesis does not integrate a board top or configure
the existing XPR; project integration is deferred until a usable top exists.
