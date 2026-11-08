# T031 integrated SoC boot

Started November 6 from T030 commit b94e043; resumed November 7. All four final gates passed on attempt 1.
Approved v0.2 ISA/fatal-halt EEI, memory map,100MHz target, reset/flush priorities
and existing CPU/peripheral/memory RTL remain unchanged. Initial native compiled
SoC boot has passed, but integration/production-divider/fabric gates remain.

New rtl/soc/soc_fabric.sv connects separate one-outstanding instruction/data
channels to dual-read64KiB boot ROM,64KiB RAM and the verified UART/GPIO/timer.
Instruction fetch is aligned ROM-only. Data ROM is read-only; RAM is read/write;
exact allocated peripheral regions route full byte addresses and byte enables,
unallocated/malformed accesses error. A registered pending target holds each
response; no consume-edge replacement. RAM writes and peripheral effects occur
only at successful response acceptance. Shared reset cancels pending state and
peripherals while preserving RAM storage. New edge_soc.sv wires the unchanged
pipeline_core and exposes its existing retirement/fault observation ports for DV.

sw/soc_smoke.S uses the original boot.S/linker.ld and actual pinned GNU RV32I/
ILP32 tools. A separate fpga/basys3/soc_boot.mem preserves T026 rom_init.mem.
It checks copied data/BSS, byte/halfword/sign behavior, persistent RAM word,
GPIO input/OUT/SET/CLEAR, timer rollover/W1C, received0x41, FENCE and transmits
PASS CRLF. Success drains TX, writes signature600d600d, returns0 and reaches the
reviewed ECALL fatal halt. UART writes intentionally encounter hardware busy
backpressure. Failure prints FAIL and returns1. No CSR/interrupt implementation.

The independent bus environment reuses the timestamp/bit-set/closed-form
peripheral oracles and a separate RAM image. Architectural comparison uses the
existing independent ISA interpreter unchanged, with a new verification-only
MMIO extension that consumes gold response snapshots. Every observed request/
response, retirement, fault and RAM effect is checked. An independent decoder
samples actual TX output intervals and verifies bit widths/8N1/ASCII; firmware
printing a marker alone cannot pass. Warm reset must reinitialize runtime state
and preserve the counter outside linker initialization, advancing1 then2.

Initial preparation soc-boot-preparation-20261107T035106853512Z PASS23checks/
19commands at fast divider8,1970 cycles, two187-retirement boots, UART PASS CRLF
twice,118 data responses/440 instruction responses,664 busy request-wait cycles,
22 physical RAM write effects. This is actual compiled CPU/memory/MMIO simulation,
not the earlier ISS-only boot. Native source-list preparation before it failed
xelab(missing pipeline_core): it selected the stage-only lint design; archived
17 source inputs/32 generated hashes and corrected the build source list only.

The canonical FPGA top now instantiates reset_sync and edge_soc. Raw RX and
switches enter the existing UART/GPIO synchronizers once. All 36 ports, pin
constraints, clock, part and reset priorities are unchanged. The original
diagnostic body is retained byte for byte except its module name in
fpga/basys3/diagnostic_top.sv, with the original vectors and negative controls.
Its synthesis checks still inspect those diagnostic pins; they do not establish
full SoC timing, resource fit or full-target CDC closure.

Native preparation soc-20261107T205446617903Z passed 60 checks / 32 commands:
two fabric seeds checked 4006 and 3970 edge rows, including all 64 offset/mask
combinations per region, distinct simultaneous ROM reads, 268/271 selected RAM
locations written before readback, high address bits, invalid fetches, ROM writes,
held responses, busy UART and reset-canceled RAM/GPIO operations. Three actual
bad-input simulations and a coherent early-RAM-write RTL mutant were rejected.

Two fast runs each checked 1970 cycles and two 187-retirement boots. The actual
canonical basys3_top at production divider 868 checked 121330 cycles and two
4357-retirement boots; 86664 cycles of data-request backpressure were observed.
Each phase independently decoded PASS CRLF, checked the entire physical RAM
against architectural state and advanced the persistent counter from 1 to 2.
An actual image with one corrupted data-load byte was rejected at bus cycle 39;
wrong-retirement, truncated and empty traces were also rejected.

For board use this verification firmware expects a host to send ASCII A after
reset, then performs the tests and prints PASS at approximately 115200 baud,
8N1. This is a simulation firmware image, not evidence of a programmed board.

## Reproduction and recovery

```powershell
python -B scripts/verify.py test-soc
python -B scripts/verify.py lint
python -B scripts/project_integration.py
python -B scripts/project_integration.py --apply
```

The last command updates sources in the existing XPR, never runs synthesis or
programming. It snapshots the XPR and generates a manifest under a fresh
build/T031 directory. The Tcl refuses unknown existing sources, constraints or
top and adds missing inputs idempotently. The tracked XPR contains the exact
config/fpga_build.json source/image list. A source-only recovery archive is
evidence/prepare/T031-before-integration/inputs.zip; compare selected members in
a new local directory before restoring anything. The baseline commit also
retains the old project. No original source or constraint has been deleted.

Actual integration receipt soc-project-integration-20261107T205550441295Z remains
FAIL: open_project emitted 76 installed Board 49-26 catalog warnings and one
empty BoardPart warning. The operation completed, saved sources and passed an
independent exact XML manifest check; no diagnostics were suppressed or tools
changed. Warning-free nonproject unit lint and native simulation provide the
separate design evidence. Initial production preparation also remains FAIL for
an incorrect waveform hierarchy; the actual board-top run uses correct signals.

Independent lint uses at most two native tools with separate directories and
serialized atomic evidence. Every previous lint check and both failure controls
remain; all submitted jobs finish even after a failure. Native timeout <=120
seconds and aggregate <=600 seconds are unchanged. Tests cover the concurrency
bound, failure retention, complete evidence and command-index associations.

Full-target technology synthesis/route/PPA/bitstream remain T043 owner-controlled;
fabric unit lint and simulation do not establish these. Formal T023 remains
owner-skipped/NOT RUN. T044 interrupt architecture review and all remaining
milestones remain mandatory. No FPGA programming, ASIC or metastability proof.

Final audit: evidence/t031-final-audit-2026-11-07.json; 3 receipts, 60 sources,
522 artifacts, 1182 preserved files, 9462 positive retirements / 36 UART bytes.

T045 compatibility note: the canonical top now defaults to the reviewed interrupt
configuration with irq_boot.mem. The T031 board-top test explicitly selects
ENABLE_TRAPS=0 and soc_boot.mem, retaining all the expectations documented here.
Both images remain in the project. This document and its historical receipts
describe the legacy configuration; see INTERRUPT_REPORT.md for the new mode.
