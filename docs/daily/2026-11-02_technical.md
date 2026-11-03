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


---

<!-- entry:609c05144fe2cf84b14fb1bc7eae52fda33cd2975e1e356ff300f65ef545227e -->

# T015 interlock and executable pipeline integration prepared

T014 committed 43a572a; began T015 from clean Git. Added hazard_unit.sv and pipeline_cpu.sv implementing pipeline_core under reviewed external ports, reusing approved decoder/ALU/RF/branch/LSU/stage/forwarding units. IF maintains one offered/accepted unanswered transaction; a three-word FIFO holds already-responded fetches, preserving instruction order and allowing burst dependencies after long memory hold. This is internal buffering, not a cache or architectural protocol revision. MEM hold drains WB once; unresolved load consumers remain in EX through response and release on WB forwarding. Held EX operands capture transient qualified WB/EX values. Fault/redirect/reset/bus wiring preserves reviewed age, effect and drain rules, but dedicated T016/T017 collision/stress and T018 independent pipeline closure remain required.

Added independent detector set-intersection tests, actual pipeline bus bench and five explicit hand-assembled retirement scenarios: both-source load dependence, disappearing WB refresh while held, load-to-store, x0 load and seeded data chains. IF ready/latency1 and data latency12..15 force queued bursts and long holds. Actual simulator must observe nonzero hazard and held-refresh cycles, compare full retirement/order/final RAM, stable requests, one outstanding/no duplicate and sticky fault plus stale fetch drain. No selector-only pass can satisfy those checks. Four oracle/four program tests supplement actual RTL runs. Generic unit driver now hashes explicit extra imported helper inputs and rejects a missing helper, with a new policy test; existing profiles retain behavior.

Registered test-hazards with both actual detector and load_use backend profiles and observable synthesis probes. First finish T015 --evidence evidence/daily/T015.md uses attempt 1/3 and runs lint/test-hazards plus both whitespace gates. Results pending. Old reference CPU/bench, architecture/XPR/XDC/kit are unchanged. Save failures, append today's same two reports, commit only inspected task files and preserve recoverability. No formal/full ISA/timing/physical/ASIC signoff, tool installation, owner-command or unattended authorization inferred.


---

<!-- entry:22ce1ff0f113366b3e75c6e686784d9aa18150d44f2a0a27459b1db48cad9f22 -->

# T015 attempt 1: functional execution passes, synthesis budget insufficient

Receipt evidence/runs/T015/attempt-1-20261103T030935925917Z.json: lint FAIL, test-hazards and both whitespace gates PASS. Pipeline probe reached technology mapping with no warnings/errors but hit the existing 45-second command timeout; Windows Job cleanup returned raw0, still correctly classified TIMEOUT/failure. No full-pipeline synthesis pass is claimed. Lint lint-20261103T030936311706Z.json retained. Functional hazard-20261103T031435072503Z.json compares 37,312 vectors per seed; load_use-20261103T031449865087Z.json actually executes five cases/64 retirements per seed (128 total), observed hazard177/161 cycles and held-WB refresh2/2. All full retirement/order/RAM/protocol and actual wrong-expected/empty checks pass. Input parser counts303/seed are not retirements.

Archived 22 exact first inputs in evidence/failed_sources/T015/attempt-1/inputs.zip plus hashes. No RTL/oracle/stimulus/structural Tcl/filter changes for retry. Explicit finite resource budgets now scale with design: existing synthesis defaults45; new pipeline CPU120 and manifest/runner maximum120; composite lint/toolchain-rtl600 with outer/inner propagation and maximum600, other commands default300. All timeouts still fail, process-tree cleanup remains, warnings/structure/coverage/negatives are unchanged. This changes project compute allowances, not actual sandbox controls or owner approval gates. Five new budget-policy tests plus updated bound/real descendant cleanup, existing harness/acceptance tests are included before functional checks. CODEX_LOOP documents it. Retry uses attempt2/3 with no budget reset or unbounded loop. Preserve complete synthesis result and both source/evidence hashes when it finishes.


---

<!-- entry:1b6fb8475e085c6115fc943420386f35bdb2c56f1439303e0673b2260d2e8c48 -->

# T015 passed second attempt and full regression

Receipt evidence/runs/T015/attempt-2-20261103T032242259806Z.json: all four gates PASS/exit0. Lint lint-20261103T032242656865Z.json passed29 checks/16 commands; integrated pipeline probe completed37.969s with zero warnings/errors and all structural checks. Explicit finite budgets120/600 are honored; timeout never passes. First timed-out inputs/logs remain intact. No RTL/expectation/structural-Tcl/filter change between attempts. Workflow resource-budget propagation and guards are tested. Test-hazards ran79 Python tests: budgets5/process7/acceptance16/harness35/unit-policy8/detector4/program4, including real descendant cleanup.

Actual detector hazard-20261103T032807683328Z.json compares74,624 vectors across two seeds, all7 bins and both negatives pass. Actual pipeline load_use-20261103T032822104969Z.json compares64 retirements/five scenarios per seed,128 total, cycle762/733, simulation2.454/2.422s, actual hazard177/161 cycles and held-WB-refresh2/2. All full fields/order/RAM/protocol/fault-drain and corrupt/empty checks pass.303 input rows/seed are not instructions. Full twelve-target regression PASS/exit0 in evidence/t015-regression-2026-11-02.json. Nine unit components total1,185,178 vectors; reference CPU/ISS324 retirements and new pipeline128 are separate replays; Python model49,276 edges separate. Pins unchanged Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465.

Changed hazard and executable pipeline integration, new bus/producer-set/hand-program tests, observable CPU probe, explicit extra helper hash support, bounded runtime budget support/tests, registry/manifest/state/backlog/README/CODEX_LOOP/LOAD_USE, evidence/archive/audit and today's same two reports. Old reference and unit RTL, approved architecture, XPR/XDC/kit and prior reports preserved. Audit evidence/t015-complete-2026-11-02.json records source/artifact/history proofs. Mandatory15/41, no active task. Commit inspected files then begin T016 dedicated redirect/wrong-path/age testing. Five dependency scenarios do not establish complete pipeline ISA, control collisions, random timing/reset, formal, routed timing, hardware or ASIC closure. No installs, pushes, physical action or unattended execution.


---

<!-- entry:cf6b4847a0432d619566f924bf496d2da359edf47ccc22732b50f1422f94524a -->

# T016 dedicated control and age cases prepared

T015 committed9fc5830; beganT016 from clean Git. Added test_flush.py/tb_control.sv and CONTROL_FLUSH.md, registry/control unit profile. Production RTL and original/reference tests are unchanged at preparation.21 scenarios per seed combine original ISA11, dependency5 and five explicit collisions. Cases16/17 force a qualified redirect to wait behind older memory then kill a wrong-path store/illegal instruction. Case18 uses a loaded odd JALR target and checks WB forwarding, bit0 clear and link readback. Case19 forces older WB fault against younger MEM store and requires no offered request/effect. Case20 redirects from ROM0xfffc while a speculative0x10000 fetch errors; that killed error must drain and not terminate architecture. Each designated case has a nonzero runtime collision requirement, preventing vacuous metadata coverage.

Actual pipeline bench preserves full ordered retirement/RAM/fault/stability/outstanding/drain/progress checks and actual corrupt/empty rejection. Four generator tests and all imported helper SHA binding required. Seeds1/20261102, IF latency1/data12..15; random waits/reset stress and independent pipeline ISS closure remain following tasks. Next finishT016 --evidence evidence/daily/T016.md reserves attempt1/3 and runs lint/test-control plus both whitespace gates. No pass asserted before execution. Preserve failure evidence and approved control priority; append today's same two reports, commit inspected scope, then continue T017 if ready/budget permits. No architecture/global/tool-install/owner-command/physical/unattended approval inferred.


---

<!-- entry:d9cc858b6570c6a61cb9273ba1482190f3b91f6b50173976dad6f0d00b1e9635 -->

# T016 passed first attempt with no RTL change

Receipt evidence/runs/T016/attempt-1-20261103T034053597508Z.json: all4 gates PASS/exit0. Lint lint-20261103T034053984038Z.json29 checks/16 commands; actual control-20261103T034520677473Z.json17 checks/10 commands plus four generator tests. Seeds1/20261102 each251 retirements/21 scenarios, total502/42;1,249 parser rows per seed are not instruction counts. Simulations2.563/2.500s, cycles2204/2218. All70 required program bins and actual wrong-expected/empty checks pass. Each seed14 qualified redirects; case16 deferred17/17 cycles, case17 deferred12/15, case18 loaded-JALR hazards16/13, case19 suppressed store1/1, case20 drained killed fetch access error1/1. All designated per-case nonvacuity checks pass alongside full retirement/order/RAM/fault/stability/outstanding/drain/progress checks. This includes all forty instruction/nine fault families through hand-expected pipeline execution; independent pipeline ISS is stillT018.

Full13-target regression PASS/exit0 in evidence/t016-regression-2026-11-02.json. Scalar/storage units1,185,178 vectors, reference/ISS324 retirements, pipeline dependency128 and control502 replay scopes, Python model49,276 edges remain separate. Replays do not expand unique program coverage. Production RTL, reference tests, architecture/XPR/XDC/kit and prior-date reports unchanged. Audit evidence/t016-complete-2026-11-02.json binds current test/helper/config and actual artifacts/preservation. Pins unchangedPython3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465. Mandatory16/41, no active task. Commit inspected files then beginT017 random request/response waits without weakening the deterministic collision cases. No formal/full certification/routed timing/physical/ASIC claim or install/global/push/scheduler/programming action.


---

<!-- entry:91403d3d5a260a55e0bc1621c2b0e2678ce163355d85e10fcb3ae368c653c39e -->

# T016 delivery sequencing guard

The preservation audit returned an ongoing subprocess session, not completion. A premature dependent git add then failed exit128 on its not-yet-created audit file. Fail-fast logic prevented commit and the clean-baseline guard refused T017 begin. No new task was started, no state was forced and no data was discarded. Waited for the audit session to finish successfully:411 historical files preserved and143 artifacts hash-verified. Then perform staging/whitespace/hash checks and commit before retrying T017. This was orchestration sequencing, not an RTL or test failure; required gates remain passed. Future audits use a longer bounded initial wait and dependent mutations wait for explicit process completion.
