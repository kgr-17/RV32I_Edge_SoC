<!-- entry:49a8f75dc2923caf04b9fd370e1f45cb6c78935c2739725fdf6be75df9096416 -->

# October 25 attended resume - T005 ALU prepared

Read the latest October 23 technical handoff, AGENTS.md, boundary, approved architecture submission/owner record, verification plan, backlog, persistent state and CODEX_LOOP. Ran daily --supervised and inspected clean Git. Starting commit 92a4fce0b54bdc4a940c3f81098f10956b8fb220. Actual America/Los_Angeles date is 2026-10-25. No October 24 session/report is fabricated. T001..T004 completed, no active task; began dependency-ready T005. Multiple sequential tasks per attended day are authorized. Runtime remains danger-full-access/never, with no filesystem sandbox; unattended stays disabled.

Added rtl/core/alu.sv: combinational op_t plus 32-bit operands to 32-bit result and supported flag. Supports stable enum IDs 19..37, register/immediate aliases, modulo arithmetic, signed/unsigned comparisons and low-five-bit shifts. Unsupported selectors output zero/unsupported; this is not an architectural fault event. Caller operand selection and later branch/LSU/retirement remain separate. Package, approved architecture and original XPR/kit/constraints unchanged.

Added dv/unit/test_alu.py and tb_alu.sv, scripts/unit_checks.py and test_unit_checks.py, docs/ALU.md, lint/unit manifest entries and real test-alu registry/regress route. Independent expected values use integer arithmetic/modulo, multiplication/floor division for shifts, not RTL parsing. Directed edges, exhaustive signed small domains, all shifts with ignored upper bits, random full-width pairs and unsupported six-bit selectors are replayable with seeds 1/20261025. Actual wrong-answer and empty-file negative simulations must be rejected. Driver records exact commands, versions, vector/WDB/Tcl/source hashes and checks no source drift during the run.

Next run python -B scripts/harness.py finish T005 --evidence evidence/daily/T005.md, reserving attempt 1 of 3 and running required lint/test-alu plus whitespace gates. Results pending, no functional pass asserted. Full logs go to evidence/runs/T005 and evidence/toolchain_runs/alu-*.json; generated outputs are under build/units and retained scoped lint directories. Append final results and actual delivery commit here and to the Chinese report. Once T005 is verified and committed, continue T006 register file to its required owner review gate; do not stop merely because another task was completed today. No download/install, host scheduling, push or FPGA programming. Official pinned ISA documentation reads remain authorized.


---

<!-- entry:09e972bf453a8b212ac9fad8fc0f264de54e77808db8788c916b6088424f0669 -->

# T005 acceptance completed on attempt 1

All four required finish commands passed, exit 0: verify.py lint, verify.py test-alu and both Git whitespace checks. Receipt evidence/runs/T005/attempt-1-20261026T040605020526Z.json. Date is October 25 in America/Los_Angeles; the receipt's October 26 stamp is UTC, not a different reporting day. No retry, weakened check or scoped DUT defect.

Lint receipt evidence/toolchain_runs/lint-20261026T040605428543Z.json: 13 checks/8 commands; decoder 27.968 s, ALU 27.234 s, fixture 25.047 s, all positive synthesis passes. ALU reported zero warnings/errors and passed latch/black-box rejection plus LUTLP-1/MDRV-1 checks. Intentional latch rejection raw exit 1 was expected. This is unit synthesis/structural lint, not routed timing or full CPU implementation.

Unit receipt evidence/toolchain_runs/alu-20261026T040753354907Z.json: 17 checks/10 commands. Compile 0.734 s, elaboration 0.907 s. Seeds 1 and 20261025 each checked 117,402 full result/support vectors (234,804 total), saved hashed waveforms, and hit every supported selector plus unsupported. Per seed: exhaustive 64x64 signed small domain for 19 selectors (77,824), 17x17 full-width edges (5,491), all shift amounts with four high-bit forms (13,056), random legal (19,456), unsupported (1,575). Positive simulations took 2.797/2.734 s. Both actual wrong-answer and empty-file negatives were rejected even though XSim raw exit was 0. Driver's exact completion and diagnostic checks prevented false passes; source hashes were unchanged during the run. This is defined stimulus coverage, not code coverage or CPU ISA certification.

Python gate passed 26 tests: test_rtl_checks.py 15, test_unit_checks.py 5, test_alu.py 6. Pins matched Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2 and Vivado/XSim 2025.2 / SW build 6299465. Full command output/exits and source/vector/WDB/Tcl/argument hashes are retained. Completion audit evidence/t005-complete-2026-10-25.json records preservation and delivered source hashes.

Modified/new files: rtl/core/alu.sv; dv/unit/test_alu.py and tb_alu.sv; scripts/unit_checks.py and test_unit_checks.py; config/rtl_checks.json; .harness/checks.json; docs/ALU.md; state/backlog projections; evidence/daily/T005.md; timestamped receipts/audit/report entries; today's exact two reports. Original package/decoder, architecture, XPR/XDC and kit are unchanged. No source integration into XPR is required before a usable board top exists. Formal, execution/retirement, routed implementation/timing, hardware and ASIC remain NOT RUN. Combined regress routing is prepared and will be exercised at the T006 unit-review boundary.

Review/stage only T005 files, check whitespace and commit locally. Then begin T006 from clean Git in this same attended session. Record the actual T005 SHA in the next entry. T006 must implement two combinational reads, one rising-edge write, nonzero WB-to-ID bypass, x0 immutability and synchronous reset per unchanged architecture. Independent seeded tests and real lint/test-regfile are mandatory. Its finish ends at awaiting_review; never approve it on the owner's behalf. Runtime remains unrestricted/attended only; no downloads, scheduling, global changes, pushes or programming.


---

<!-- entry:8d864bfaabd2ccaa7de94fcfcbd152291b133002dccccb97ac8b2ad86db460a1 -->

# T005 committed; T006 prepared in the same attended session

T005 delivery commit 0b89a04a0336af843b37c8623880d819a2c97050 contains the ALU and its passed evidence. All whitespace checks passed and Git was clean before begin T006. This demonstrates the new sequential multi-task policy in the actual project; both tasks are in daily_tasks[2026-10-25]. T005 source/evidence remains recoverable and earlier claims unchanged.

Added rtl/core/regfile.sv with ports clk_i/rst_i, write_en_i, write_addr_i[4:0], write_data_i[31:0], two read addresses[4:0] and two read outputs[31:0]. x0 has no storage, x1..x31 reset synchronously to zero, reset wins over write, and each nonzero read selects matching current write data before stored data. Reads mask to zero during reset; between-edge reset pulses must retain storage. No reviewed architecture/core interface changed. Caller must supply valid retiring WB enable; pipeline/stall capture remains later work.

New dv/unit/test_regfile.py uses last-event history queries, independent from the RTL array, and six fixed oracle tests. tb_regfile.sv checks both ports before the edge, after the edge with bypass disabled, and during/after between-edge reset pulses. Directed coverage includes all source pairs, register collisions, x0, disabled writes, walking bits/complements and resets; 4,096 random cycles use seeds 1/20261025. Wrong-answer and empty-input negative simulations remain mandatory.

New dv/lint/regfile_lint_top.sv makes both read cones observable through a selected 32-bit synthesis-probe output; direct functional DV still uses both full ports. The same latch/black-box/structural checks remain. Registered manifest/registry entries and strengthened T006's original lint/test-regfile commands with a third composite regress command, validating fixture/decoder/ALU/RF routing together at this owner-review boundary. No prior acceptance criterion or gate was removed. docs/REGFILE.md contains interface details and a concrete review checklist.

Next run finish T006 --evidence evidence/daily/T006.md. Results pending and at most three attempts; success must end awaiting_review. Do not begin T007 or invoke owner approval. Append actual evidence and modified files to these same two October 25 reports, review the diff and commit. This is attended work under unrestricted permissions; no unattended automation, installation, global change, push or FPGA programming. No formal, timing, hardware or ASIC result is claimed.


---

<!-- entry:96edc8ae05ae9b44ed3912933ba4bfc6b271ec6b8eec2fb631aa683f913cfa7f -->

# T006 attempt 1 retained; RTL hierarchy repair prepared

Receipt evidence/runs/T006/attempt-1-20261026T041216038008Z.json records lint FAIL/exit 1, test-regfile PASS, composite regress PASS and both whitespace checks PASS. The gate correctly rejected WARNING [Netlist 29-101]: the large primitive-only regfile cellview was unsuitable for floorplanning. The vendor process returned 0 and emitted the lint completion marker, but warnings are independently fatal to acceptance; no false pass was recorded. Lint evidence is evidence/toolchain_runs/lint-20261026T041216417257Z.json. Functional RF comparisons and the complete newly combined fixture/decoder/ALU/RF regression passed under the first implementation; that does not override failed synthesis lint.

The repair partitions regfile.sv into 31 rv32_regfile_word instances (each 32-bit rising-edge storage with reset priority) and two rv32_regfile_read instances (combinational reset/x0/bypass/store-data selection). Both public read outputs remain net-connected 32-bit values with identical behavior. Internal word enables use the shared clock and address decode, never fabric clocks. Explicit hierarchy is the design repair; no test/oracle, warning severity/filter, synthesis Tcl, hierarchy flag, gate or timeout was weakened. The approved architecture/ISA/reset/clock and original project are unchanged. AMD's official UG901 hierarchy guidance was read for diagnosis; no tools/IP/packages were downloaded.

Next run finish T006 with its same evidence path, consuming attempt 2 of 3. Preserve all first-attempt logs and hashes; document the rerun's actual result before claiming acceptance. Keep the task active/failed until verification succeeds or its budget blocks it. Success still requires owner review before T007, not agent approval. Exactly the same two October 25 reports are appended. Runtime stays unrestricted and attended only.


---

<!-- entry:56e3f7ab8082f0ea09dd9a09bd5e9f4c8c596350f7c376600a9874ffddb6ac15 -->

# T006 automated acceptance passed on attempt 2 - owner review required

## Final outcome and failure preservation

Final receipt evidence/runs/T006/attempt-2-20261026T041624015172Z.json records five PASS/exit-0 outer commands: python -B scripts/verify.py lint, test-regfile, regress and both Git whitespace checks. State is awaiting_review, active=null, attempts=2/3. This is not completed until the owner reviews it. Attempt 1 and its warning failure remain in evidence/runs/T006/attempt-1-20261026T041216038008Z.json. The exact first RTL source is archived at evidence/failed_sources/T006/attempt-1/regfile.sv; SHA-256 d1b753957a9881e977ee96fc21be4d8756c6ef33c93082a75ae1c1c7995234c8 matches its original unit-run source hash. No warning suppression, severity/filter change, Tcl/hierarchy-flag change, timeout change or test/oracle weakening occurred. Explicit word/read hierarchy removed the Netlist 29-101 warning while preserving the public interface.

Lint receipt evidence/toolchain_runs/lint-20261026T041624412017Z.json: 15 passing checks over 9 commands. Register-file probe synthesis 26.531 s, zero warnings/errors, no latches/black boxes or selected structural violations. Decoder 23.093 s, ALU 25.281 s, fixture 22.734 s also passed; intentional latch defect was correctly rejected. This is scoped synthesis/structural lint, not routed floorplanning/timing or complete CPU implementation.

Direct RF unit receipt evidence/toolchain_runs/regfile-20261026T041823227812Z.json: 17 passing checks/10 commands. Seeds 1 and 20261025 each checked 10,369 clocked rows (20,738 total), both 32-bit read ports before the edge and actual storage after bypass was disabled. Thirty-one pulse rows per seed also checked temporary read masking and state preservation without a reset edge. All 73 defined address/reset/bypass/x0/hold bins hit. Six independent event-history oracle tests passed. Both wrong-answer and empty-file negative simulations were correctly rejected despite raw XSim exit 0. Source hashes remained constant during verification. No scoped functional bug was observed; the encountered defect was the flat synthesis hierarchy warning.

## Full combined unit regression now executed

All four components passed together through the registered regress entrypoint; receipt basenames below are under evidence/toolchain_runs:

| Component | Receipt | Positive vectors |
|---|---|---:|
| Register infrastructure fixture | regress-20261026T041837780332Z.json | 268 |
| RV32I decoder | decode-20261026T041854703067Z.json | 287,618 |
| ALU | alu-20261026T041911924439Z.json | 234,804 |
| Register file | regfile-20261026T041926641095Z.json | 20,738 |

Total 543,428 positive vectors across eight seeded simulations, 66 EDA acceptance checks. This is a combined unit suite, not connected core/pipeline integration. Existing seed rechecks are repetitions, not new unique stimulus coverage. Composite Python execution counts were policy 15 + decoder oracle 6 + repeated policy 15 + unit-driver 5 + ALU oracle 6 + RF oracle 6 = 53 test executions, including repeated shared policy tests. Direct RF's six tests and earlier T005's 26 are separate/repeated invocations, not added distinct coverage. Fixture fatal/missing-marker/hang/syntax rejection and all three production units' wrong-answer/empty cases passed. Hangs remain TIMEOUT even when raw exit is 0.

Pins matched Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2, Vivado/XSim 2025.2 / SW build 6299465. Full argv/stdout/stderr/status/exits, seeds, counts, coverage and source/vector/WDB/Tcl/argument hashes remain in immutable run records. Generated files live under build/units/regfile-*, build/units/alu-*, existing scoped build/T004 decoder and build/T003 fixture/lint directories. Dates in filenames are UTC; the reporting/history date stays October 25 in Los Angeles.

## Changes and preservation

New files: rtl/core/regfile.sv (public module plus word/read modules), dv/lint/regfile_lint_top.sv, dv/unit/test_regfile.py, tb_regfile.sv, docs/REGFILE.md, evidence/daily/T006.md, failed-source snapshot, first/second harness/EDA receipts, completion audit and report-entry inputs. Updated config/rtl_checks.json, .harness/checks.json, README.md, VERIFICATION_PLAN.md and controller state/backlog. Strengthened T006 backlog verification by adding complete regress after original lint/test-regfile; no original check removed. Today still has exactly two daily Markdown reports, both appended with all T005/T006 findings.

Audit evidence/t006-review-2026-10-25.json checked all 23 original files, 119 existing historical/source files and both T005 report prefixes against baseline 0b89a04, plus 44 source-artifact vector/WDB/Tcl/argument hashes from successful final runs. All matched. Existing T001..T005 states/attempts/receipts, legacy claims/exceptions and owner reviews are unchanged. Original XPR/kit/constraints, approved architecture and ALU/decoder/package RTL remain untouched. T005 delivery is 0b89a04a0336af843b37c8623880d819a2c97050; T006's actual delivery SHA is appended after its inspected commit. All work is project-local under an attended unrestricted runtime. No install/download of tools/IP/packages, global change, scheduler, push or FPGA programming.

## Owner gate and exact resume instructions

Stop for the T006 review gate: docs/BACKLOG.json sets human_approval_required=true, and AGENTS.md says never call approve on the owner's behalf. docs/REGFILE.md is the concrete interface/evidence checklist. The owner may run python -B scripts/harness.py approve T006 --confirm-owner-review after reviewing x0, pre-edge writeback bypass on both ports, reset/write priority, synchronous state retention and unit evidence. No approval command has been invoked by the agent. Do not implement T007 until the persisted review completes, and do not infer approval from a generic keep-going request. No additional architecture proposal is needed for this unchanged behavior.

Current project in_progress: 5/41 mandatory completed, T006 awaiting_review, 35 mandatory pending and four optional disabled. Next session reads this latest October 25 handoff plus the mandatory contract files, inspects actual permissions and Git, runs daily --supervised/validate/status/next and honors the review hold. After owner review, next is T007 branch comparator/target math/JALR bit clearing; it may proceed in the same attended day without calendar quota. Keep real lint/test-branch, independent signed/unsigned/target/alignment tests and the full regress route. Formal proof, CPU retirement/hazard/long-stall integration, precise bus/fault ordering, routed timing, physical board and ASIC remain NOT RUN; unit simulation is not signoff for those milestones.


---

<!-- entry:23545b65d2dbe69f7829f0a28e960168184db7b150d12102a97ea8bff77e84d2 -->

# Committed October 25 delivery - owner review resume point

T005 ALU delivery is 0b89a04a0336af843b37c8623880d819a2c97050 (19 inspected files, attempt 1 completed). T006 register-file delivery is 4f67b3ccfe104f5078f74a5e52adf862d078a6bc (33 inspected files, automated acceptance passed on attempt 2, awaiting_review). Both are on engineering/bootstrap, parent session baseline 92a4fce. All seven T006 audited source/config/driver SHA-256 values matched staged blobs; both whitespace checks passed and Git was clean after delivery. The final documentation commit only records these hashes in evidence/daily/T006.md and today's same two reports, plus this report-entry input. No functional source/check changed after the passing gates; no extra test run was needed. Obtain this documentation SHA with git log -1 --format=%H -- docs/daily/2026-10-25_technical.md.

Actual final state: project in_progress, active=null, completed mandatory=5, T006 awaiting_review, next=null because of the owner gate, daily_tasks[2026-10-25]=[T005,T006]. First T006 failure, exact failed source and all rerun/negative evidence remain intact. Final combined unit regression passed 543,428 vectors, separate ALU acceptance 234,804 and RF acceptance 20,738 rows; repeated seeds are not extra unique coverage. No formal, full CPU, routed timing, physical hardware or ASIC acceptance.

Owner action is review docs/REGFILE.md and evidence/daily/T006.md, then the owner may run python -B scripts/harness.py approve T006 --confirm-owner-review. BACKLOG marks T006 human_approval_required and AGENTS.md reserves approval; the agent has not invoked it or started T007. Generic continuation is not approval. After persisted owner review, read this latest handoff and required files, inspect actual runtime controls/clean Git, run daily --supervised and next, then begin T007 branch comparison/target math/JALR masking. Continue sequential tasks in the attended session while budget permits, respecting future gates; no calendar wait or quota exception. Unattended automation remains disabled under unrestricted runtime. Do not re-request the confirmed Basys 3/Vivado path or previously recorded T002/T003 approvals.


---

<!-- entry:72b4af0ce78145b3d4d399d57506550d9a2a05d671ad96be8d1b0302a98bbfbc -->

# Owner reviewed T006 and authorized its approval command

The owner answered ‘Reviewed: approve T006 and authorize the command’ to question call_ab2669f837ed4a1ebe438fcf87a79810, after the concrete delivery 4f67b3c/handoff 9babc92. This is an explicit exception to the agent's prohibition for this exact command only: python -B scripts/harness.py approve T006 --confirm-owner-review. Provenance is evidence/owner_reviews/T006-2026-10-25.json; execution result is evidence/owner_reviews/T006-2026-10-25-command.json. Applied the authorized owner action, which promotes T006 from awaiting_review to completed and records the reviewed final receipt; it does not rerun tests, reset attempts or change evidence.

T006's automated acceptance remains attempt 2; first failure and all prior logs stay intact. The project now has 6/41 mandatory completed, no active task, and T007 is first dependency-ready. Review and commit this approval state/provenance/report checkpoint from clean baseline 9babc92, then begin T007. Implement only branch comparisons and target math against the unchanged reviewed architecture, including JALR bit-zero clearing followed by target alignment and not-taken branch behavior. No new architecture/ISA/clock/reset proposal, blanket approval, installation or hardware authorization is implied. Continue sequential attended tasks within the session budget, respecting later owner gates.


---

<!-- entry:26477f14f8dd4a5f9d7fa38606589334b80c610ea48144b7f2b817f3f7b88cca -->

# T007 implementation prepared after committed owner review

T006's explicit owner approval/provenance was applied and committed as 4339813, then T007 began from clean Git. Added rtl/core/branch_unit.sv and dv/unit/test_branch.py/tb_branch.sv, docs/BRANCH.md and dv/lint/branch_lint_top.sv. Updated only unit manifest/registry and controller state/backlog; existing package/decoder/ALU/RF/architecture/XPR/constraints are unchanged.

The combinational interface accepts op_t, PC, rs1, rs2, immediate and returns target[31:0], taken, misaligned, supported. All six predicates, PC-relative branches/JAL, rs1-relative JALR, modulo wrapping and bit-zero clearing-before-alignment are implemented. Untaken branches expose zero target/bad flag; taken bad targets retain condition/target for caller fault handling. Caller must gate bad redirects and construct precise age-ordered faults; this unit does not halt or retire.

Independent tests use predicate tables, integer modulo/division and original decoded inputs. All 12-bit JALR offsets, signed small domains, full-width edges, both branch outcomes/alignment bins, JAL boundaries, wraparound, irrelevant operands and all unsupported IDs are replayable with seeds 1/20261025. Six oracle tests and actual wrong-answer/empty-file simulations are required. The synthesis probe independently captures operand words, reducing physical probe ports while the direct combinational DUT is fully simulated. No new clock domain or architectural state.

Run finish T007 --evidence evidence/daily/T007.md to reserve attempt 1 and execute lint/test-branch plus whitespace checks. Outcome pending. Append final results, preservation and commit here; then continue to the next ready task within the attended budget. Current unrestricted permissions do not authorize unattended operation, downloads/installs, global changes, pushes or FPGA programming. Formal, full CPU, timing and physical evidence remain separate.


---

<!-- entry:2398395b06cedf7819c5ba2bbbb3216f25eb5827ea1197b7b4a7603e02a5f69e -->

# T007 completed on first acceptance attempt

All four outer commands passed, exit 0. Receipt evidence/runs/T007/attempt-1-20261026T042652163468Z.json. Lint receipt evidence/toolchain_runs/lint-20261026T042652619549Z.json has 17 checks/10 commands: branch synthesis probe 25.000 s, warning/error/latch/black-box free with selected structural checks passing; retained decoder/ALU/RF/fixture syntheses pass and the intentional latch remains rejected. No test weakening, retry or scoped DUT bug.

Unit receipt evidence/toolchain_runs/branch-20261026T042926105469Z.json has 17 checks/10 commands. Seeds 1/20261025 each compared 126,968 complete target/taken/misaligned/supported vectors, total 253,936; times 3.078/3.016 s. Per seed: 6,144 exhaustive signed small-domain, 46,080 edge-cross, 65,536 JALR full-immediate/base pairs, 120 JAL walking/boundary, 8,192 random and 896 unsupported cases. Every one of 39 declared operation/condition/alignment/wrap/JALR-odd bins hit. Six anchored oracle tests and both actual wrong-answer/empty-vector rejection checks pass. Source hashes stayed fixed; exact argv/status/output/exits and source/vector/WDB/Tcl/argument hashes are retained. Pins unchanged: Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2 and Vivado/XSim 2025.2/SW build 6299465.

Files: new rtl/core/branch_unit.sv, dv/lint/branch_lint_top.sv, dv/unit/test_branch.py and tb_branch.sv, docs/BRANCH.md, evidence/daily/T007.md and receipts/audit/report entries; updated manifest/registry/state/backlog, README and today's same two reports. Updated REGFILE.md and appended T006 evidence to reflect the already-authorized approval commit 4339813; older review entries remain historical. No existing production RTL/architecture/XPR/constraints/kit changed. Completion audit is evidence/t007-complete-2026-10-25.json. Branch is routed into regress, but the combined route after this addition has not yet been rerun; the earlier 543,428-vector review-boundary regression covers only its recorded four units.

Project has 7/41 mandatory completed and no active task. Review/diff-check/commit T007, then begin T008 load/store byte formatting in the same attended session; record the T007 SHA in the next entry. Implement all load/store widths, little-endian byte strobes for reads/writes, extension and misalignment gating with independent byte-array/neighbor-preservation tests. Keep original-byte address ownership in the caller, no split/misaligned requests, no early memory effect. No architecture/permission change. Formal, complete CPU/pipeline/fault ordering, routed timing, hardware and ASIC remain NOT RUN. Continue sequential ready work within attended budget, no calendar hold.


---

<!-- entry:1869d808262f361acac142b4a35b3e40056566e9ba77b2453b8d478f06e8a6f0 -->

# T007 delivered; T008 formatter prepared

T007 delivery c4619b176c2eb1c899f4d33b2002c833492d3910 passed its functional/EDA acceptance and T008 began from a clean worktree. The closing T006 evidence note inadvertently introduced a trailing blank line; the shell continued past that post-test whitespace error. Corrected immediately in documentation-only commit a239409, reran both whitespace checks successfully, and changed subsequent commit orchestration to subprocess check=True so failure stops it. No verified RTL changed and no Git history was rewritten. T008 remains the sole active task.

Added rtl/core/lsu.sv: op_t + byte_offset[1:0] + store_data/read_word[31:0] -> load/store data[31:0], byte enables[3:0], write/misaligned/supported. Handles all five loads/three stores, little-endian lanes, sign/zero extension and natural alignment. Both read and write byte enables are defined; misaligned operations retain supported but suppress all effect metadata. The caller retains the full ORIGINAL byte address and creates age-ordered faults before any request. No bus timing or memory effect is implemented here. No existing production RTL, ISA/EEI, clock/reset or memory map changed.

New dv/unit/test_lsu.py uses byte arrays and signed byte conversion; tb_lsu.sv compares every output and independently applies DUT byte strobes to verify neighbor preservation. Six fixed tests plus all byte values/lane patterns, halfword sign/walking cases, word walking/complements, edge crosses, random inputs and unsupported IDs are seeded 1/20261025. Wrong-answer/empty-file actual runs remain mandatory. Added docs/LSU.md and dv/lint/lsu_lint_top.sv capture/multiplex probe, plus manifest/registry/regress route.

Next finish T008 --evidence evidence/daily/T008.md reserves attempt 1 and executes lint/test-lsu plus whitespace gates. No pass claimed yet. Append exact results and commit, then continue dependency-ready work only within attended session budget. Runtime remains unrestricted, unattended disabled, with no new tool installs, global changes, scheduling, pushes, deletion or FPGA programming. Formal, CPU/pipeline, actual bus effect ordering, timing, physical hardware and ASIC remain separate.


---

<!-- entry:a31e3e80c65ad751f9ac68ad3660c8c674530c4d286ecb7ad5d9e76b256ed2c6 -->

# T008 first-attempt failure retained; explicit-width repair

Receipt evidence/runs/T008/attempt-1-20261026T043415368034Z.json recorded lint FAIL, test-lsu PASS and both whitespace checks PASS. Vivado raw synthesis exit 0 was correctly rejected for WARNING Synth 8-3936: internal shifted signal trimmed from 32 to 16 bits. All functional comparisons already passed, 44,872 vectors per seed, but that cannot override warning-sensitive lint. Full first lint/unit JSON and exact source are preserved; evidence/failed_sources/T008/attempt-1/lsu.sv matches the original unit-run source SHA.

Repair narrows shifted to 16 bits and selects explicit slices for all four byte offsets. Halfword legal paths and byte lanes retain exactly the same behavior; no oracle/test/check, severity filter, Tcl/timeout or architecture change. Next finish uses attempt 2 of 3 and reruns every required gate. The task stays active/failed until those actual results pass. Keep both October 25 reports and all failure evidence; no reset/reopen or unbounded budget. Runtime remains attended, no tool installs or hardware action.


---

<!-- entry:4462d5fa2d30eb930b297cd8701b244f155ec2e32984397879ed3a0dbc8f3a2b -->

# T008 completed on second acceptance attempt

Final receipt evidence/runs/T008/attempt-2-20261026T043734414814Z.json: lint, test-lsu and both whitespace gates PASS/exit 0. First failed receipt/source remain intact; no test or warning suppression. Explicit 16-bit slice selection removed Synth 8-3936. Lint receipt evidence/toolchain_runs/lint-20261026T043734800085Z.json has 19 checks/11 commands, LSU synthesis 25.313 s with zero warnings/errors, no latches/black boxes/selected structural violations. Other units and intentional latch rejection pass.

Unit receipt evidence/toolchain_runs/lsu-20261026T044012923687Z.json has 17 checks/10 commands. Seeds 1/20261025 each checked 44,872 full output/merged-neighbor vectors, total 89,744; times 2.734/2.719 s. All 33 defined lane/misalignment/unsupported bins hit. Per seed: 6,272 edge crosses, 32,768 random, 3,072 all-byte values, 456 halfword patterns, 512 word walking/complements and 1,792 unsupported inputs. Six fixed byte-array oracle tests and both actual wrong-answer/empty-file gates pass. Exact source/vector/WDB/Tcl/argument hashes and full command evidence retained; source drift guard passed. Pins unchanged (Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2, Vivado/XSim 2025.2/SW build 6299465).

Changes: new lsu.sv, direct unit bench/oracle, synthesis probe and LSU.md; manifest/registry/state/backlog, README, task evidence, source archive, run records, audit and today's same two report files. No prior production RTL/architecture/XPR/constraints/kit changed. Audit evidence/t008-complete-2026-10-25.json binds delivery sources and preservation. The full regress route includes branch/LSU but its combined execution after these additions is NOT RUN; only the recorded T006 four-component suite has that full regression result. New branch/LSU required unit gates have actually passed. No CPU/bus sequencing, formal, routed timing, hardware or ASIC result follows.

Current mandatory completion is 8/41 with no active task. Inspect diff and commit using fail-fast whitespace checks, record its SHA, then next ready task is T009: Python instruction/data memory behavior models, fixed latency >=1, one outstanding request, stable stalled payloads and effects only on successful response acceptance. Reset cancels transactions but retains memory. Any tests of these models must be labeled model behavior, not integrated CPU/RTL bus validation. Continue only as the attended session budget permits; preserve exact handoff if stopping. No new install, global change, unattended automation, push or programming authorization.
