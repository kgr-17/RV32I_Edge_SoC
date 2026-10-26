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
