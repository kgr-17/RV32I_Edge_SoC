# T025 Basys 3 board boundary and constraints

Completed 2026-11-04 from clean approval checkpoint 9fe0855. All four required
gates PASS on attempt 2. This is board-boundary evidence, not SoC/hardware signoff.
Owner-confirmed board: Digilent Basys 3, xc7a35tcpg236-1. Existing approved
architecture target/100 MHz domain/reset policy remain unchanged.

## Pin evidence and interface

Selected factual pins were read from Digilent's [Master XDC](https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Basys-3-Master.xdc)
and independently checked against the [reference manual](https://digilent.com/reference/_media/reference/programmable-logic/basys-3/basys3_rm.pdf),
sections 4/5, printed page 7, and figure 16, printed page 15. Accessed November 4.
The XDC header says rev B; the 2019 manual applies to rev C. The selected pins
agree; a physical board revision/wiring inspection remains hardware work.
Only selected factual assignments were transcribed; no complete upstream XDC,
IP, package or tool was downloaded/installed. config/basys3_pins.json records the
source locations and independent expected pin/direction inventory.

| Port | Direction | Pins, ascending bit order |
|---|---|---|
|clk|input|W5, 100 MHz|
|btnC|input|U18, pressed high|
|RsRx|input|B18, FTDI/PC TX into FPGA|
|RsTx|output|A18, FPGA TX toward FTDI/PC RX|
|sw[15:0]|input|V17 V16 W16 W17 W15 V15 W14 W13 V2 T3 T2 R3 W2 U1 T1 R2|
|led[15:0]|output|U16 E19 U19 V19 W18 U15 U14 V14 V13 V3 W3 U3 P3 N3 P1 L1|

36 selected port bits, all LVCMOS33; CONFIG_VOLTAGE=3.3, CFGBVS=VCCO.
create_clock sys_clk on clk: 10.000 ns, waveform 0.000/5.000 ns. This is a
constraint, not measured Fmax or timing closure. Unused board peripherals have no
top ports or package assignments. The selected map avoids assigning clocks or
asynchronous inputs to an output pin.

## Implemented diagnostic shell

fpga/basys3/top.sv defines basys3_top. Its current functional scope is a board I/O
diagnostic: synchronized switches drive LEDs and synchronized incoming serial
level loops back to TX. There is no CPU/SoC, MMIO, firmware or UART protocol
controller connected. T031 must replace these explicit diagnostic connections
with the verified SoC; this shell cannot demonstrate instruction execution.

One oscillator clock only, no generated/fabric clock. Reset is active high:
btnC asynchronously sets a two-stage release chain, which releases after two
oscillator rising edges. FPGA INIT=11 holds startup reset; physical bring-up must
still explicitly press/release reset. LEDs clear and TX idles high during reset.
Two synchronizer stages sample each switch bit and RX; data state resets
synchronously. ASYNC_REG/SHREG_EXTRACT attributes preserve the intended chains.
No internal asynchronous core reset or architectural reset priority is changed.
Switch bit synchronization is not mechanical debounce or an atomic multi-bit
sample. RTL simulation cannot prove analog metastability behavior.

No guessed synchronous I/O delays or broad false paths were added to make timing
look complete. Asynchronous entry path analysis, narrow exceptions and actual CDC
reports remain T029. Complete routed setup/hold/unconstrained-path review remains
T043. No board timing, power, physical programming or ASIC claim is made here.

## Existing project integration and recovery

The original XPR was inspected empty, with the selected part and no top/source/
constraint entries. Baseline9fe0855 and .baseline/T025-2026-11-04/project-before.xpr
preserve exact original bytes. evidence/prepare/T025-baseline-2026-11-04.json
binds original XPR and989 tracked files before implementation.

fpga/basys3/integrate.tcl opens that same project, guards the part, all existing
design/constraint files and top before adding anything, then adds just top.sv and
basys3.xdc and selects basys3_top. Unknown user additions cause refusal. No source
deletion or replacement, IP, run launch, bitstream or hardware operation occurs.
Vivado serializes the new source/constraint entries/top, a simulation source
filter and abbreviated run-strategy descriptions; run steps/part remain unchanged.
The script is reusable for this diagnostic checkpoint; later SoC integration must
deliberately extend its guards and source list, not overwrite newly added work.

Opening this installed project's board catalog emits76 Board49-26 warnings for
unavailable unrelated FPGA presets plus Project1-5713 for its empty preset field.
All three preparation records remain strict FAIL despite exit0 and the integration
marker. Session board-flow and empty-preset normalization experiments did not
resolve them and were removed. Their exact scripts/logs are archived under
evidence/failed_sources/T025/integration-preparation/. No warnings were suppressed
and no installed catalog, message severity or global config was modified.
The installed catalog issue remains unresolved. Required test-top independently
checks written XPR structure and the selected part's actual non-project synthesis,
pins, clock, sync attributes and DRC. It does not relabel those preparation records.

## Independent verification and reproduction

Nine Python policy tests challenge missing/extra/duplicate/aliased pins, UART
direction/pins, I/O voltage standard, clock period/waveform, blanket exceptions,
wrong target, malformed XPR and independent reset/sample examples.
The board_model history oracle determines outputs by elapsed edges since the last
asserted reset, rather than reproducing RTL register updates. Seeds1/20261104 each
generate481 vectors: walking ones/zeros on all16 switches, serial levels, reset
holds1/2/5 edges, repeated reset/discard and400 random stimuli. The SV checker also
tests startup reset, asynchronous assertion while the clock stops and no release
without edges. All expected LED/TX/reset values are compared at every sample.
Actual XSim negatives must reject a wrong expected value, empty vectors and a
truncated record with their exact diagnostic; native failure/timeout cannot pass.

Actual non-project Vivado inspection queries all36 synthesized ports against the
independent pin/direction list, all I/O standards, sole clock/period/waveform/source,
config voltage,36 synchronizer attributes and no latch/black box. Actual DRC checks
LUTLP-1/MDRV-1/NSTD-1/UCIO-1 and emits I/O, clock and utilization reports. A separate
intentionally11ns XDC run must fail specifically BOARD_CLOCK_PERIOD. No route.
Generic lint includes this shell in addition to all existing CPU/unit probes;
test-top is added to the regression registry, now20 targets, without removing19.

```powershell
python -B scripts/test_board_checks.py
python -B scripts/harness.py finish T025 --evidence evidence/daily/T025.md
```

Required gates are lint, test-top and both whitespace checks; max3 finish attempts.
The Tcl integration is already applied. Replaying it may emit the documented
installed-catalog warnings; do not treat a zero process exit as a warning-free
integration pass. To inspect or recover a selected old project file, compare the
baseline copy/Git version first; never destructively reset or overwrite user work.

## Retained first gate attempt and repair

Attempt1 receipt `evidence/runs/T025/attempt-1-20261105T041213907265Z.json`:
lint/test-top/working whitespace FAIL, staged whitespace PASS. Vivado and XVlog
rejected four input ports because `input logic` defaults to a net that requires
explicit net type under default_nettype none. Added `wire` to those inputs;
behavior and width are unchanged. No simulation or board-constraint result was
obtained in this failed attempt. Vivado's CRLF XPR rewrite also failed whitespace.
The same XML is now canonical UTF-8/LF, and the integration script normalizes its
own serialization after close. No whitespace policy or diagnostic check changed.
Archive110 source inputs and1,759 generated artifact hashes under
evidence/failed_sources/T025/attempt-1/. Retry every required gate on attempt2.

## Final measured results and preservation

`evidence/runs/T025/attempt-2-20261105T041817977094Z.json`: lint, test-top and both
whitespace gates PASS/exit0. Lint31 checks/17 commands; test-top nine policy tests
and22 actual tool checks/13 commands. Both seeds passed481 vectors (962 total).
All three simulation negatives emitted their exact intended diagnostics, and the
wrong11ns clock run failed specifically BOARD_CLOCK_PERIOD. Positive Vivado pin/
clock/attribute/DRC inspection had zero warnings/errors. Current tool receipts:
lint-20261105T041818371384Z.json, top-20261105T042309463350Z.json.

`evidence/t025-final-audit-2026-11-04.json` binds two passing current tool receipts,
38 source hashes,80 artifact hashes and983 preserved earlier tracked files.
Original kit and21 of23 original baseline files remain byte-identical. Original
XPR and its generated project.wpc cache changed; before/after hashes and recovery
locations are in evidence/t025-original-files-update-2026-11-04.json. The cache
only added BatchMode counter3 while retaining GUI counter1. Original bytes remain
in the initial archive and new local before copies; the updated cache is also
backed up. Do not restore that generated cache over current work indiscriminately.
Configuration, simulator settings and run steps in XPR are unchanged; selected
files/top, documented serialization and run-description formatting account for its
diff. Both existing dated report prefixes and all earlier task evidence remain.

The full20-target regression was not run for this bounded board task; no CPU RTL
changed, and original required lint/test-top gates passed. T024's approved full19
regression remains its historical CPU evidence. The20-target registry is ready
for subsequent regressions. Unrelated installed board-catalog warnings remain
unresolved and all preparation FAIL records remain FAIL. They are not hidden by
the passing non-project selected-target result. No physical board is programmed.
