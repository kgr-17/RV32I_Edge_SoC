<!-- entry:5e31f721651cb9261c55e37d2f923da9cf15c5c7889a63ec2f8ec6fc6f4cb16a -->

# Technical engineering handoff - 2026-10-16 (America/Los_Angeles)

## 1. Phase and selected task

Second attended engineering working day, P0, T002: architecture proposal and owner review. Calendar date is October 16, not a backfilled October 15 session. The latest previous handoff was 2026-10-14 and was read before work. T001 was completed; Git was clean at session start, no active task existed, and today had no daily claim. begin T002 succeeded and reserved today's only primary task. This entry precedes final gate execution; append actual final results.

## 2. Overall status

No CPU/peripheral RTL, XDC, source integration, firmware, synthesis, timing, physical hardware or ASIC result exists. The owner already confirmed Basys 3 and Vivado was located on day 1. Initial architecture proposal v0.2 is now concrete but NOT APPROVED. Project state remains in_progress, not completed. The backlog now has 45 tasks: 41 mandatory, 4 optional, including restored later interrupt milestones.

## 3. Microarchitecture and technical decisions proposed

Single-hart RV32I 2.1, 32-bit little-endian, IF/ID/EX/MEM/WB, EX branch resolution and WB retire trace. Source baseline is the ratified 20240411 manual snapshot; official RISC-V/EEI and Digilent documentation were fetched with explicit owner authorization. This authorizes documentation only, not packages/tools/IP.

The board manual confirms 100 MHz W5; proposed timing period is 10 ns, with no measured closure. Active-high synchronous core reset zeros GPRs and valid/protocol/fault state; wrapper release synchronized; warm-reset RAM/ROM retained, shared local interface reset cancels transactions. No fabric clock domain is introduced.

Native I/D request/response buses permit one outstanding each, at least one-cycle response, stable offered payload and no same-edge response/new-request replacement. Data requests carry original byte address plus lane enables for reads AND writes; reads return the containing aligned word. Successful response acceptance is the single side-effect point. Stale offered fetch requests drain under stable-valid rules and their responses/faults are discarded.

Priority: reset > oldest_fault > memory_hold > redirect > load_use > advance. Older WB retires once while MEM holds younger stages. Forward loads from WB only. Hold/replay operands safely after a producer's WB event has vanished.

Initial EEI: precise sticky fault/halt-until-reset output, including ECALL/EBREAK and illegal/access/alignment cases. No initial machine-mode CSR handler or return. Full base-instruction target includes all 40 mnemonics, legal HINTs and conservative full-drain FENCE. The later requested interrupt feature is still mandatory, with T044 owner review and T045 implementation of a new trap/CSR/IRQ revision before final FPGA execution.

## 4. Changes completed

Replaced the ambiguous v0.1 active specification with v0.2 proposal. Added machine-readable contract, explicit core ports, memory protocol/reset/fault ordering, address permissions and peripheral register behavior. Added owner decision table A1-A10 and proposed ADR-0007..ADR-0012. No owner approval was created.

Added a structural consistency checker and 16 positive/negative mutation tests. These check the artifact rather than a DUT. Strengthened T002's required files and commands with checker/tests; retained its original validation command and human-review requirement.

Added R-IRQ traceability and future T044/T045 because the original objective required later interrupt support but it was missing from the backlog. T043 depends on T045, physical acceptance includes IRQ firmware, and T040 directly depends on every mandatory task. Optional AXI4-Lite/DMA remain disabled and cannot block mandatory completion.

Clarified the stale AGENTS bootstrap-date sentence so it cannot reserve T001 forever on future days. Updated README, audit, reference verification status and boundary authorization to match actual evidence.

## 5. Exact files modified or added

- .harness/state.json
- AGENTS.md
- README.md
- docs/ARCH_AUDIT.md
- docs/ARCH_CONTRACT.json
- docs/ARCH_REVIEW.md
- docs/ARCH_SPEC.md
- docs/BACKLOG.json
- docs/DECISIONS.md
- docs/ENVIRONMENT_BOUNDARY.md
- docs/REFERENCES.md
- docs/VERIFICATION_PLAN.md
- evidence/arch_contract_check.json
- evidence/day2_start.json
- evidence/t002_inspection.json
- evidence/t002_sources.json
- scripts/check_arch_spec.py
- scripts/test_arch_spec.py

Also added for today's evidence/report workflow:
- evidence/daily/T002.md
- evidence/report_entries/day2-initial.json
- docs/daily/2026-10-16_technical.md
- docs/daily/2026-10-16_zh-CN.md

The final timestamped verification receipt and final report-entry files will be listed in the closing addendum. Original XPR, original kit, existing generated metadata, all prior-date reports and installed tools are unchanged. No unrelated file or home/global configuration was touched.

## 6. Critical interfaces and integration assumptions

38 named rv32_core ports are documented in Markdown and JSON; exact names/widths/directions are compared by the checker. Protocol reset assumes both endpoints reset together. Isolated core reset is not supported by local_mem_v1. fault_code is a project-defined diagnostic, not mcause. Faulting instructions do not produce successful retire events. Successful MEM effects may precede their ordered WB trace, after all older faults have been excluded; the scoreboard must correlate response and later trace exactly once.

ROM: 0x00000000..0x0000ffff, I-fetch/D-read, no writes. RAM: 0x00010000..0x0001ffff, D-read/write, no execution. UART at 0x10000000..1f, GPIO 20..3f, timer 0x10000100..10f. Peripheral subregisters, selected-byte side effects, reset values, read-only write errors and collision priorities are explicit. These are proposed software contracts, not verified hardware.

Contract SHA-256 at submission: 403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03. This binds the proposed 38 ports, 40 instruction names and 22 requirement IDs. The checker will repeat the hash in the final receipt.

## 7. Commands, results and versions

Startup commands daily --supervised, validate/status/next and begin T002 succeeded; evidence/day2_start.json records exact command output and starting commit. No production date override or quota bypass was used.

Preliminary python -B scripts/check_arch_spec.py passed against the earlier 21-requirement draft. Preliminary python -B scripts/test_arch_spec.py passed 16 tests, exit 0, 0.015s. R-IRQ/backlog additions happened afterward, so final finish must execute all current required gates; do not treat the preliminary result as final verification.

Final commands configured for T002:
- python -B scripts/harness.py validate
- python -B scripts/check_arch_spec.py
- python -B scripts/test_arch_spec.py
- automatic git diff --check and git diff --cached --check

Versions executed this session: Python 3.9.13 and Git 2.48.1.windows.1; exact paths/output are in evidence/t002_inspection.json. Installed tools were not changed. The prior Vivado 2025.2 startup/part probe remains day-1 evidence; no Vivado process was launched for day 2.

## 8. Verification coverage and gaps

Structural checks include target/config agreement, pinned ISA inventory, interface table drift, one-clock/reset/bus rules, address bounds/overlap, executable reset PC, register containment, fault code uniqueness and task traceability. Negative tests corrupt those inputs to show rejection. They do not prove a microarchitecture, decoder, transaction FSM or EEI implementation. The existing 26 harness tests remain their prior recorded evidence; harness source was not changed today.

All 22 implementation requirements remain NOT RUN. Future tests must specifically cover oldest fault vs younger store, older redirect vs younger fault, no repeated WB retire during MEM hold, stale operands, killed stalled fetches, load-to-x0 side effects, ignored FENCE fields and reset cancellation.

## 9. Timing, synthesis, FPGA and ASIC

NOT RUN. No resource, power, Fmax, timing slack, setup/hold, coverage percentage, proof bound or hardware observation is asserted. Logical ROM+RAM capacity arithmetic is planning only, not a synthesis utilization result. No physical FPGA programming or hardware access occurred.

## 10. Issues found and reasoning

The v0.1 draft did not define exact ports, reset policy, response ownership or fault age. Simulator-only errors and avoided misalignment would not establish full RV32I behavior. A stalled wrong-path request cannot simply disappear under ready/valid rules. An old WB instruction must not retire repeatedly during a global younger-stage hold. The v0.2 proposal makes these rules explicit and adds future independent tests.

Later interrupt support was absent from the original 43-task migrated backlog; T044/T045 restore that requirement and preserve review before CSR/IRQ architecture changes. No implementation was silently claimed or expanded today.

No implementation bug is claimed to be fixed: these are specification gaps and planning defects. Preliminary checks reported no current document errors; final gate still pending at this entry.

## 11. Unresolved technical issues

Owner must accept or revise the fatal initial EEI, bus/reset coupling, conservative stalls, map/register semantics and MEM-effect/WB-trace rule. Full pin/XDC review and hardware revision checks remain T025. Existing XSim compatibility and executable RTL/CI gates remain T003; other simulators/formal/ASIC tools are still missing/unverified.

The controller currently has owner reopen for blocked tasks only; should the owner reject an awaiting_review proposal, do not bypass state or reuse its old receipt. Establish an explicit owner-controlled revision/reverification workflow before implementing revisions. This is a workflow limitation, not permission to approve the design.

## 12. Dependencies, authorization and blockers

No current environment blocker prevents an attended documentation task. Actual session permissions remain unrestricted (danger-full-access / never); unattended automation is still disabled. Only official documentation reads were newly authorized. No package install, downloads of tools/IP, scheduler, remote change or hardware programming is authorized by this review.

T002 must end awaiting_review if automated checks pass. That is not completed acceptance: human review is outstanding and T003 remains blocked by dependency. No task after T002 may be started in this session.

## 13. Git branch and commit

Branch: engineering/bootstrap. Verification base: c3035b977a5eb7178bd58a8683a8ffe42cfb8493 (day-1 tool discovery). Original baseline: 8f16054b24a9d50021f8a805f7f0d78435206daa. Recoverability was preserved; all 23 original file hashes were checked again this session. The actual architecture delivery commit will be added after commit in a same-day report entry.

## 14. Next recommended task

First: owner reviews docs/ARCH_REVIEW.md and the exact v0.2 proposal/receipt. If approved, T003 is next on a new eligible day: establish real lint/simulation/CI/toolchain gates, testing existing XSim rather than presuming compatibility. Do not begin T003 before approval. If revisions requested, preserve all findings and reverify the revised proposal through an explicit owner-controlled workflow.

## 15. Next-session instructions

Read this report including final appendices, AGENTS, boundary, ARCH_SPEC, ARCH_CONTRACT, ARCH_REVIEW, VERIFICATION_PLAN, BACKLOG and state. Run the supervised daily entrypoint and inspect Git status. Recover T002 only if active/failed. If awaiting_review, stop for the owner decision and do not call approve/reopen/enable/authorize. Board/Vivado location are already known; do not ask again. No October 15 report is backfilled because no engineering run was recorded that date. Keep exactly two reports for each actual execution date, including blocked days. Do not start another primary task on October 16.


---

<!-- entry:f47b5ca2d3390722fd194950a8c0d0b3c77c4aadb9127b77ba1f0deb149c73c1 -->

# Final T002 gate result - ready for owner review

T002 automation completed on attempt 1 and transitioned to awaiting_review, NOT completed. Receipt: evidence/runs/T002/attempt-1-20261017T034202692993Z.json. All five required commands returned exit 0:

- python -B scripts/harness.py validate: valid 45-task plan/state.
- python -B scripts/check_arch_spec.py: document consistency PASS, 38 ports / 40 instructions / 22 requirements, no errors.
- python -B scripts/test_arch_spec.py: 16 tests in 0.013 seconds, OK.
- git diff --check.
- git diff --cached --check.

Final contract SHA-256: 403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03. The receipt's checker stdout binds this exact proposal. No automated test or checker is an owner architecture approval.

evidence/t002_final_state.json confirms active=null, owner_reviews empty, T002 attempts=1, no next eligible task, all original 23 files unchanged, prior daily reports byte-for-byte unchanged and exactly two October 16 reports. Current project status is in_progress: 1 of 41 mandatory tasks completed (T001), one awaiting_review (T002), 39 mandatory pending, 4 optional pending/disabled. T003 cannot start yet.

The closing additions after the initial file list are this entry input evidence/report_entries/day2-final.json, evidence/t002_final_state.json and the timestamped T002 receipt. This updates the same two dated reports and T002 evidence with final results; all previously recorded findings are preserved.

Owner must review ARCH_REVIEW.md A1-A10, especially the initial fatal EEI with a later reviewed IRQ revision, synchronous/shared reset, memory handshake/byte enables, priority and side-effect/retire timing, and the proposed software map. If accepting the exact proposal and receipt, only the owner runs:
python -B scripts/harness.py approve T002 --confirm-owner-review

No such command was executed by this session. Do not start T003 today or implement RTL pending review. Tool/package installation, scheduling, programming, new domains and external publication were not authorized. Actual unattended execution remains disabled. RTL/ISA simulation, formal, FPGA implementation/timing/hardware and ASIC are NOT RUN.

Next step is the owner review, not another implementation task. The proposal/evidence will now be committed, and the actual delivery commit recorded in a separate same-day documentation entry. The verification base remains c3035b977a5eb7178bd58a8683a8ffe42cfb8493.
