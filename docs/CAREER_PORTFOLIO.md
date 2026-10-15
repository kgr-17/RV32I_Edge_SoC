# 以招聘面试为中心的验收体系

## 四条求职主线

- RTL Design: RV32I decode、ALU、regfile、五级流水线、hazard forwarding、synthesizable coding。
- Design Verification: self-checking directed/random, independent ISS model, retirement scoreboard, SVA, functional coverage, regression, defect injection, negative tests。
- FPGA/Hardware Validation: Vivado Tcl, XDC, BRAM, UART, clock/reset, button CDC, on-board UART output, waveforms and hardware debug logs。
- ASIC/SoC: handshake, optional AXI4-Lite, PPA synthesis/STA, physical flow exploration, documentation, timing paths, DRC/LVS where supported。

## 简历项目 bullet（完成后按真实数据填写）

- Designed a 32-bit, 5-stage in-order RISC-V CPU in SystemVerilog with forwarding, hazard detection, pipeline stalls, and branch flush; verified ___ instruction cases and ___ randomized seeds against an independent ISA reference.
- Developed pre-silicon verification infrastructure with assertions and functional coverage, achieving ___ measured coverage on ___ specified reachable bins and zero known failures in ___ scoped regressions.
- Integrated the core on a Digilent Basys3 FPGA with BRAM/UART peripherals and automated Vivado reports; met ___ MHz in ___ build with WNS ___ ns and ___ LUTs (actual implemented reports only).
- Explored open-source ASIC implementation of ___ block with ___ library/PDK/corner/clock constraint and reported area/timing/power limitations without claiming tapeout.

**Do not copy these bullets into a real resume until numbers are measured and verifiable.**

## 你必须能手动回答的 10 个问题

1. Why is load-use hazard different from simple ALU forwarding?
2. What is the exact stall vs flush priority and why?
3. Which stage resolves a taken branch, and how many younger instructions are squashed?
4. How do store byte enables and sign extension work in RV32I?
5. How does your reference model avoid mirroring DUT bugs?
6. What does your coverage model include and exclude?
7. Why is `valid&& !ready` stability important, and how is it asserted?
8. How do you constrain a 100MHz board oscillator without inventing Fmax?
9. What is CDC and what are the limitations of a two-flop synchronizer?
10. How do ASIC timing/library constraints differ from Vivado FPGA implementation?

## Project release page

After verified bring-up, create a concise README with architecture block diagram, table of ISA supported/unsupported, simulated regressions, example timing report, UART video/transcript, test reproduce commands, bug investigations, and toolchain versions. Be accurate and modest about remaining gaps.
