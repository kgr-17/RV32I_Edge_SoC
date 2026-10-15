# Architecture audit — proposed, not frozen

The original kit's v0.1 design is a useful starting proposal, not implemented or
owner-approved hardware. Preserve it while resolving T002. No RTL exists.

1. FPGA part is known from XPR; board and oscillator/pin assignments are not.
   Basys3 and 100 MHz are candidate assumptions only.
2. Specify precise core reset polarity/synchrony, reset PC, cleared valid bits,
   register-file initialization policy and reset during outstanding transactions.
3. Freeze instruction/data request-response ports and timing, transaction
   ownership, error semantics, byte lanes and synchronous BRAM latency.
4. Review proposed memory map and UART TX/RX, GPIO and timer register semantics
   before implementing peripherals. No map has yet been verified.
5. Review stall/flush/backpressure priority and retirement metadata, including
   memory writes and younger wrong-path work, before pipeline implementation.
6. The original MVP omits ECALL/EBREAK/traps and some execution-environment rules.
   That subset cannot satisfy the owner's full RV32I completion requirement.
   T041 explicitly closes instruction/EEI behavior after reviewed design; no
   certification claim is implied by unit tests. Interrupts remain a later
   separately reviewed milestone; AXI4-Lite and DMA remain optional.
7. UART RX is mandatory per the owner, although the kit called it stretch scope.
   T042 covers synchronization, framing/error handling and MMIO reception.
8. Script creation does not prove FPGA implementation. T043 requires actual
   synthesis/routing/timing/utilization/power evidence before physical bring-up.
9. Final T040 depends on every mandatory task. Optional extension status must not
   prevent mandatory project completion; final owner approval is always required.

Initial sequence: bootstrap T001; architecture proposal/review T002; approved
toolchain/CI T003; decoder, ALU, register file, branch and load/store units; bus
models; reference core and independent ISA interpreter; five-stage pipeline,
hazards and complete ISA behavior; DV closure; board/SoC/peripheral integration;
actual FPGA implementation and authorized hardware; approved ASIC block flow;
final evidence and owner review. No architecture decision was silently frozen.
