# T006 register file and owner review

Status: automated acceptance PASS on attempt 2; awaiting owner review.
No agent may self-approve this gate or begin T007 before review completes.

The module `regfile` implements the approved v0.2 register interface internally:

| Port | Width | Behavior |
|---|---:|---|
| clk_i / rst_i | 1 each | Rising clock; active-high synchronous state reset. |
| write_en_i | 1 | A valid retiring write enable supplied by the caller. |
| write_addr_i / write_data_i | 5 / 32 | x1..x31 may be written; x0 writes are discarded. |
| read_addr_a_i / read_addr_b_i | 5 each | Independent combinational read addresses. |
| read_data_a_o / read_data_b_o | 32 each | Zero, current nonzero write bypass, then stored value. |

x0 has no storage element. x1..x31 clear to zero on a rising reset edge.
Reset has priority over write enable; disabled writes preserve state. Both read
outputs are masked to zero while reset is high, an internal defined behavior
while the core is reset. A reset pulse without a rising clock edge masks outputs
temporarily and must not erase storage. No initial/power-on register value is
assumed before a reset edge. No fabric clock or asynchronous state reset exists.

For each nonzero read address, if write_en is high and its address matches,
return write_data before the upcoming edge; both ports may bypass together.
After the edge the same value is stored. The caller gates write_en with valid
WB/retirement control; this module cannot decide instruction validity or age.
Long-stall operand capture/reread and pipeline forwarding remain later tasks.
No architecture, ISA, reset priority or clock-domain revision was introduced.

The implementation uses 31 `rv32_regfile_word` instances and two
`rv32_regfile_read` instances. This explicit hierarchy partitions storage and
read cones for synthesis; it adds no clock or architectural state. The first
flat-array version passed functional DV but failed strict lint because Vivado
Netlist 29-101 warned about the large primitive-only register-file cellview.
That complete failed receipt is retained. The repair changes RTL hierarchy,
not warning severity, filters, check coverage, Tcl or synthesis hierarchy flags.
The exact first source is retained at evidence/failed_sources/T006/attempt-1/
regfile.sv, SHA-256 d1b753957a9881e977ee96fc21be4d8756c6ef33c93082a75ae1c1c7995234c8.
It is historical evidence, outside the active manifest. Background:
[AMD UG901 hierarchy controls](https://docs.amd.com/r/2025.1-English/ug901-vivado-synthesis/KEEP_HIERARCHY).

## Independent verification

`dv/unit/test_regfile.py` derives data by searching the history of enabled writes
back to the newest reset. It does not reproduce the RTL array update algorithm.
It rejects uninitialized nonzero reads rather than assuming zero. Six fixed
oracle tests anchor reset/write priority, x0, newest write, pre-edge bypass,
warm reset and undefined startup. Seeds are 1/20261025.

Directed vectors cover every read-port address pair, each write/read collision,
both-port bypass, attempted x0 writes, disabled writes, repeated reset,
walking bits/complements in every stored word and post-reset scans. Thirty-one
between-edge reset pulses verify synchronous state retention. Another 4,096
random cycles mix reset, writes, x0 and source collisions. Defined hit bins cover
every source address plus reset/bypass/hold/x0 behavior; these are not formal
proof or code coverage percentages.

`tb_regfile.sv` checks both ports before the rising edge, then disables bypass
after the edge and checks actual stored data. Pulse rows also check zero while
reset is asserted and restored data after deassertion before the clock edge.
All comparisons use case inequality. The generic unit driver enforces versions,
coverage, exact seed/count completion, clean diagnostics, waveform/source hashes
and actual wrong-answer/empty-file failure rejection.

Lint synthesizes `dv/lint/regfile_lint_top.sv`, which exposes both read cones
through a selected 32-bit output. This is an internal-unit synthesis probe with
independently controlled addresses and output select, not a board top. Functional
DV instantiates the full register file directly and checks both ports together.
The existing latch/black-box/LUTLP-1/MDRV-1 checks are unchanged. Synthesis is not
implementation or timing closure.

T006 acceptance requires lint, test-regfile and the newly strengthened composite
regress gate. The latter executes fixture, decoder, ALU and register-file suites
together for the first unit-review boundary. Preserve all existing checks and
logs. Use `python -B scripts/harness.py finish T006 --evidence evidence/daily/T006.md`.
Individual unit rechecks in regression are labeled repetitions, not new unique
coverage. No T007 work is permitted until T006's owner review completes.

## Owner review checklist

Final receipt: evidence/runs/T006/attempt-2-20261026T041624015172Z.json.
All five gates passed: lint, test-regfile, full regress and both whitespace checks.
Register-file synthesis probe took 26.531 s with no warnings/errors, latches,
black boxes or selected structural violations. Each replay seed checked 10,369
clocked vectors, 20,738 total, including both pre/post-edge ports and 31 reset
pulses per seed. Full regression rechecked 543,428 vectors across all four
designs; see evidence/daily/T006.md for exact scope and repeated-test accounting.

- Confirm x0 is unwritable, including current writeback bypass.
- Confirm both read ports see a matching nonzero retiring write before its edge.
- Confirm synchronous reset priority and state retention across between-edge pulses.
- Inspect test evidence, actual synthesis scope, remaining pipeline integration gaps.

After automated acceptance, the owner may acknowledge review with
`python -B scripts/harness.py approve T006 --confirm-owner-review`.
The agent must not run this command on the owner's behalf.
Formal, CPU retirement/hazards, timing, hardware and ASIC are still separate work.
