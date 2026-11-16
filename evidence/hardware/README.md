# T032 supervised Basys 3 bring-up proposal

Prepared 2026-11-15 after owner approval of T043. **T032 is pending; execution
authorization, physical connection, programming and UART capture are NOT RUN.**
This document prepares a reviewable next action. It does not start T032 or grant
permission. No hardware server or serial port has been opened by this session.

## Exact proposed image and scope

Use the existing T043 acceptance image, without rebuilding or changing firmware:

`build/T043/fpga-impl-20261108T212739021522Z/reports/artifacts/design.bit`

SHA-256: `13f3639d2b01feded384a1316207a0ddb02fb5d4036bc399901fc87fd2aacbd9`.
Target: Digilent Basys 3, `xc7a35tcpg236-1`, one 100 MHz clock; image part
`7a35tcpg236`, native header 2026/11/08 13:31:04. The unchanged production
configuration is `basys3_top`, `ENABLE_TRAPS=1`, UART divisor 868, `irq_boot.mem`.
Firmware source `sw/interrupt_smoke.S` SHA-256:
`86facd959133db5b973b617be91c4d0167bb04d5227bf08ca1440da699c7c7e5`.
ROM image SHA-256:
`d52196d93577a9dc4f4d661aae72bf2b6a1ee837034610cfe409ff5c1c7856fd`.
The T043 manifest, review package and 176-member ZIP preserve the source/image
bindings and native checkpoints/reports. Verify hashes before any programming.

Proposed authorization covers a local hardware-server connection, identifying
the owner's board/serial interface, loading this bitstream through JTAG into
volatile FPGA SRAM, and capturing UART under owner supervision. This replaces
the running FPGA configuration. SPI flash, configuration-memory writes, eFuses,
keys, new images, remote targets and driver/tool installation are outside this
proposal. No global configuration changes or unattended automation.

The [Digilent Basys 3 manual](https://digilent.com/reference/_media/reference/programmable-logic/basys-3/basys3_rm.pdf),
rev C, sections 2.1 and 5, identifies J4/PROG as the on-board USB-JTAG/UART
connector. JTAG overwrites the running SRAM configuration; it does not persist
through power loss. The DONE LED indicates configuration completion, not CPU
test success. The owner should connect the board by a data-capable cable, power
it according to the manual, confirm the physical board/revision and retain the
ability to press btnC. No other attached target may be selected implicitly.
Official documentation was read on 2026-11-15 under the existing authorization
for official documentation reads; no tool, package or IP was downloaded.

## Procedure after explicit authorization

1. Preserve a clean Git baseline, record the exact owner reply in a task-specific
   receipt, then execute the owner-authorized command:
   `python -B scripts/harness.py authorize T032 --confirm-owner-review`.
   Re-evaluate `next`; begin T032 only when the harness selects it. No `finish`
   attempt is spent merely to discover missing hardware or checks.
2. Implement and independently validate the hardware evidence capture/checker
   under active T032. Keep all logs/temporary files project-local and append the
   same two daily reports. The current registry has **no `hardware-evidence`
   entry**; this is NOT RUN and must be implemented, not bypassed or replaced by
   a simulation PASS. Preserve the existing required lint and test-soc gates.
3. Enumerate only relevant local JTAG and UART interfaces, save board/target/cable
   identity, device part, IDCODE where available, and COM port association. Require
   an unambiguous owner-confirmed Basys 3. Stop on ambiguous identity, another
   device/part, missing board or unavailable driver; do not install a driver or
   guess/select the first matching device. Record actual Vivado/hw_server versions.
4. Prepare a fresh bounded project-local run directory. Recheck image/ROM/source
   hashes and approved T043 receipt, hardware identity and active authorized T032
   before the programming call. Save exact Tcl/job/stdout/stderr/exit status.
   The [AMD UG835 2025.2 command reference](https://docs.amd.com/r/2025.2-English/ug835-vivado-tcl-commands/program_hw_devices)
   documents setting `PROGRAM.FILE` on the selected hardware device and invoking
   `program_hw_devices`. Build explicit target/part/hash guards before using those
   commands; do not use a first-device default, force flag or warning suppression.
   No hardware Tcl/programming script has been executed or delivered by this
   proposal; the guarded implementation is work for authorized active T032.
5. Open the confirmed UART at 115200 baud, 8 data bits, no parity, one stop bit,
   no flow control. Save raw bytes and timestamps, baud/settings, run/image identity
   and host command. A project-local .NET SerialPort helper can avoid a package
   installation; validate its capture/error handling before physical use. Do not
   read unrelated COM ports or treat simulator files as board captures.
6. Capture while the owner presses and releases **btnC**, the core reset input.
   A normal deliberate press comfortably exceeds the required four clock edges.
   btnC is distinct from the board's PROG configuration control. Firmware prints
   once per boot, so capture must already be active before reset release. Preserve
   any partial initial output instead of replacing it with an expected string.
7. Require the exact physical bytes `IRQ PASS\r\n` (hex
   `49 52 51 20 50 41 53 53 0d 0a`) and no `IRQ FAIL`, framing/capture error or
   unexplained extra bytes in each bounded boot observation. Repeat one warm
   reset without reprogramming, save both epochs and the owner's button/DONE
   observations. Retain timeouts/failures. Missing data never becomes PASS.
8. Run all registered T032 gates from the frozen tested state through `finish`,
   then request final T032 owner review. Successful programming alone is
   insufficient. No subsequent task begins while T032 is failed or awaiting
   review. Preserve the prior T043 archive and all failure history.

## What the physical observation can establish

The current interrupt firmware needs **no host input**. It services the reviewed
timer through machine-external cause 11, returns via MRET, checks saved s0/s1,
prints `IRQ PASS\r\n`, then spins. It does not contain the legacy firmware's
ASCII-A receive prerequisite, GPIO LED test or `PASS\r\n` success marker.
General-purpose LEDs are therefore not an IRQ success oracle for this image.
Do not swap images or expect LED/switch/RX tests without a separately reviewed
build and its new source/bitstream bindings.

Two physical serial success messages support this particular firmware's boot,
interrupt/return and UART path. They do not expose every retirement, internal
CSR value, persistent RAM counter or IRQ waveform. Do not copy the simulator's
retirement counts, counter values or bus traces into physical evidence. Additional
internal observations require instrumentation and a separately bound implementation.

Required physical evidence must include owner authorization, board identity,
programming command/result, tool versions, exact bitstream and firmware bindings,
raw UART transcript, capture settings/times, reset epochs and observations.
Record unobserved items honestly. T023 formal remains owner-skipped / NOT RUN;
small routed margins (+0.123 ns setup / +0.013 ns hold), unspecified external I/O
delays and low-confidence vectorless power remain the T043 limitations.
Hardware validation and ASIC evidence remain separate.

## Handoff at this proposal

T043 is completed after the owner's exact approval-command authorization.
T032 is dependency-ready but lacks start permission; harness `next` is null
because it excludes unauthorized tasks. Do not call `authorize`, `begin`, program
or open hardware from this document alone. The next owner decision is whether to
authorize the scope above and the exact T032 authorize command. Physical board
availability and identity must then be established before programming.
