# 项目章程 — RV32I Edge SoC

## 目标与求职价值

目标不是“尽可能多的 feature”，而是提供一个可解释、可验证、可复现、可被质疑的 RTL-to-hardware 项目：

1. 微架构：single-issue, in-order RV32I core（先单周期/多周期教学参考，再五级流水线）。
2. 验证：directed / randomized / scoreboard / assertion / coverage / regression / optional formal。
3. FPGA：Basys3 实机跑 bare-metal 程序，UART 输出结果，RTL synthesis + implementation + timing closure。
4. ASIC：先对独立模块做 Yosys / OpenROAD / LibreLane 工艺探索，条件成熟再尝试完整 CPU，明确前后端边界和 PDK 约束。

## 关键词 → 可核验证据

| 招聘关键词 | 交付物 | 证据 |
|---|---|---|
| SystemVerilog / RTL / FSM | CPU stages, controller | 编码规范 + lint + test |
| Microarchitecture / Pipeline | forwarding, hazard detection | RAW/load-use/control-hazard directed waveform |
| AMBA / AXI-Lite | optional bridge | protocol assertions + backpressure tests |
| Design Verification | scoreboard, reference ISA model | seed reproducible regression report |
| SVA / Formal | invariant library + bounded proof | property list and formal log |
| Functional coverage | op families / hazard crosses | coverage bins and uncovered bins |
| Hardware validation | UART, button sync, Basys3 | physical log + board settings + UART transcript |
| CDC / reset | external inputs synchronizers; optional dual-clock FIFO | reset/CDC structural checks |
| Synthesis / STA / PPA | Vivado / ASIC reports | part/clock/constraints/version + WNS/Fmax/resources |
| CI / regression | GitHub Actions | CI badges linking to reproducible checks |
| ASIC flow | Yosys + OpenROAD/LibreLane | cell area, report constraints and limitations |

**Not claiming:** commercial UVM implementation, tapeout, silicon validation, formal signoff, RISC-V certification until actually and independently demonstrated.

## Release boundaries

- L1 Core: every supported instruction family works on simulation; verified pipeline hazards and retirement semantics.
- L2 SoC: repeatable Basys3 boot + UART + timing reports. This is *FPGA hardware validation*.
- L3 Stretch: optional CSR/exception/interrupt/AXI/DMA/formal/ASIC experiments with separate acceptance; avoid feature inflation.

## Decisions fixed for MVP

- 32-bit RV32I subset, no compressed, FPU, vector, multicore, cache coherence, Linux, MMU, superscalar.
- No arbitrary external proprietary IP. One clock domain for core+SoC on FPGA initially.
- 32 x 32-bit GPR (`x0` hardwired zero), little-endian, 4-byte aligned instruction fetch.
- Branch resolved in EX with younger instruction flush; MEM delayed response stalls pipeline, priority defined in ARCH_SPEC.
- Physical constraints are not simulated performance. ASIC and FPGA frequency/area are separate measurements.

## Decision gates

Owner reviews at architecture freeze, basic core, pipeline, DV closure, hardware bring-up, and ASIC planning milestones. No auto-skip; if blocked, stop and report.
