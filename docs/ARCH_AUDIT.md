# Architecture audit — proposed, not frozen

The original kit's v0.1 design is a useful starting proposal, not implemented or
owner-approved hardware. T002 now supplies explicit proposed resolutions in
ARCH_SPEC v0.2 and ARCH_CONTRACT.json; ARCH_REVIEW.md lists the owner decisions.
All resolutions remain subject to owner review. No RTL exists.

1. FPGA part is known from XPR; the owner confirmed Digilent Basys 3 on
   2026-10-14. On 2026-10-16 the official manual confirmed the 100 MHz W5 source.
   Full XDC and actual timing/hardware validation remain future work.
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
   certification claim is implied by unit tests. Required later interrupts now
   have explicit T044/T045 review/implementation tasks; AXI4-Lite and DMA remain optional.
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
reviewed later interrupt support, actual FPGA implementation and authorized
hardware; approved ASIC block flow;
final evidence and owner review. No architecture decision was silently frozen.
