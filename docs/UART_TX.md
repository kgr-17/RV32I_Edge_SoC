# T027 UART transmitter and sending-side MMIO

Completed November6 on attempt2 from clean a04e23a(T026). All four gates passed.
Approved ISA/map/reset priorities/100MHz clock/target remain unchanged.

T042 development note: uart_mmio_tx now preserves this exact interface as a
compatibility wrapper around canonical uart_mmio with RX tied idle. The canonical
frontend adds reception and meaningful CTRL bits9:8. Original T027 evidence below
is bound to its commit; T042 replays its unchanged vectors against the refactor.
See UART_RX.md for current implementation scope and pending task gates.

## Implemented interfaces and bit timing

rtl/peripherals/uart_tx.sv uses clk_i/rst_i/enable_i, data_valid_i/data_ready_o,
8-bit data_i, busy_o and tx_o. One clock only; all state changes on rising edges,
using enables rather than a fabric clock. Default CLKS_PER_BIT=868 at100MHz gives
115207.373baud,64.004ppm above target115200. The ten-bit frame is start0, eight
data bits LSB first, stop1; idle1. Each bit lasts exactly the configured number
of clock intervals. A held-valid producer can start the next frame one edge after
the previous frame finishes; no zero-gap acceptance promise is made.

Synchronous reset aborts traffic and returns idle. enable_i blocks new acceptance
while an active frame completes without pause or corruption. data_ready_o is
gated with reset and enable; accepted payload is captured. Valid divider range
is2..65536. Fast divider4 is a DV configuration; hardware target remains868.

rtl/peripherals/uart_mmio_tx.sv provides a byte-payload internal TX frontend:
valid/ready,32-bit original byte address,8-bit meaningful write payload, write
flag,4-bit byte enables and32-bit aligned read data/error. The CPU/master bus
stays32-bit; the explicit adapter selects wdata[7:0], since the sending-side
registers ignore higher payload bits. Native tests still drive full32-bit master
packets through that explicit selection. T031 must make the same connection; RX
W1C data bits are part of T042's frontend extension. One accepted unanswered request,
response registered after acceptance, no consume-edge replacement. Response
fields hold under backpressure. Read snapshots are captured when the response is
created, rather than following a changing TX status. Outputs/acceptance are gated
by reset and all protocol/control state resets synchronously.

## Register behavior in this milestone

| Aligned address | Read | Write |
|---|---|---|
|0x10000000 TXDATA|0|Enabled low-byte lane sends once; busy backpressures; disabled writes error|
|0x10000004 STATUS|bit0 TX_READY; RX status bits read0 until T042|error|
|0x10000008 RXDATA|0(empty; reception is T042)|error|
|0x1000000c CTRL|bits1:0, reset3|selected low byte updates RX_ENABLE/TX_ENABLE bits; reserved bits ignored|

Unallocated words and writes to read-only words return errors without effects.
Byte/halfword/word lanes must match the original byte offset; malformed masks
are rejected defensively(the conforming CPU LSU never sends them). Read data is
the full aligned word; the LSU performs byte extraction. Upper TXDATA lanes do
not transmit while enabled; a write to TXDATA while disabled errors even if the
low lane is not selected. High CTRL lanes leave enables unchanged. RX W1C bits
currently have no events/flags to clear. RX_ENABLE is stored/read but no receiver
is connected by T027. T042 must implement the receiver, pending slot, error flags,
consume/W1C collision behavior and its tests before SoC integration. This task
does not claim complete UART reception or substitute for that mandatory milestone.

A TX side effect occurs ONLY at successful response acceptance. Accepted TXDATA
payload waits while the response stalls; there is no early frame at request
acceptance. A busy selected-low-byte write remains unaccepted until ready; a
disabled write instead accepts and produces an error, avoiding deadlock. A
pending TX response cannot be overtaken by a control transaction. Disabling TX
during an already active frame lets it finish, as approved. Shared reset cancels
pending responses and the serializer, and restores CTRL=3. These are unit ports;
the XPR remains the board diagnostic shell until T031 wires the actual SoC.

## Independent verification

dv/unit/test_uart.py contains a timestamp-based serial reference, transaction
queue model and bounded master. Serial expectations select a bit by elapsed
cycles from acceptance, rather than copying the RTL shift register/count logic.
The MMIO model snapshots data and records side effects at response acceptance.
Nine unit tests challenge explicit0xa5 LSB order, frame/enable/reset behavior,
one-edge response/no replacement, delayed TX effect, lane/disabled errors, reset
cancellation, reproducibility/all256 completed payloads, divider bounds and peer
valid/payload stability until acceptance. Native SV also asserts both producers'
payload stability under backpressure, with reset as the cancellation exception.

Actual SV compares pre-edge AND post-edge public outputs of both the MMIO frontend
and a second direct serializer. The latter sees a legal held-valid producer,
payload changes after acceptance and disable during live traffic. Four positive
runs use seeds1/20261106 with divider4 and production868. Fast runs must complete
all256 payload values through both interfaces. Bus cases include response stalls
longer than a frame, busy request holds, status snapshots across frame finish,
CTRL disable during a frame, selected lanes, invalid/RO/unmapped accesses,
reset of pending/active/offered traffic, consume-edge replacement rejection and
seeded transactions. All prior CPU/board/memory checks remain registered.

Initial preparation before attempt1, retained as history:

| Divider | Seed | Clock-edge rows | Accepted requests | Responses | Error responses | Reset-canceled |
|---|---:|---:|---:|---:|---:|---:|
|4|1|11733|360|359|30|1|
|4|20261106|11944|360|359|24|1|
|868|1|112097|56|55|17|1|
|868|20261106|94718|56|55|20|1|

Initial total230492 rows. The strengthened producer below changes these counts;
each row still compares eight interface values on both sides of an edge.
The real XSim gate must execute every row with exact completion counts and save
WDB/vector/Tcl/argument/summary hashes. Actual wrong-expected, empty and truncated
vector runs must emit their specific diagnostics with no success marker; arbitrary
native failure or timeout cannot satisfy a negative. Generic synthesis lint adds
the default868 frontend/serializer and retains all older checks. Registry now22
regression targets, with21 predecessors retained; a full22-target run is not yet
claimed. Simulation does not establish physical UART baud tolerance, CDC, board
operation, routed timing/power or ASIC evidence.

```powershell
python -B dv/unit/test_uart.py
python -B scripts/harness.py finish T027 --evidence evidence/daily/T027.md
```

Required gates: lint, test-uart and both whitespace checks; at most3 attempts.
After pass, audit actual wave/vector/summary/source bindings and baseline
preservation, append the same two November6 reports, review/stage/commit locally,
then query the next dependency-ready task(T042 expected). Do not skip RX or infer
architecture/physical-programming authorization from this milestone.

## Retained first attempt and strengthened retry

Attempt1 `evidence/runs/T027/attempt-1-20261106T211642945623Z.json` reports
FAIL/PASS/PASS/PASS. Actual UART gate passed34 checks/14 commands, all230492 rows
and the three intended negatives. Direct peripheral synthesis nevertheless emitted
48 Synth8-7129 warnings for intentionally ignored write bits31:8. Strict warning
rejection remains unchanged. Archive128 inputs/2128 generated hashes under
evidence/failed_sources/T027/attempt-1/.

A wrapper around a full32-bit child input still produced those warnings; that
failed targeted preparation and its exact6 inputs are separately archived. The
current internal frontend now accepts the meaningful8-bit byte, with explicit
master32-to-byte adaptation, rather than inventing a hardware use for reserved
bits or suppressing warnings. dv/lint/uart_lint_top.sv selects a byte from its
full probe payload so every probe input has a meaningful role. The targeted
repair probe `uart-lint-repair-20261106T212657418951Z.json` is warning-free PASS;
it is not a substitute for the full task gates. Software-visible behavior, CPU
bus widths, addresses, masks, read snapshots and effect timing are unchanged.

Review also found the direct PHY producer withdrew an unaccepted final offer
when beginning its old drain. It now stops only after that offer handshakes,
then drains the last accepted frame. Add independent Python and native SV
producer-stability checks for both the PHY and MMIO master. These strengthen DV;
no RTL functional error was found and no functional/negative check was removed.
New expected rows:11775/11986 at divider4,120779/103400 at divider868, total247940.
Request/response/error/cancellation counts are unchanged. Fresh full attempt2
must run all gates and save new artifacts; previous successes are historical.

## Final measured results

Attempt2 `evidence/runs/T027/attempt-2-20261106T212832194283Z.json` passed
lint, test-uart and both whitespace gates, all exit0. Current lint receipt
`lint-20261106T212832569545Z.json` passed35 checks/19 native commands, including
all older lint tops and the default UART probe, with no warnings. Current UART
receipt `uart-20261106T213400777026Z.json` passed34 checks/14 commands plus the
separate nine Python reference tests. All247940 rows above executed in real SV;
actual wrong-expected/empty/truncated controls were detected as intended.

`evidence/t027-final-audit-2026-11-06.json` validates2 current tool receipts,
39 source bindings and85 distinct artifacts. Independent reconstruction checks
request/response holds, effect timing, producer stability, and all frame bits
from the checked native vectors:1148 complete frames,12 reset-aborted starts.
Both fast seeds complete all256 byte values through each interface. All1070
historical tracked files outside the five declared editable integration/report
files remain byte-identical. Earlier report prefixes, both failed source archives
and all2128 first-attempt generated hashes remain intact.

This establishes unit-level TX/MMIO simulation and generic synthesis/structural
checks. RX remains mandatoryT042; compiled SoC execution remainsT031. No full22-
target regression, formal proof, CDC signoff, routed timing, hardware operation,
power measurement or ASIC result is asserted. T023 remains owner-skipped/NOT RUN.
