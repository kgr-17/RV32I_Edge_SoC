# T042 combined UART receive and MMIO verification

Prepared November6 from T027 commit0ddab70. All four task gates passed on attempt1.
Approved architecture/map/target/100MHz clock/reset priorities remain unchanged.

## Interfaces and sampling

rtl/peripherals/uart_mmio.sv is the combined UART frontend for later T031 SoC
integration. It accepts the unchanged32-bit original byte address,4-bit byte
enables, write flag and valid/ready transaction; its internal meaningful write
payload is10 bits(master wdata[9:0]), and held read response/error is32 bits.
Bits9:8 are CTRL W1C fields and bits7:0 serve TXDATA/CTRL. Reserved master bits
are ignored by an explicit adapter; no CPU bus/map width change. T031 must make
that adaptation. rx_i is asynchronous; tx_o idles high. uart_mmio_tx.sv preserves
the original8-bit TX frontend interface as a wrapper with RX tied idle and W1C
payload zero. Original TX tests and native corpus must replay unchanged.

uart_rx.sv takes clk_i/rst_i/enable_i/rx_i and emits a one-clock data_valid_o or
frame_error_o, data_o[7:0] held between valid bytes, and busy_o. Only rx_meta_q
samples the external line; rx_sync_q samples that first stage. Both carry
ASYNC_REG. All receive logic uses the second stage, with one100MHz clock and
counter enables. Divisor2..65536; production868, fast8 and odd7 only for DV.

After reset, disable or bad stop, wait for synchronized high before accepting
a new low start. Validate start at floor(D/2) cycles after detection; sample
data centers at floor(D/2)+(k+1)*D and stop at floor(D/2)+9*D. Data is LSB first.
A short false start is discarded without an error. Bad stop discards the byte,
emits one framing event and waits high, avoiding repeated events during a
continuous low break. Digital tests exercise input transitions0/1/2/3ns after
the falling clock edge; production tests also use860/876 sender clocks per bit.
These are finite sampling tests, not analog metastability/MTBF or physical baud
tolerance guarantees. Routed CDC/placement evidence remains laterT029/T043.

Disable aborts partial sampling and requires high rearming; a byte already
completed into the registered event still reaches the pending slot. The frontend
consumes a PHY event on the following clock edge. Existing pending bytes/errors
survive disable. Reset clears all slot/protocol/control/error state and restores
CTRL=3. Releasing reset in arbitrary payload can look like a fresh start on an
untagged UART stream; deterministic abort tests hold reset through sender idle.
No packet/framing reacquisition guarantee beyond the defined8N1 receiver is made.

## Register effects and collisions

| Address | Read | Write |
|---|---|---|
|0x10000000|0|selected low byte TX; busy stalls, disabled errors|
|0x10000004|bits0/1/2/3 TX_READY/RX_VALID/OVERRUN/FRAME_ERROR|error|
|0x10000008|pending byte or0|error|
|0x1000000c|bits1:0 TX/RX enables, reset3|low lane updates enables; lane1 bits8/9 W1C overrun/frame|

The slot stores one byte. Full+receive retains old byte and sets sticky overrun.
Bad stop never inserts a byte and sets sticky framing. A read captures the old
head and whether it was valid when the request was accepted. Only a successful
response acceptance for a selected-low-lane, originally-valid RXDATA read pops.
High-lane reads cannot pop; an originally-empty read cannot consume a byte that
arrives while its response waits. Response snapshots hold through all such events.

Pop+receive on the same edge replaces the consumed byte with the new byte without
new overrun. Receive into an unconsumed full slot sets overrun, including during a
stalled low-lane read. New overrun/framing events win simultaneous W1C. Each W1C
field respects its actual byte enable and acts only at response acceptance, as
do TX launches, CTRL updates and RX pops. New CTRL applies to later receiver
sampling; an already-completed byte survives same-edge disable. Reset wins all.
One outstanding request, registered response and no consume-edge replacement
remain unchanged. Malformed natural masks/unaligned lane choices, unallocated
words and read-only writes error with no transaction effect. LSU extracts lanes
from aligned32-bit responses; CPU alignment checking remains upstream.

## Independent checks and retained limitations

dv/unit/test_uart_rx.py uses absolute timestamp sample deadlines and a two-sample
input history, distinct from the RTL countdown/state implementation. A separate
transaction model tracks response snapshots and slot/error effects. Six policy
tests check a manually calculated0xa5 frame/two-stage delay, one-error break,
consume/clear collision priority, empty-read snapshot, replay/all256 bytes,
production/odd divisor cases and legal held requests. Native SV checks pre/post
public MMIO/TX and direct receiver outputs, plus master hold invariants.

The required driver runs seeds1/20261106 at8/7/868, checks every counted row and
saves vectors, summary, argument files, Tcl and WDB hashes. Directed cases cover
all256 payloads at8, short false start, bad stop/break recovery, overrun retention,
high lanes, snapshots across receive, empty-read/later-byte collision, pop+receive,
both new-error/W1C collisions, partial W1C, enable/disable, read-only/unmapped/
malformed access errors, reset during start/all data/stop and seeded full duplex.
Actual wrong-byte/empty/truncated negatives validate diagnostics. Isolated RTL
mutations remove pop replacement or give W1C priority; actual XSim must reject
each at a visible collision. Actual synthesis inspects the two ASYNC_REG cells,
single first-stage fanout to second-stage D and their common clock. This is
specific structural evidence, not a complete CDC signoff.

Preparation failure source archive is retained under
evidence/failed_sources/T042/reference-preparation/. Its failed assumption was
that a one-edge reset released inside payload prevents later apparent starts.
The test now holds reset through idle; no RTL exception/check suppression.
Before final task success, inspect all native receipts and exact current hashes.

```powershell
python -B dv/unit/test_uart_rx.py
python -B scripts/harness.py finish T042 --evidence evidence/daily/T042.md
```

T042 gates are lint, test-uart-rx(including full prior TX replay), and both
whitespace checks. Registry retains all22 predecessors, now23 targets. No full23
regression, compiled SoC/firmware execution, interrupts, formal(T023 skipped/NOT
RUN), routed timing/power, physical FPGA or ASIC result is asserted here.

## Final measured evidence

evidence/runs/T042/attempt-1-20261106T215848954626Z.json passed all gates. Native profile checks/commands: {"lint": [37, 20], "uart": [34, 14], "uart-rx": [66, 24]}.
Audit counts: {"tools": 3, "sources": 46, "artifacts": 138, "preserved": 1094, "rx_edge_rows": 752306, "tx_replayed_rows": 247940}.

| Divider | Seed | Edge rows | Requests | Responses | Errors | Reset-canceled |
|---|---:|---:|---:|---:|---:|---:|
|8|1|27900|371|370|5|1|
|8|20261106|27907|369|368|5|1|
|7|1|3133|58|57|5|1|
|7|20261106|3135|58|57|5|1|
|868|1|345115|61|60|5|1|
|868|20261106|345116|60|59|5|1|

RX total752306 rows plus247940 unchanged TX replay,1000246 total. All current
source/artifact hashes and1094 preserved old files are bound in the final audit.
Read earlier preparation sections as chronology, not pending final results.
