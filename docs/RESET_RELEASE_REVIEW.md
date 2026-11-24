# T032 board reset-release qualification proposal

Prepared 2026-11-21. **PROPOSED, not approved or implemented.** Current physical
UART acceptance remains FAIL; T032 is active with zero finish attempts. This
proposal does not authorize programming a new image or waive an acceptance gate.

## Observed problem and diagnostic limits

The approved image was programmed successfully. The owner confirmed holding
BTNC, releasing it once, leaving buttons untouched, and previously observing
DONE lit. The 60-second capture `capture-20261122T021244489932Z.json` contains
one burst: `ff 49 f2` followed by exactly `IRQ PASS\r\n`. Those three extra bytes
fail the original full-capture oracle. The earlier passive 30-second check was
silent. Earlier multi-message captures included additional presses explicitly
confirmed by the owner; those are not evidence of spontaneous core restarts.

The new deterministic simulation runs the unchanged canonical top, actual IRQ
ROM, 100 MHz clock and UART divisor 868. The existing strict serial decoder
accepts an ideal button release, rejects a representative reset-chatter stimulus
with `SOC_UART_FRAMING`, and accepts the full final message after the simulated
reset stabilizes. Receipt:
`evidence/toolchain_runs/reset-uart-diagnostic-20261122T021545951186Z.json`.
The physical switch waveform has not been measured. Reset chatter is a plausible
mechanism, not a confirmed sole cause or a promise that this proposal will fix it.

The first diagnostic execution remains FAIL: XSim returned nonzero after its
completion marker. The second full execution, with identical sources and checks,
passed. No process-exit or UART check was bypassed; root cause of that native
exit remains unknown, consistent with earlier retained XSim failures.

## Concrete proposed behavior

Keep the existing two clocked ASYNC_REG button synchronizer stages, 36 board
ports, pin assignments, 100 MHz clock, core synchronous reset, reset priority,
warm RAM policy and UART/ISA/interrupt behavior.

Only the canonical board reset distribution changes: require **2,000,000
consecutive synchronized low button samples (20 ms at 100 MHz)** before releasing
reset. A synchronized high sample asserts/keeps reset and clears the release
counter. Reset remains initialized asserted. The generic `reset_sync` defaults
and standalone unit interfaces remain unchanged.

The counter needs 21 explicit bits. Its compare constant is 1,999,999; the final
low sample releases the reset FF. It saturates after release. Any sampled high
restarts qualification, including during the quiet interval. Assertion still
uses the current synchronizer/distribution latency; the documented four-edge
minimum button hold remains. No generated clock, broad exception or asynchronous
core reset is introduced. Firmware boot starts about 20 ms after stable release.

Conceptual transition, not committed RTL:

```text
startup: reset=1, low_count=0
at each sys_clk edge:
    synchronized_button_high -> reset=1, low_count=0
    otherwise, count below 1,999,999 -> reset=1, low_count=count+1
    otherwise -> reset=0, keep count saturated
```

This qualifies release only. It is not a general switch debouncer, an analog
metastability proof or protection against every long noise pulse. A high pulse
that reaches the synchronizer may assert reset. The existing capture procedure
still begins while reset is held, then uses one release and no further presses.

## Implementation and validation scope requested

After explicit owner approval, implement the board qualification and independent
cycle/history tests under active T032. Test startup, exact release count,
short low windows, repeated chatter, a high during qualification, reassertion
after release, clocked transitions, and generic-default compatibility. Use
replayable seeds for new randomized RTL tests and real faulty variants for
off-by-one or omitted-requalification cases.

Exercise both actual production timing and shortened test parameters without
mislabeling the latter as the production implementation. Existing board boot
watchdogs currently cover a few milliseconds; extend their stated cycle/time
bounds for the reviewed 20 ms latency while retaining the same boot, serial,
retirement, memory and fault oracles. Keep native tool caps at 120 seconds,
registered composite caps at most 600 seconds and the three-finish-attempt rule.

Run fresh RTL lint, interrupt/legacy integration and regression, then full fresh
Vivado synthesis, bounded checkpoint stages, setup/hold/DRC/route/CDC/power
parsing and conditional bitstream generation. Existing T043 evidence is for the
old image and must remain intact. New T032 reports, jobs, manifest and image
must have separate paths and full current-source/predecessor bindings. Keep
XPR source integration reproducible; preserve every original source/constraint.

The FPGA launcher currently requires active authorized T043. Extend that workflow
only through a task-specific hashed owner review receipt for this T032 revision,
with explicit local-build scope, current-attempt gate checks and separate output
manifest. Do not fake active T043, reset its approval, reuse old checkpoints or
disable its existing protections. Document all new registered T032 gates; retain
the existing required lint, test-soc and physical-evidence checks.

The added counter can alter placement and marginal timing. No fit or timing
number is claimed before a new actual implementation; the old image has only
+0.123 ns setup and +0.013 ns hold margin. A local build failure stays FAIL.

## Approval boundary

The requested approval covers this reset-release contract change, its RTL/tests,
required workflow support, and fresh **local** verification/FPGA implementation.
It does **not** authorize writing a new bitstream to the board. After the new
image passes its gates, present its exact hash and evidence for separate physical
programming approval. The existing T032 programming authority covers only the
old approved image.

After any separately authorized new programming, repeat the original two clean
reset captures with no unexpected bytes or serial errors, preserve raw data and
truthful owner observations, then request final T032 review. Do not filter the
three bytes, accept only a suffix, suppress errors or label simulation as hardware
PASS. If qualification does not remove the physical symptom, preserve that failure
and continue diagnosis rather than weakening the oracle.

Formal T023 remains owner-skipped / NOT RUN. ASIC is NOT RUN. T032 and the whole
project remain incomplete.
