<!-- entry:145daddc0f240f312949e2526a17e09b07323d263c3e3f525172bd4db3902577 -->

# November 2 attended resume and explicit T012 owner approval

Read the latest October 26 technical handoff, AGENTS.md, environment boundary, approved architecture submission, verification plan, backlog, persistent state and CODEX_LOOP. Ran daily --supervised and inspected clean Git at b535b78. Actual America/Los_Angeles date is 2026-11-02; no reports are fabricated for the intervening dates. Runtime remains unrestricted danger-full-access/never: the harness is not a sandbox, and unattended automation stays disabled. All engineering writes remain project-local.

The user explicitly answered 'Approve T012 and authorize that command' for python -B scripts/harness.py approve T012 --confirm-owner-review. This specific authorization persisted across resume; it is not inferred from general permission. Hash-checked the exact report from reviewed commit 4591b78 against evidence/t012-review-ready-2026-10-26.json, saved authorization evidence/owner_reviews/T012-2026-11-02.json, executed the command and saved the exact argv/stdout/stderr in T012-2026-11-02-command.json. PASS/exit 0, T012 completed. Updated README, verification report acknowledgment and T012 evidence; original report body/evidence and all earlier reports remain recoverable and unchanged where historical. No new RTL result or broad approval is claimed.

Mandatory completion is now 12/41 with no active task. Commit these inspected acknowledgment files with both whitespace gates, then begin dependency-ready T013 from clean Git. T013 is scoped to clocked stage registers/valid metadata with advance/hold/flush/reset tests; forwarding, hazard/control/bus integration and full pipeline execution remain following milestones. Maintain one active task, three verification-attempt limit, actual local report dates and exactly two reports per worked day. No architecture/ISA/map/clock/reset policy change, global configuration, installs, push, scheduling or physical hardware action is authorized by this acknowledgment.


---

<!-- entry:96dbaeb8c58260baf74435f7ea20fc32fd69b1c45df0fa3bfb54ceca3e171064 -->

# T013 stage storage prepared

Approval delivery 14d9641 is committed; began T013 from clean Git. Added rv32_pipeline_stage and pipeline_registers in rtl/core/pipeline_core.sv, with five independent IF/ID/EX/MEM/WB valid/payload slots. This is a storage scaffold, not the executable pipeline core or a changed CPU external interface. Existing reference CPU/execution units/architecture/XPR/kit are untouched. Reset/selected clear inserts zero metadata, hold retains state, capture writes valid payload; invalid payloads zero. Reset masks outputs but storage resets only at the clock edge. Local clear is already-arbitrated control: the later controller must retain the approved reset/fault/memory-hold/redirect/load-use order.

Added independent event-history oracle, direct SV bench at WIDTH1/32/129, observable synthesis probe and PIPELINE_REGISTERS.md. Seeds 1/20261102 cover all 32^3 clear/hold/valid masks, walking/complement 129-bit data, held tokens, reset collisions/pulses, independent WB drain and random transitions. Every row compares all five stages before/after the edge, with four anchored Python tests and actual corrupted-expected/empty negative rejection. Real test-pipeline and regression route are registered, with source/vector/WDB/argument hashes from the existing driver. Next finish T013 --evidence evidence/daily/T013.md uses attempt 1/3. No pass asserted before execution. Append exact results to today's same two reports, commit reviewed task files, then continue T014 if gates/budget permit. Forwarding/hazards/control/bus/complete pipeline ISA execution, formal, timing and hardware remain following evidence.


---

<!-- entry:2a2fb5093417f30a8e63ad7571097e0f821abbe804d1661c09d315d2de143df6 -->

# T013 completed on first attempt

Receipt evidence/runs/T013/attempt-1-20261103T022921997640Z.json: all four gates PASS/exit 0. UTC stamps are November 3; America/Los_Angeles report date is November 2. Lint lint-20261103T022922375287Z.json has 23 checks/13 commands, pipeline storage probe 19.078 s, zero warnings/errors and no latches/black boxes/selected structural violations. Unit pipeline-20261103T023233165030Z.json has 17 checks/10 commands. Seeds 1/20261102 each checked 39,511 full pre/post clocked vectors simultaneously at WIDTH1/32/129, total 79,022. Simulations 3.172/3.172 s. All 39 declared bins, four anchored tests and actual wrong-expected/empty negatives pass; source-drift guard passes. Groups per seed: 32,768 control crosses, 1,290 walking, 1,290 held-walking, 32 reset crosses, 32 between-edge pulses, 4,096 random and three startup/drain rows. No check or oracle weakened.

Expanded ten-target regression actually ran, PASS/exit 0, full nested record evidence/t013-regression-2026-11-02.json. Seven RTL unit components total 966,130 vectors (prior six 887,108 plus stage storage 79,022). Reference CPU/ISS separately replay their 324 retirements and terminal samples; Python memory separately replays 49,276 edges/11 tests. These units do not execute a complete pipelined CPU, and replay is not new unique program coverage. Pins unchanged: Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Original 23 baseline files are byte-identical. All generated data/waves/logs stay project-local.

Files: new pipeline_core.sv storage modules, independent ledger/SV bench, synthesis probe, PIPELINE_REGISTERS.md; manifest/registry/state/backlog/README, actual receipts/audit and today's two appended reports. Old CPU/unit RTL, architecture/XPR/XDC/kit and prior-date reports remain unchanged. Audit evidence/t013-complete-2026-11-02.json records source/artifact/preservation hashes. Mandatory progress 13/41, no active task. Commit inspected files and record SHA, then begin T014's nearest-older EX/WB forwarding, x0/unused qualification and unavailable-load blocking tests. Preserve global controller priority; local clear is already arbitrated. Full pipeline/control/bus/ISA, formal, routed timing, hardware and ASIC remain future milestones.


---

<!-- entry:c6ee81305267a3a5c0eb29ca52df116adeb453e3a52e1795347a8ba1a2b11020 -->

# T014 forwarding prepared after c020c43

T013 committed c020c43; began T014 from clean Git. Added dual-source forwarding_unit.sv, producer-age independent oracle, direct SV bench, observable synthesis probe and FORWARDING.md. Consumer valid/use/x0 and valid/write/nonzero producer qualifiers are explicit. Nearest EX/MEM result wins over older WB. A matching EX load is unavailable and blocks the operand, never forwarding its address or falling back to stale WB; only completed WB load data may forward. Values/selectors/blocked flags for both operands are checked. Caller age/fault/completion qualifications and held-source refresh remain pipeline-controller responsibilities; no full pipeline integration claimed.

Seeds 1/20261102 exercise all source/EX/WB register triples with both load states, all 256 qualifier combinations on identity edges, walking/complement and random data. Four anchored tests and actual corrupt-expected/empty negative simulations are required, plus all declared coverage and source-drift guard. Real test-forwarding and regression route registered. Next finish T014 --evidence evidence/daily/T014.md reserves attempt 1/3 for lint/test-forwarding and both whitespace checks. No pass asserted before execution. Preserve existing RTL/architecture/XPR/constraints/kit and all previous reports. Append results to today's same two files, commit inspected files, then continue dependency-ready work within the attended budget. No new approval is inferred for owner commands, installs, physical programming or unattended execution.


---

<!-- entry:7c5498cfbc596d64afb637f1c871d5bd58706258bd9635b2aa176cefcf7207ad -->

# T014 completed and eleven-target regression passed

Attempt 1 evidence/runs/T014/attempt-1-20261103T024234381472Z.json: all four required gates PASS/exit 0. Lint lint-20261103T024235074260Z.json has 25 checks/14 commands; forwarding probe 19.734 s with zero warnings/errors, no latches/black boxes/selected structural violations. Unit forwarding-20261103T024609161432Z.json has 17 checks/10 commands: seeds 1/20261102 each 72,212 full 70-bit comparisons, total 144,424, simulation 2.922/3.172 s. All 21 defined bins, four anchored oracle tests, actual corrupted-expected/empty negatives and source-drift guards pass. Per seed 65,536 identity/load crosses, 2,048 qualifier crosses, 528 walking data, 4,096 random and four anchors. Newest EX load blocks stale matching WB for both operands.

The first closing regression wrapper had an inline SyntaxError before any command/test executed; exact explanation retained in evidence/t014-regression-launch-failure-2026-11-02.json. Corrected only that launch wrapper; actual verify.py regress PASS/exit 0 in evidence/t014-regression-2026-11-02.json. Eleven targets pass. Eight RTL unit components total 1,110,554 vectors; reference CPU/ISS separately replay established retirements/terminal samples and Python memory replays its own edges. Repeats are not new unique program coverage. Pins unchanged Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Report date November 2, UTC receipts November 3. No install/global/physical/unattended operation.

Changed new forwarding RTL/bench/oracle/probe/FORWARDING.md, config/registry/state/backlog/README, evidence/audit and today's same two report files. Existing RTL/architecture/XPR/XDC/kit/prior-date reports preserved; audit evidence/t014-complete-2026-11-02.json binds sources/outputs/preservation. Mandatory 14/41, no active task. Commit inspected files then begin T015 load-use integration, preserving dependent operands and actual single commit rather than equating combinational selection with full pipeline ISA behavior. T013 storage and T014 selectors are ready components; executable pipeline, control/bus/ISA closure, formal, routed timing, hardware and ASIC remain following evidence.
