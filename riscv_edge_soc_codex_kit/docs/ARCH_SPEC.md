# Architecture v0.1 — controlled design contract

**DESIGN STATUS: proposed, not implemented. Owner must review before architecture freeze.**

## Core

- RV32I 32-bit instructions, 32-bit address bus, byte-addressable little-endian.
- Architectural GPR x0 always 0; x1..x31 write at retirement edge, deterministic read/write bypass convention documented per regfile test.
- Stages IF → ID → EX → MEM → WB; single-issue, in-order; valid bit per interstage pipeline register.
- IF: PC, instruction request; ID: decode, regfile, immediate; EX: ALU, branch compare / target; MEM: load-store request and wait; WB: GPR commit.
- Branch/JAL/JALR resolved in EX; JALR clears bit 0; squash younger instructions; no wrong-path architectural commit.
- Bypass: EX/MEM→EX and MEM/WB→EX; do NOT forward load data until returned. Stall at least one cycle for unresolved load-use; exact cycle policy proven by tests.
- During memory backpressure, maintain transaction stability and freeze dependent stages; design defines one outstanding request until response.
- Hazard/control priority **reset > memory response hold > taken redirect/flush > dependency stall > advance**; exception handling is out of the MVP and requires a separate design revision.
- Unsupported instruction behavior in MVP: report test failure/simulator error, not a standards-compliant architectural trap. Architectural certification is explicitly out of scope until trap/CSR support is complete.
- Base support groups: LUI/AUIPC/JAL/JALR, BRANCH (BEQ/BNE/BLT/BGE/BLTU/BGEU), OP-IMM, OP, LOAD (LB/LH/LW/LBU/LHU), STORE (SB/SH/SW). FENCE may be treated as no-op only for documented uncached single-hart model; `ECALL/EBREAK` support deferred and must NOT be counted as complete RV32I.
- Misaligned load/store: MVP self-checking tests avoid them; exception/trap support required before complete ISA conformance claims.

## Memory and bus

- Initial instruction memory: 64 KiB ROM/BRAM at 0x00000000–0x0000FFFF; reset PC 0x00000000.
- Initial data memory: 64 KiB RAM/BRAM at 0x00010000–0x0001FFFF.
- UART registers: 0x10000000 TXDATA, 0x10000004 STATUS (bit 0=TX_READY), 8-bit TXDATA field, byte stores supported.
- GPIO at 0x10000020, TIMER at 0x10000100/0x10000104; registers and semantics finalized in individual peripheral tasks.
- Core data interface candidate: request-valid/request-ready, 32-bit addr/wdata/rdata, 4-bit byte strobes, read/write indicator, response-valid / response-data. One outstanding transaction; request must not be replayed after accepted. Bus addresses byte addressed; read lane shift/sign extend in load/store unit. Document exact RTL ports and timing in architecture-freeze milestone.
- Initial ROM read latency synchronous 1 cycle; data RAM response latency 1 or more cycles, potentially randomized by DV memory model. Core must not rely on zero wait states.
- AXI4-Lite bridge is a **later optional adapter**, not core's native interface. No AXI full/multi-beat claims. DMA is later optional and will require arbitration+memory consistency specification.

## Reset and clock

- Core single synchronous 100 MHz external board clock or slower generated *clock enable* where supported. No fabric-derived clocks.
- External asynchronous pushbuttons must go through appropriate synchronizer and debouncer. FPGA async-reset assertion with synchronized release may be used in top if documented; core module reset policy must be defined during T002.
- An externally sampled UART RX (stretch stage) needs properly synchronized sample path; no unjustified CDC waiver.

## Retirement trace for DV

Expose registered `retire_valid`, `retire_pc`, `retire_insn`, `retire_rd`, `retire_rd_wdata`, plus memory operation metadata. Commit events must be in program order and one per retired instruction (x0 writes are architecturally ignored). `retire_valid` must never assert for a flushed/wrong-path instruction. This is an RVFI-inspired interface, **not automatically RVFI compliant**.

## Performance observations

- Record IPC/CPI on explicitly defined benchmark instruction mixes, instruction count, cycles, pipeline stall cycles. Use no fabricated performance data.
- FPGA clock constraint begins at 100 MHz Basys3 oscillator (pin W5), but achievable Fmax and closure depend on actual timing reports. 100 MHz input does not imply 100 MHz CPU timing closure.
- Only compare equal RTL configurations and identical constrained flows for PPA comparisons.

## Forbidden in L1

Cores > 1, MESI/coherent cache, speculative out-of-order execution, branch prediction, Linux, virtual memory, DDR/PCIe, full AXI4 or AXI-stream. Keep these as separate projects if ever pursued.
