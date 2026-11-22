# T032 supervised Basys 3 bring-up

Proposal prepared 2026-11-15 after owner approval of T043. The owner explicitly
authorized it in question `call_9053eb495dcb4c1f9a981401711da49e`; authorization
and command receipts are in `evidence/owner_reviews/T032-2026-11-15-*.json`.
The original approved proposal remains at commit `a85f71c` with its pinned hash.
On 2026-11-21 T032 began, identified the local board, and successfully loaded the
approved image into volatile FPGA SRAM. **Physical UART/reset validation and
T032 acceptance are pending.** Do not request the same authorization again.

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

## Execution tooling and current handoff (2026-11-21)

`scripts/hardware.py` supports inventory, explicit target/device/COM programming,
and bounded capture (5-60 seconds per epoch). Its Tcl rechecks live job/authority
before connect and programming. `hardware_serial.py` uses Win32 UART APIs without
external packages. PowerShell is used only for native read-only PnP enumeration;
no execution policy is changed. T032's new registry entry runs independent
policy tests then `hardware_evidence.py`; it never performs device operations.
Without the completed physical session input, it returns NOT RUN.

Actual board: `localhost:3121/xilinx_tcf/Digilent/210183B03B59A`, `xc7a35t_0`,
part `xc7a35t`, IDCODE `00000011011000101101000010010011`. The common observed USB
parent `210183B03B59` joins JTAG interface A and UART interface B / COM3. Actual
inventory receipt: `inventory-20261122T015411030005Z.json`. Programming receipt:
`program-20261122T015603204700Z.json`, exit0/PASS without native diagnostics.
The captured receipts retain actual Vivado2025.2 SW6299465/hw_server2025.2 output.

Do not reprogram blindly after an interruption. Inspect those receipts and
existing captures first. Programming success is separate from UART evidence.
Capture requires an owner-operated btnC reset with capture already listening:

```powershell
python -B scripts/hardware.py capture --program evidence/hardware/program-20261122T015603204700Z.json --epoch 1 --seconds 60
```

Use epoch2 for a second warm reset without reprogramming. Preserve raw uart.bin,
timestamped events, exact commands, process errors, and all empty/failed captures.
Owner DONE/reset observations must identify the actual reply, not be inferred
from a PASS marker. Bind the programming receipt, two successful captures and
owner observations by SHA-256 in `evidence/hardware/session.json`. The checker
requires ordered, distinct epochs, exact IRQ PASS CRLF bytes and matching events.
Never manufacture a missing physical observation or use policy fixtures as data.
Then run the unchanged required T032 lint/test-soc/hardware-evidence finish gates.
Final T032 owner review is still required; no approval command is authorized yet.
