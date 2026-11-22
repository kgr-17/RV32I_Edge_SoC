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
