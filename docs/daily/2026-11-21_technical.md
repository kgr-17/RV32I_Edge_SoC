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
