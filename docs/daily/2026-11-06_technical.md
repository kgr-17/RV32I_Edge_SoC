<!-- entry:1c8cc6e1c9ace379688486563368f7f6c30d1e345684623f24912b2e58253470 -->

November6 resumed same activeT026 from latest November4 handoff and inspected uncommitted sources; HEAD1dd3dae T025, no user-work replacement. daily --supervised exit0 saved .tmp/2026-11-06-daily.txt; beginT026 RESUME preserves attempts2 and adds November6 participation, no reopen/reset. Actual attempt2 finished FAIL/PASS/PASS/PASS, evidence/runs/T026/attempt-2-20261105T045329256744Z.json. Mapping repair succeeded: firmware-20261105T050000850238Z.json PASS44checks/27commands,66250 RTL memory vectors, compiled-image/ISS/overflow/negative controls, warning-free actual16ROM+16RAM inference. Generic lint failed only on unchanged register_fixture: zero-warning/error synthesis/DRC and exactmarker, then EXCEPTION_ACCESS_VIOLATION nativeexit4294967295. Strict failure retained, native rootcauseunknown; crashtext says no stack trace. Archived120 current inputs/2284 generated hashes+text crash under evidence/failed_sources/T026/attempt-2/. All current firmware source hashes matched passing attempt2 before retry. evidence/prepare/T026-gate-evidence-2026-11-06.json preserves exact preattempt1/2 texts and receipt hashes. No RTL/check/seed/timeout/budget changes for final attempt3; rerun every required gate, never substitute earlier partialpasses. If third fails, taskblocks and owner-specific reopen required; do not self-reopen. Prior November4 reports preserved, create exactlytwo November6reports. Runtime remains danger-full-access/never, harness is not sandbox; attendedonly, no scheduling/install/download/globalPATH/push/FPGA programming. Read required AGENTS/boundary/ARCH/verification/backlog/state/loop context. On actual pass audit current/source/tool/artifact/preservation hashes and historical archives, append todayreports, locallycommit inspected task files, thenquerynext expectedT027. No compiled RTL CPU/SoC/formal/routedtiming/hardware/ASIC claim; T023 still skipped/NOT RUN, T024 owner approval9fe0855 retained.


---

<!-- entry:145b32cbca728f009d4f71978bea6196ae40bc4e1ee15a56d8104c4c50b830e2 -->

T026 completed on November6. Final receipt: evidence/runs/T026/attempt-3-20261106T205251043860Z.json; all four required gates PASS, exit0. Lint passed33 checks/18 commands, including the unchanged fixture and intended latch rejection. test-firmware passed17 acceptance-policy tests,7 independent ELF/memory tests and44 actual tool checks/27 commands. Current tool receipts are lint-20261106T205251466810Z.json and firmware-20261106T205810599677Z.json.

Each seed(1,20261104) passed33125 primitive-memory vectors,66250 total. Audit read the actual artifacts and confirmed all16384 enabled addresses on each ROM port and RAM, all16 masks and12 reset edges per seed. Both actual memory negatives, compiled-image corruption controls and real ROM/RAM linker overflow controls passed. Four independent compiled-image model boots each retire72 instructions with correct data/BSS/stack/signature/ECALL. Real synthesized banks contain16ROM+16RAM RAMB36E1 cells with zero warnings/errors and clean structural DRC. These are model/primitive RTL/standalone synthesis results; actual compiled CPU/SoC execution, local-bus adapter, full21-target regression, complete CDC, routed timing, hardware, formal and ASIC are not claimed.

Final audit evidence/t026-final-audit-2026-11-06.json binds2 current receipts,46 sources,92 distinct artifacts and1017 preserved tracked files. It validates120-input archives for each failed attempt,2124/2284 generated hashes, the9-source initial preparation archive, compiler components and all3 original pre-gate evidence texts. Exact crash text is preserved as .txt plus hashed receipt; native crash rootcause remains undetermined. Only RAM mapping attribute changed between attempts1/2, no source/check/seed/timeout change between2/3; all original failures remain FAIL. November4 reports remained unchanged during November6 recovery. ARCH hash403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03 and CPU/XPR/kit are unchanged byT026.

Progress26/41 mandatory completed plus1 owner-skipped(T023 NOT RUN), no active task; T024 explicit approval9fe0855 remains. Review/stage only inspected T026 files, verify46 indexed source hashes and both whitespace checks, commit locally. Then query actual next(expectedT027 UART TX/MMIO), begin from clean Git and continue one active task at a time. No owner approval command is needed or generated forT026. Next session must read this latest handoff plus all required contract files, daily --supervised and Git status, and recover actual state. Tool versions remain Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465; software GCC13.4.0 actualtargetriscv32-xilinx-elf, ld2.43.1.20241111, objcopy/readelf/objdump2.39.0.20220819. Runtime unrestricted/never, attended only; no installs/downloads/global PATH/push/scheduling/FPGA programming. Exactly the November6 report pair is appended today.


---

<!-- entry:d7bb870f71511e8149a268a122d7d51f6f61e16cd9e2e4debc81cd47c273ccda -->

T026 saved in clean local commit a04e23a5cef5712807ffb6e86ff45602b8007777 after all4 gates and final audit passed. Raw crash bytes retained in crash-report.zip; readable .txt is canonicalLF so existing staged-whitespace rules remain unchanged. Current-source/index46 hashes matched. Queried actual next and began sole activeT027 from clean Git; no verification attempts yet. Existing rtl/peripherals and UART tests absent. Baseline evidence/prepare/T027-baseline-2026-11-06.json preserves current tracked source hashes.

T027 implements UART TX plus bounded TX-side MMIO frontend under the already-reviewed v0.2 contract: single100MHz clock,868cycles/bit near115200baud,8N1/LSB-first/idlehigh, complete active frame if disabled, no new transmit unless enabled, synchronous reset. Local one-outstanding bus, registered response/no consume-edge replacement, stable stalled read snapshots; TX side effect only at successful response acceptance, busy backpressures low-byte writes, disabled TXDATA writes return error. Natural byte-lane accesses/partial CTRL writes/reserved bits/unallocated or RO write errors follow approved map. RX deserializer/slots/error flags remain requiredT042 next; no RX or SoC completion claim. XPR stays diagnostic shell, no ISA/map/reset/clock/target changes.

Implement explicit-width uart_tx.sv and uart_mmio_tx.sv, independent history-based serial/transaction model and actual XSim pre/post-edge waveform comparisons. Test fast divider for all256 bytes and real868 divider, response stalls/held requests, status snapshots, disabled/busy/partial writes, reset pending/active traffic, invalid accesses and replay seeds. Add actual wrong-expected/empty/truncated negatives and synthesis lint/registry entries without removing earlier checks. Review ambiguous behavior against ARCH_SPEC before changing software-visible semantics. Prepare docs/evidence and append exactlytheexisting November6 report pair before finishT027, maximum3 attempts; inspect/hash/commit after pass thenquery nextT042. Runtime unrestricted/never attendedonly; no download/install/globalPATH/push/scheduler/programming.


---

<!-- entry:197020f7fd89a2e96fc5d2b39efea629b02a8d9649b7ed60baa7318edbc646ca -->

T027 RTL/reference/DV prepared. uart_tx uses one100MHz clock, divider868(default)/8N1/LSBfirst/idlehigh, enable-gated new starts and complete active frames on disable. uart_mmio_tx implements full-byte-address natural-lane decoding for reviewed TXDATA/STATUS/RXDATA(empty)/CTRL, one-outstanding registered/stable response/no consume-edge replacement, TX start only at successful response handshake, busy selected-low write backpressure and disabled-write error. RX receiver/slots/flags remain mandatoryT042; no map/ISA/reset/clock/target or XPR change.

Eight independent reference tests PASS. Timestamp/queue model uses elapsed-time bit selection and transaction snapshots; no RTL decoder/shift-state imports. Actual SV pre/post public comparisons cover both MMIO and directPHY. Prepared four corpora at divider4/868, seeds1/20261106,11733/11944/112097/94718 rows(total230492), fastall256completebytes bothinterfaces. Includes long response stalls/no early effects, busy heldrequests/status snapshots, CTRL/lanes/reserved/RO/unmapped errors, reset pending/active/offered traffic and no replacement. Actual native gate stillpending; wrong-expected/empty/truncated negatives must be executed with exact diagnostics. New UART synthesis/default868 lint and test-uart registry retain21 earlier regression targets(now22); no full22 regression claim.

Next finishT027 --evidence evidence/daily/T027.md attempt1/3, every required gate; preserve failure/inputarchive before repair. On pass audit current sources, real vectors/waves/summaries, historical1075baselinefiles, append sameNovember6two reports, inspect/stage/localcommit thenquery actualnext expectedT042. T026 completea04e23a, formalT023stillowner-skipped/NOT RUN, T024approval9fe0855 retained. Versions Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Runtime unrestricted/never attendedonly. No install/download/globalconfig/push/schedule/physicalFPGA; no formal/RX/SoC/CDC/routedtiming/hardware/ASIC proof.


---

<!-- entry:a4c35a9c10708736dfb316edaad6abeafd29dd5d5d903b3aaafd220785f13db2 -->

T027 attempt1 retained FAIL/PASS/PASS/PASS, evidence/runs/T027/attempt-1-20261106T211642945623Z.json. Native UART gate PASS34checks/14commands,230492 pre/post rows and3 intended negatives. Strict lint rejects48 Synth8-7129 warnings because sending-side registers intentionally ignore master write bits31:8. Archived128 inputs/2128 generated hashes. A constant-driven wrapper around a full32-bit child still warned; its6 exact sources/failed receipt archived separately. Current frontend instead has a natural8-bit internal TX payload, explicit master32-bit wdata[7:0] adaptation with original32-bit addresses/4BE/32-bit reads. No CPU bus or software-visible semantics change, dummy load, diagnostic filter or warning waiver. Targeted adapter lint PASS warning-free uart-lint-repair-20261106T212657418951Z; only preparation, not taskpass.

Review identified old direct-PHY drain withdrawing an unaccepted final valid. Generator now stops after the next actual acceptance then drains its frame. Added independent Python and native SV producer-hold assertions for PHY/master, reset cancellation only. Nine unit tests PASS. Fresh expected rows11775/11986/120779/103400,total247940; request/response/error/cancel counts unchanged. New cases/negative tests retained, no existing timeout/attempt budget changed. Full finishT027 attempt2/3 next, rerun every mandatorygate; actual functional/RTL results pending on updated source. Source serializer logic unchanged, RX/frontend W1C extension remainsT042 and actualSoC hookupT031. No ARCH/map/ISA/clock/target/XPR change. Append sameNovember6two reports, no installs/downloads/globalconfig/push/scheduling/programming.


---

<!-- entry:1dbf7d30b8af90fd19895c439933bd6585f47f22d60ddef03da6b56c27a1b67b -->

## T027 completed: UART transmitter and sending-side MMIO

T026 was committed as a04e23a5cef5712807ffb6e86ff45602b8007777. T027 attempt2
passed all four gates, exit0: lint, test-uart, git diff --check and cached check.
Receipt evidence/runs/T027/attempt-2-20261106T212832194283Z.json. Native lint35
checks/19 commands; UART34 checks/14 commands and9 separate reference tests.
Current receipts lint-20261106T212832569545Z and uart-20261106T213400777026Z
under evidence/toolchain_runs/. Actual seeds1/20261106, divisors4/868 checked
11775/11986/120779/103400 edge rows, total247940, plus three actual negative
controls(wrong expectation, empty, truncated), with precise diagnostics.

Interfaces: uart_tx has valid/ready byte, enable/busy and8N1 TX output, default868
100MHz cycles per bit, reset abort/idle-high. uart_mmio_tx accepts full32 original
byte address, write flag,8-bit meaningful payload adapted from master wdata[7:0],
4-bitBE and held32-bit read/error response. Master remains32-bit. Response effects
occur only at successful response acceptance; one outstanding/no same-edge
replacement, busy backpressure, CTRL reset3, exact approved map. RX is NOT yet
implemented. T042 must add receiver/pending/error/collision behavior, and T031
must connect the real SoC including explicit payload adaptation.

Modified production files rtl/peripherals/uart_tx.sv,uart_mmio_tx.sv; new
dv/lint/uart_lint_top.sv,dv/unit/test_uart.py,tb_uart.sv,scripts/uart_checks.py,
docs/UART_TX.md; registry config/rtl_checks.json,.harness/checks.json; state/backlog,
README, evidence and these same-day report appendices. No CPU/XPR/XDC/ISA/map/
clock/reset-priority/init-image change. Existing21 regression targets retained,
test-uart makes22; full22 regression NOT RUN in this bounded task.

Audit evidence/t027-final-audit-2026-11-06.json binds2 current tool receipts,
39 sources/85 artifacts, reconstructs1148 completed frames and12 reset-aborted
starts from the checked vectors, validates actual producer holds/effect timing,
all256 byte values on fast runs,1070 preserved historical files and retained
report prefixes. Pre-verification evidence snapshots are under evidence/prepare/.
First failed lint warnings remain FAIL;128-input source archive/2128 generated
hashes and6-input failed targeted wrapper archive remain intact. Current targeted
natural-byte probe PASS is separately bound. No warning waiver/check weakening.

Reproduce: python -B dv/unit/test_uart.py; python -B scripts/verify.py test-uart;
python -B scripts/verify.py lint. All commands above ran successfully in attempt2.
Versions remain Python3.9.13,Git2.48.1.windows.1,tzdata2026.2,Vivado/XSim2025.2
SW6299465. Review diff/whitespace and staged hashes, commit inspected T027 files
locally, then run harness next and begin the actual next ready task(T042 expected).
Read this handoff and required contract/context before a future session; recover
state.active before selecting another task.27 mandatory completed plus1 skipped
of41. T023 is still owner-skipped/formal NOT RUN, never PASS. No RX/CDC/routed
timing/hardware/ASIC signoff. Runtime unrestricted/never, attended only; no host
scheduling, tool installation/global changes/downloads/push/FPGA programming.


---

<!-- entry:445a0e6cacfadefce955c5230c8c2e6f9884a4f7fd7ad769e9b080158742a57c -->

## T042 prepared: synchronized UART receiver and combined frontend

T027 committed0ddab70, Git clean before beginT042. Baseline1102 tracked hashes
excluding state/backlog; declared existing changes cover frontend wrapper/shared
TX driver/registries/docs/report pair. Canonical uart_mmio.sv adds meaningful
master wdata[9:0] adapter, unchanged32-bit address/read response and4BE. Old
uart_mmio_tx8-bit interface wraps canonical UART with RX high/W1C0; actual oldTX
corpus replay is required inside the RXgate. No architecture/map/CPU/XPR/XDC/
clock/resetpriority/firmware image change. T042 does not need owner review.

uart_rx.sv uses two ASYNC_REG stages and absolute center timing8N1 at default868.
Disable aborts partial sampling; existing completed event and slot remain. One
slot; overrun retains old, bad stop discards, error events beat W1C, selected-low
successful originally-valid read pops, empty snapshot cannot consume future byte.
Simultaneous old-pop/new-receive retains new. CTRL masks honor lowlane enable and
lane1 bits8/9 W1C. Reset clears slot/errors/protocol/CTRL3. Full spec UART_RX.md.

Six independent timestamp/history model tests PASS. Reference-preparation failure
is archived: releasing a one-cycle reset inside ongoing payload can create a fresh
apparent start. Deterministic abort tests hold reset until idle; no RTL/check
relaxation. Actual native preparation uart-rx-20261106T215650293874Z PASS66checks/
24commands: six positive seeds1/20261106 at8/7/868, all256 bytes fast, four phase
offsets, production sender860/876 skew, three precise wrong-byte/empty/truncated
negatives, two actual isolated pop/clear-priority RTL mutation detections, and
actual synthesized2ASYNC_REG/firstfanout1/commonclock inspection. This is
preparation, not taskPASS; fresh finish runs every required gate. Registry23
retains22 predecessors. Test-uart native replay also executed separately; current
full gate will bind its result. All logs remain project-local.

Next python -B scripts/harness.py finish T042 --evidence evidence/daily/T042.md,
attempt1/3. On pass independently audit actual checked files/effects/frames/source
bindings, preserve historical bytes/report prefixes, append existing Nov6 report
pair, review/stage/whitespace/commit thenquery next(expectedT028). If failure,
archive exact sources/artifacts before correction; never weaken checks or self-
reopen. Versions Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2
SW6299465. Runtime unrestricted/never, attendedonly; no downloads/install/global
settings/push/scheduler/programming. FormalT023 remains skipped/NOT RUN; no full23
regression/completeCDC/analogMTBF/SoC/IRQ/routedtiming/power/hardware/ASIC signoff.


---

<!-- entry:ce957472e8ea94b5f99b29924c1c9ee3d5c35d0f6111d894d50a95e5d22c2506 -->

## T042 completed: synchronized UART reception and exact MMIO effects

T027 remains committed0ddab70. T042 passed all four gates on attempt1, exit0:
lint, test-uart-rx, git diff --check, cached check. Current task receipt:
evidence/runs/T042/attempt-1-20261106T215848954626Z.json. Current native gate receipts:
evidence/toolchain_runs/lint-20261106T215849820672Z.json, evidence/toolchain_runs/uart-20261106T220653942752Z.json, evidence/toolchain_runs/uart-rx-20261106T220726016343Z.json. Native checks/commands by profile:
{"lint": [37, 20], "uart": [34, 14], "uart-rx": [66, 24]}. Nine priorTX reference tests plus six RX tests passed.
Real RX six seed/divider runs checked752306 edge rows: fast8=27900/27907,
odd7=3133/3135, production868=345115/345116. Prior unchanged TX corpus replayed
247940 rows; total1000246 native-compared edge rows. Wrong-byte/empty/truncated
controls and two isolated pop/clear-priority RTL mutations detected exactly.
Actual synthesis found2ASYNC_REG stages, firstfanout1 to secondD, common clock.

Changed RTL: new uart_rx.sv/uart_mmio.sv, existing uart_mmio_tx.sv becomes unchanged-
interface compatibility wrapper. New DV tb_uart_rx.sv/test_uart_rx.py, lint probe
uart_full_lint_top.sv; new scripts/uart_rx_checks.py/uart_rx_structure.tcl, shared
uart_checks.py compiles dependencies; registries/state/backlog/README/UARTdocs/
evidence/report pair. No CPU/XPR/XDC/ISA/map/target/clock/reset-priority/image
change. Full frontend uses internal meaningful write10bits from master[9:0],
32-bit original byte address/read response,4BE. T031 must use that adapter and
canonical uart_mmio with raw rx_i; compatibility wrapper tiesRXhigh/W1C0.

Receiver: two stages, center sampling8N1/LSB first, default868, short false starts
ignored, bad stop discarded/one error during break until high, disable aborts
partial but preserves completed event/pending slot. RXevent passes registered
PHY-to-slot boundary one edge later. One slot; new receive overruns and retains
old unless same-edge successful originally-valid low-lane read pop, which keeps
new. Empty snapshot cannot pop future byte; response values hold. New error wins
W1C; byte1 bits8/9 clear flags only on successful response. Reset clears all;
mid-payload reset release is not an untagged framing recovery guarantee.

Audit evidence/t042-final-audit-2026-11-06.json checks current source/artifact
bindings, bus snapshots/lanes/transaction accounting/effect collisions, native
direct receiver pulses and raw sampled bit positions independently of models.
Counts: {"tools": 3, "sources": 46, "artifacts": 138, "preserved": 1094, "rx_edge_rows": 752306, "tx_replayed_rows": 247940}. All1094 historical tracked files outside8 declared
integration/report edits remain byte-identical; report prefixes and4-input failed
reference-preparation source archive retained. Preparation nativePASS66/24 is
separate from fresh task gates. Prior T027 post-gate staged whitespace initially
exit2(extra final blank line); corrected before0ddab70, final cached check exit0.
A Python3.9 helper rejected Path.write_text(newline=...) without changing files;
used byte-preserving LF write instead. No verification gate or source weakened.

Reproduce python -B scripts/verify.py test-uart-rx(includes old TX replay), and
python -B scripts/verify.py lint. Review diff/staged hashes/whitespace then commit
inspected T042 files locally; query harness next, begin actual readyT028 expected.
At next session read latest handoff/AGENTS/boundary/ARCH/verification/backlog/state/
loop first, daily --supervised, recover state.active before next.28 mandatory
completed plus1 owner-skipped of41. Registry23 retains22 predecessors; full23
regression NOT RUN. T023 formal remains skipped/NOT RUN, never PASS. No analog
MTBF/fullCDC/routedtiming/SoC/IRQ/hardware/power/ASIC signoff. Versions unchanged
Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Actual
runtime unrestricted/never, attendedonly; no install/download/global settings/
push/hostscheduler/physicalprogramming. Exactly same two Nov6 report files.


---

<!-- entry:b10e87a1c3f5ecb1004bd48cef06df8ed65b4e38e053b2bdae3fbabb08823e41 -->

## T028 prepared: GPIO and free-running timer

T042 committed d71d900 after all four first-attempt gates: lint37/20commands,
UART34/14,RX66/24;46 sources/138 artifacts,1094 old files preserved. BeginT028
from clean Git; baseline1124 tracked hashes excludes state/backlog. New absent
RTL files input_sync.sv,gpio.sv,timer.sv created before inventory but no old file
changed. Two-stage ASYNC_REG GPIO helper is needed here; T029 reset/fullCDC remains
pending. GPIO meaningful write16 from master[15:0], full32 address/read response,
4BE, output16; input16 sampled/snapshotted. Timer meaningful32 payload, COUNT/
COMPARE32, CTRL enable/auto2, sticky/W1C bit0; no interrupt. Both registered one-
outstanding interfaces hold snapshots, no consume-edge replacement, reset gates
acceptance/clears state and successful response acceptance commits writes only.

COUNT write merges selected bytes with pre-increment value and suppresses that
edge increment/match. Old compare/control govern normal counting; event beats W1C.
Timer counts through response stalls. GPIO SET/CLEAR idempotent/masked; high lanes
ignored, RO/unallocated/malformed originals error. No architecture/ISA/map/clock/
target/resetpriority/CPU/UART/XPR/XDC/image change. New test_mmio.py uses bit sets
and elapsed-epoch formulas, TB pre/post outputs and master hold, driver native
two seeds/three exact input negatives/three isolated RTL fault injections.

Five reference tests PASS. Preserve first fixture failure(mask8 at offset0 instead
of3), five-input ZIP. Native preparation mmio-20261106T221416774407Z FAIL35checks/
17commands at undetected clear-priority mutant: both positive seeds, input
negatives and SETfault passed. Archive12 exact inputs/117 generated hashes under
failed_sources/T028/native-preparation-1. Autoreloadcompare1 reasserted flag before
observation; add immediate STATUS read and isolated singlematch W1C collision,
keeping all existing cases and productionRTL unchanged. Fresh task gates pending.

Next python -B scripts/harness.py finish T028 --evidence evidence/daily/T028.md,
attempt1/3, lint/test-mmio/whitespace. On pass audit current receipt/source/vector/
summary/WDB/negative bindings, old files/report prefixes, append this same Nov6
pair, review/stage/hash/whitespace/commit thenqueryactualnext(expectedT029).
Registry24 retains23 predecessors; no full24regression/completeCDC/SoC/IRQ/formal/
routedtiming/hardware/ASIC result. T023 skipped/NOT RUN. Versions unchanged Python
3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Runtime
unrestricted/never, attendedonly; no download/install/globalconfiguration/push/
hostscheduler/programming. No owner review gate waived.28 complete+1 skipped/41.


---

<!-- entry:ced94be2279b780f5ee055f89d41aa9b3db1d79a79486adb4e7f54e86e038be0 -->

## T028 completed: synchronized GPIO and timer priorities

T042 committedd71d900. T028 passed all four gates on attempt1, all exit0: lint,
test-mmio and both whitespace checks. Current task receipt: evidence/runs/T028/attempt-1-20261106T221630943647Z.json.
Current native receipts: evidence/toolchain_runs/lint-20261106T221631390123Z.json, evidence/toolchain_runs/mmio-20261106T222532992519Z.json. Checks/commands:
{"lint": [41, 22], "mmio": [46, 20]}. Five independent reference tests passed. Real XSim two
seeds1/20261106 checked 9295 rows, every pre/post public bus/LED
output. Actual wrong-LED/empty/truncated negatives and all three isolated RTL
mutations detected: GPIO SET toggling, timer W1C winning over match, COUNT-write
allowing match. Fresh result does not relabel failed preparation.

New rtl/peripherals/gpio.sv,input_sync.sv,timer.sv; new dv/integration/test_mmio.py,
tb_mmio.sv and scripts/mmio_checks.py, docs/GPIO_TIMER.md, registry/state/backlog/
README/evidence and same two report appendices. GPIO16 raw bits through2ASYNC_REG
stages/bit, LEDs16 with maskedOUT/SET/CLEAR, IN held snapshot; internal meaningful
write16 from master[15:0], full32 address/read response,4BE. Timer full32 payload/
COUNT/COMPARE, CTRL2bits, stickyW1C bit0, no IRQ. Both one outstanding/registered
response/no consume-edge replacement; writes at successful response acceptance.
COUNT merges pre-increment bytes/suppresses increment+newmatch; old enable/
compare govern other edges; real match beats W1C. Timer continues during stalls.
No CPU/UART/XPR/XDC/ISA/map/clock/target/resetpriority/firmware change.

Independent oracle uses bit-set GPIO and elapsed-epoch closed-form timer; final
audit uses direct per-cycle modular arithmetic/bit masks on actual SV-compared
transcripts, not that oracle. Validates bus snapshots, handshakes, all16 single-bit
LED values/seven legal lane choices each, resets, timer effects/priorities and
source/wave/vector/summary/argument bindings. Audit counts: {"tools": 2, "sources": 45, "artifacts": 100, "preserved": 1119, "edge_rows": 9295}.
Per-seed inventory: [{"seed": 1, "cycles": 4648, "requests": [1851, 1797], "replies": [1850, 1796], "errors": [481, 361], "canceled": [1, 1], "gpio_single_bit_values": 16, "legal_lane_choices_each": 7, "count_write_match_collisions": 1, "match_w1c_collisions": 2, "match_events": 12, "gpio_effects": 624}, {"seed": 20261106, "cycles": 4647, "requests": [1837, 1805], "replies": [1836, 1804], "errors": [516, 358], "canceled": [1, 1], "gpio_single_bit_values": 16, "legal_lane_choices_each": 7, "count_write_match_collisions": 1, "match_w1c_collisions": 2, "match_events": 12, "gpio_effects": 589}]. Preserves1119 historical tracked
files outside5 declared integration/report edits and both earlier report prefixes.
Pre-gate evidence snapshots under evidence/prepare/T028-gate-evidence-2026-11-06.json.

Both failures retained: five-input reference fixture archive(mask8 needed byte
offset3), and12-input/117-generated native-preparation archive. First native FAIL
missed transient wrongclear during compare1 autoreload; immediateSTATUS and
singlematch collision now force visibility and detect actual faulty RTL. No
warning/negative/check/timeout weakened; original productionRTL unchanged since
first native prep. Read docs/GPIO_TIMER.md for exact evidence/limitations.

Reproduce python -B scripts/verify.py test-mmio and python -B scripts/verify.py
lint. Reviewdiff/whitespace/staged source hashes, commit inspectedT028 locally,
thenquery next and begin actualT029 expected. Next session read handoff/AGENTS/
boundary/ARCH/verification/backlog/state/loop, daily --supervised and recover
active before selectinganother. Input_sync helper introduced for GPIO does not
complete T029: async reset release/full scoped CDC analysis remains pending.
OfficialAMD UG906 pages were read ahead for CDC planning, no download/install;
2025.2-specific webURL unavailable, verify installed tool help/options; no zero-
path CDC signoff or analogMTBF inference. Notes in .tmp/t029_documentation_notes.json.

29 mandatory complete plus1 owner-skipped of41. Registry24 retains23 predecessors;
full24regression NOT RUN. T023 formal still skipped/NOT RUN, neverPASS. No
completeCDC/SoC/IRQ/routedtiming/power/hardware/ASIC result. Versions unchanged
Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Actual
runtime unrestricted/never, attendedonly; no tools/packages/IP install/download,
globalconfiguration, push, hostscheduler or physicalFPGAprogramming.
