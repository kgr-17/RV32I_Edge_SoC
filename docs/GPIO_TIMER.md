# T028 GPIO and timer MMIO

Prepared November6 from T042 commitd71d900. All four task gates passed on attempt1.
Approved addresses, CPU bus,100MHz clock, reset priorities and target unchanged.
These peripherals have separate unit bus channels; SoC fabric/wiring is T031.

## GPIO

rtl/peripherals/gpio.sv takes clk_i/rst_i, raw16-bit switches_i and emits16-bit
leds_o. input_sync.sv supplies two ASYNC_REG stages per bit and synchronous
zero reset. Bits are independent level samples, not an atomic multibit transfer,
pulse catcher or mechanical debounce. Switch changes are asynchronous to the
clock in native DV; software reads a held snapshot of the second-stage vector.
Actual reset-release and full CDC analysis remain mandatoryT029; creating this
GPIO helper does not complete that task or establish analog MTBF.

The unit request interface has valid/ready, full32-bit original byte address,
write flag,4-bit natural byte enables and meaningful16-bit write payload selected
explicitly from master wdata[15:0]. CPU/master stays32-bit. Read response is32-bit
aligned data/error, valid held until ready. One outstanding request, registered
response, no consume-edge replacement. Effects occur once at successful response
acceptance. Reset gates bus acceptance and clears protocol/LED/synchronizer state.

| Address | Read | Write |
|---|---|---|
|0x10000020 OUT|LED bits15:0, reserved0|replace selected lower-two byte lanes|
|0x10000024 IN|synchronized switch bits15:0|error|
|0x10000028 SET|0|selected one bits set LED latch|
|0x1000002c CLEAR|0|selected one bits clear LED latch|

Upper two lanes of writable GPIO registers have no effect. Reserved bits read0;
SET/CLEAR are idempotent, not toggles. Unallocated/aliased full addresses and
malformed natural lane masks error without transaction effects. Read snapshots
hold while switches change. T031 must use the explicit low16 adapter and connect
raw switches here, without adding a second undocumented synchronization latency.

## Timer

rtl/peripherals/timer.sv has the same unit handshake/address/read interface,
meaningful full32-bit write payload and4BE; no external input or interrupt output.
All state is clocked at clk_i. There is no generated/fabric clock.

| Address | Register | Behavior |
|---|---|---|
|0x10000100|COUNT|32-bit read/write, reset0|
|0x10000104|COMPARE|32-bit read/write, reset0|
|0x10000108|CTRL|bit0 enable/bit1 auto-reload, reset0; other bits read0/ignore|
|0x1000010c|STATUS|bit0 sticky match, reset0; selected bit0 W1C|

With old enable set, count increments every edge modulo2^32 regardless of bus
stalls or pending responses. A match compares incremented count to old compare.
Old auto-reload resets count0 on match; otherwise normal wrap. Compare0 does
not immediately match upon enabling count0: the next increment is1; matching0
requires wrap. Auto-reload compare1 can match on every enabled edge.

A successful COUNT write suppresses increment AND new match on that edge;
selected bytes merge with the pre-increment count. It does not clear an already
sticky status bit. COMPARE/CTRL writes take effect for later counting; that edge
still uses old compare/control. A disabled CTRL write cannot erase a real old-
enable match. Match wins over simultaneous status W1C. Only selected low byte can
clear bit0 or change CTRL; higher lanes ignore. All writes occur at successful
response acceptance; COUNT reads snapshot when their request is accepted. Timer
events continue during unrelated errors/response stalls. Reset wins and clears
all timer/protocol/configuration state. No interrupt capability is claimed; its
separate architecture/implementation reviews remain T044/T045.

## Independent DV and retained preparation failures

dv/integration/test_mmio.py represents GPIO outputs as a set of bit indices and
the timer as elapsed-cycle formulas from configuration epochs. The latter uses
distance-to-compare and periodic wrap/auto-reload arithmetic rather than copying
the RTL increment/count state machine. A separate pending transaction queue
captures read snapshots and delays effects until response consumption.

Five pure tests check manually calculated wrap/auto/compare0 values, byte merge,
two-stage input snapshot, effect timing, replay, priority witnesses and producer
stability. Native tb_mmio.sv drives two independent channels, input switches2ns
after falling clock, compares pre/post public bus/LED outputs every row, and
checks both held request producers. Seeds1/20261106 each include all16 LED bits,
idempotent SET/CLEAR, all seven legal lane choices, malformed masks, upper-lane
ignores, RO/unmapped/address-alias errors, long input/counter response snapshots,
32-bit rollover, auto-reload, W1C/match, COUNT/match, old compare/control semantics,
pre-increment partial merge, shared reset cancellation, no replacement and4096
random parallel transaction edges plus bounded drain.

Actual wrong-LED/empty/truncated controls must emit exact diagnostics, never a
timeout or unrelated launch failure. Three isolated RTL mutations challenge SET
idempotence, match-over-W1C priority and COUNT-write match suppression. Original
production sources stay unchanged during those negative runs.

Retained reference-preparation failure: high-byte COUNT fixture used mask8 with
base address, correctly rejected; fixed original byte offset to+3. Archived5
input files. First native preparation passed both main corpora and three input
negatives and detected SET mutation, but clear-priority mutant escaped: compare1
auto-reload reasserted flag before another status read. Archived12 inputs/117
generated hashes and full receipt. Add immediate status read plus a single-match
W1C collision so that bad flag is visible. No RTL fix/check waiver; failed fault
detection remains FAIL. Fresh full task gates must exercise the stronger corpus.

```powershell
python -B dv/integration/test_mmio.py
python -B scripts/harness.py finish T028 --evidence evidence/daily/T028.md
```

Registry24 targets retain all23 predecessors. No full24 regression, completeCDC,
formal(T023 skipped/NOT RUN), SoC/compiled firmware, IRQ, routed timing/power,
physical board or ASIC signoff follows from these standalone checks.

## Final measured results

evidence/runs/T028/attempt-1-20261106T221630943647Z.json passed all four gates, exit0.
Native checks/commands: {"lint": [41, 22], "mmio": [46, 20]}. Audit: {"tools": 2, "sources": 45, "artifacts": 100, "preserved": 1119, "edge_rows": 9295}.

| Seed | Edge rows | GPIO requests/responses/errors/canceled | Timer requests/responses/errors/canceled | COUNT/match collisions | Match/W1C collisions |
|---|---:|---|---|---:|---:|
|1|4648|1851/1850/481/1|1797/1796/361/1|1|2|
|20261106|4647|1837/1836/516/1|1805/1804/358/1|1|2|

All1119 preserved historical tracked files, current source/artifact bindings and
failed archives are verified in evidence/t028-final-audit-2026-11-06.json. Earlier
preparation sections are chronology; final results above are the fresh task gates.
