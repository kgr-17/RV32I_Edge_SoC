<!-- entry:b4e812fb9f081ced5f799b768214c8835115f2f921fe3675473177055213ffd4 -->

# 2026-11-21 T032 interrupted-session recovery

Recovered uncommitted .harness/state.json and two T032 owner receipts left by the
November15 interruption. Owner explicitly authorized supervised local Basys3
identification, the exact approved image into volatile SRAM and UART capture,
plus authorize T032. The command already returned AUTHORIZE/exit0 on November15;
do not repeat authorization or ask again. Receipts preserve question
call_9053eb495dcb4c1f9a981401711da49e and answer "Authorize T032 and that command".
State difference is exactly the T032 start approval; pending/attempt0/active=null.
Baseline HEAD73c4a29; inspect and commit only recovered files/reports before begin.

Read latest November15 technical handoff and required startup files; hashes in
evidence/hardware/recovery-2026-11-21.json. daily --supervised exit0; actual LA date
November21. Prior-day reports untouched. Runtime unrestricted/approval never;
attended-only, no scheduler/download/install/global changes. No hardware connected
or programmed by the recovered session. T043 completed; formal T023 skipped/NOT RUN,
physical and ASIC NOT RUN. Next begin T032 after clean commit, inventory relevant
USB/serial interfaces and implement independent hardware evidence checks. Preserve
all failures; missing hardware is NOT RUN and must not consume a finish attempt.


---

<!-- entry:bc19ec0b887c932f6235ff288cae3b3d97269ccc16c8ff902806eef4b0c2a815 -->

# T032 native discovery and guarded-programming checkpoint

Recovered authorization in commit58ccbe5, then begin T032 exit0. ActiveT032/
in_progress/attempt0, daily_tasks includes November21. Owner now confirms board
connected in call_ce0d1c5587a74ba9b7490383b62f6650, answer "It is connected now".
Native inventory PASS evidence/hardware/inventory-20261122T015411030005Z.json:
Vivado/hw_server2025.2 SW6299465, target localhost:3121/xilinx_tcf/Digilent/
210183B03B59A, device xc7a35t_0/xc7a35t, IDCODE binary
00000011011000101101000010010011. Present parent USB serial210183B03B59 joins
JTAG interfaceA to UART interfaceB, COM3. Win32_SerialPort omitted this device;
Get-PnpDevice -PresentOnly and .NET port names independently show COM3.

Implemented scripts/hardware.py, hardware.tcl, hardware_serial.py,
hardware_evidence.py and8 independent policy tests. Hardware-only inputs match
T043; new workflow tooling is separately bound. Every live operation requires
active authorizedT032, completedT043, approved manifest/image/source hashes,
local unique target/part and exact shared-parent COM association. Tcl checks
before connect and again before programming. No flash/remote/driver commands.
Captured native outputs/hashes and exact UART/raw event checks; missing physical
session is NOT RUN. Human DONE/reset observation remains required.

Preserved initial FAILs: Vivado PYTHONHOME contamination and PowerShell script
execution restriction in evidence/failed_sources/T032/initial-native-probe/
(40-file inputZIP), and PnP regex escaping in pnp-regex/. Fixed child Python
process environment only, native read-only cmdlets (no script-policy change),
and direct Win32 serial capture. Independent negative elapsed-time test exposed
a validator defect; retained FAIL receipt evidence/prepare/T032-negative-event-
time-failure-2026-11-21.json, fixed >=0 check; all8 tests now pass. No lowered
oracle/check or finish attempt used. Native probes are preparation, not hardware
PASS. No CPU/XPR/XDC/firmware/clock change. Exactly two November21 reports;
formal skipped/NOT RUN, ASIC NOT RUN. Next program approved image then capture
two owner-operated btnC resets and actual DONE observation, register/check the
physical evidence gate, freeze source and run required finish gates. If interrupted,
inspect existing programming/capture receipts before repeating any device action.


---

<!-- entry:1e120ed55606325fcaf3f63aac126dcf62c0e74893bb26f1cb4fd16b7e34c1ea -->

# T032 actual programming saved; waiting for physical reset observation

Checkpoint8b57b5e saved tooling/tests/preparatory failures. Authorized actual
programming PASS/exit0 on November21, receipt
evidence/hardware/program-20261122T015603204700Z.json. Vivado2025.2/SW6299465 and
hw_server2025.2 targeted localhost:3121/xilinx_tcf/Digilent/210183B03B59A,
xc7a35t_0/xc7a35t, observed IDCODE00000011011000101101000010010011. Shared USB
parent210183B03B59 associates JTAG-A and UART-B/COM3; no first-device guessing.
Programmed only approved volatile image SHA256
13f3639d2b01feded384a1316207a0ddb02fb5d4036bc399901fc87fd2aacbd9. No flash,
driver/install/global policy/RTL/XPR/XDC/clock/firmware changes. Approval remains
valid; do not ask again or repeat authorize. Python3.9.13/Git2.48.1 unchanged.

First real UART capture: evidence/hardware/capture-20261122T015621336421Z.json,
60.516seconds, command exit0 with READY and COMPLETE markers, raw0bytes/events0.
Physical success observation NOT RUN, retained without manufacture or weakened
oracle. Owner reset/DONE reply has not arrived. No formal task finish attempted,
budget still0/3. Active T032/in_progress; human reset is the outstanding dependency.
Do not repeat programming simply to get serial data: firmware is one-shot and
needs btnC reset with capture listening. No generic LED success inference.

Added hardware-evidence registry entry (only addition; full28 regression unchanged):
policy tests then read-only physical-session validator.10 policy tests PASS/exit0,
receipt evidence/prepare/T032-policy-2026-11-21.json. Cover real Tcl sequencing with
mock hardware, authority/target/part/interface rejection, error diagnostics,
timestamp/raw-byte framing, source/artifact drift, distinct ordered epochs and
owner observations. Mock fixtures never enter physical evidence. Actual
verify hardware-evidence preflight returned125/NOT RUN because session.json is
missing; receipt evidence/prepare/T032-hardware-preflight-2026-11-21.json. Missing
physical inputs must not pass. Required T032 lint/test-soc final gates have NOT
RUN this task yet; do not spend a finish attempt before complete physical proof.

No execution policy was changed: blocked PS file prototypes remain in initial
failed-source archive; current serial capture uses Win32 Python ctypes. Direct
read-only PnP cmdlets enumerate relevant FTDI devices; no blocked script is
evaluated. Tcl removes vendor PYTHONHOME/PYTHONPATH only in its process around
the selected child interpreter and restores them. Native caps120s unchanged.
Initial native failures, the independent negative-time test FAIL, and empty
capture all retained. Actual capture opened successfully without serial errors.

Audit evidence/hardware/audit-2026-11-21.json PASS checks program/source/image
and capture artifacts, exact source equality and unchanged regression registry.
T032-program-and-empty-capture-2026-11-21.zip preserves all program inputs,
native job/report/copy and raw capture/job/event artifacts plus receipts. CRC
and member SHA passed. This archive proves integrity, NOT functional board PASS.
Tooling code is in Git; programming/capture evidence is added to the delivery
commit. T043 approved hardware/manifest remain unchanged; new T032 workflow
registry/checker files are intentionally separate from its frozen source snapshot.

Next session: read this latest handoff/startup files, inspect Git, daily --supervised,
recover activeT032 with begin T032 (no approval repeat). First inspect existing
program and captures. Wait for owner's "Ready for another capture now" reply;
the first timed window has ended. Start a fresh epoch1 capture for60s using
`python -B scripts/hardware.py capture --program evidence/hardware/program-20261122T015603204700Z.json --epoch 1 --seconds 60`,
then immediately prompt owner to press/release btnC once and confirm DONE lit.
Repeat epoch2 as a warm reset without reprogramming; preserve all unsuccessful
captures. If owner confirms reset but no UART arrives, diagnose actual serial/
board behavior; do not fabricate printouts or change approved image implicitly.
If power cycled, establish current board state before deciding whether reloading
the already-authorized image is needed. Authority covers this exact volatile
scope; other images/flash/driver changes remain unauthorized.

After two exact physical IRQ PASS CRLF captures, save truthful owner DONE/reset
observations with actual question/reply IDs. Bind program, two distinct successful
captures and observations via SHA256 in evidence/hardware/session.json (schema1,
kind physical_basys3, program, captures, observations, inputs_sha256). Validate
read-only checker and freeze all tooling; run finish T032 --evidence
evidence/daily/T032.md for lint/test-soc/hardware-evidence+whitespace gates.
Never self-approve final T032. Formal T023 skipped/NOT RUN; ASIC NOT RUN; board
programming PASS is distinct from still-pending physical functional acceptance.
Today's two reports append findings; no prior-day report edits or scheduling.


---

<!-- entry:42c54be9cc604d70de95c5f3e3fa8db6d54674af0272a072b9c24883d1841e5a -->

# T032 delivery checkpoint

Committed c7ced03: actual programming receipt, empty capture, 51-member integrity archive, physical evidence gate, policy tests and current bilingual reports. All15 staged files matched working bytes; git diff --check/cached check, Python syntax and harness validate passed/exit0; postcommit status clean. Earlier recovery58ccbe5 and tooling8b57b5e remain.10 policy tests PASS; hardware-evidence preflight125/NOT RUN; no finish attempts spent. ActiveT032/in_progress, attempts0, owner authorization already valid. Both dated reports preserved and earlier-day reports unchanged.

Waiting only for owner's readiness to operate btnC during a fresh capture. The first60s capture has ended; do not call it active or accept a late reset reply as captured data. Do not reprogram/reauthorize blindly. Resume a fresh epoch1, then epoch2, truthful DONE/reset observations, session hashing and full required gates. No physical functional PASS, no final T032 review request yet, no later task begun. Git saved locally; no push/scheduling or system changes.


---

<!-- entry:af0932b551ad40da97ee4398e6391697bd30679abe2cd2e35520cba2d9fba947 -->

# T032 owner needs button-location help

Owner replied to call_b930ecb459514c53a831393eeff00057: "I could not perform the reset", and to call_3b2b725ce9a249a089e7a245ea98933e: "I need help finding btnC". This confirms the empty capture is not a successful reset observation. DONE remains unobserved. No new capture/programming or finish attempt was run. ActiveT032/in_progress, attempts0; authorization persists. Baseline ef31a3d.

Read official Digilent Basys3 manual (board callouts and general-purpose IO) and official Digilent Master XDC: BTNC is the center user button, U18, matching this project's btnC pin. Give the owner a simple five-button cross diagram (BTNU above; BTNL/BTNC/BTNR across; BTND below). Leave the separate PROG configuration control alone. No capture is currently active. Wait until owner identifies BTNC and says Ready, then start a new60s epoch1 capture and request press/release during that window; later epoch2 and truthful DONE/reset observations remain mandatory. Do not spend another empty timed window before readiness or infer a button press/DONE light from these replies. No RTL/tooling change; no new simulation/formal/hardware functional PASS. Same-day reports appended, prior entries retained. Source: https://digilent.com/reference/_media/reference/programmable-logic/basys-3/basys3_rm.pdf and https://github.com/Digilent/Basys3/blob/master/Resources/XDC/Basys3_Master.xdc .
