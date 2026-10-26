<!-- entry:211696ed2a3bbf76263c97d4687cc1b1fb921c9f6ceddf8c75703fd01cb2ea44 -->

# October 26 attended recovery: T009 memory models

Read the latest October 25 technical handoff and required project contract/state documents, inspected Git status, and ran daily --supervised. Actual UTC 2026-10-26 23:18 corresponds to America/Los_Angeles October 26. Recovered active T009 with begin T009, preserving its October 25 participation and adding October 26. No attempt had been consumed. T008 was committed as 075d738 (load/store formatting, 89,744 comparisons); prior-day report files are preserved. Runtime is still unrestricted danger-full-access/never; the harness is not a sandbox and unattended automation remains disabled.

Completed the initial model implementation and independent tests under dv/models/memory.py and dv/integration/test_memory.py; documented API in docs/MEMORY_MODELS.md. Shared ROM/RAM image, separate I/D outstanding slots, immutable request payloads, fixed positive latency, full aligned read data, byte masks, deferred successful stores, stable stalled responses, error suppression and shared-reset cancellation/retention follow the approved v0.2 contract. MMIO is deliberately outside this bounded model, not a memory-map change. No existing production RTL, XPR, XDC, kit or architecture modification.

The independent byte/event ledger has seeds 1/20261025 across I/D ports and latency 1/3/7, with per-case replay traces/coverage and source hashes. Directed tests check lanes, boundaries, stalled offers, response stability, reset phases, no duplicate/replacement acceptance and simultaneous independent bus occupancy. Four deliberately faulty models must be rejected. Registered test-memory and its regression route. Next execute harness finish T009 --evidence evidence/daily/T009.md, attempt 1/3, with real retained RTL lint and both whitespace gates. No pass is asserted until execution. Preserve all failures and append results to exactly today's two reports; do not restart the task or erase previous work. Model tests are distinct from future CPU/RTL bus simulation, formal, timing, hardware and ASIC milestones.


---

<!-- entry:6ee95e70f2a2d6b33b211253b4f6829251e47bc1c55853933b83b871313590e1 -->

# T009 attempt 1: retained failure and precise repair

Receipt evidence/runs/T009/attempt-1-20261026T231924185738Z.json: lint PASS, test-memory FAIL, unstaged whitespace FAIL, staged whitespace PASS. Memory receipt memory-20261026T232141538434Z.json records 11 tests with one failing stress subcase, seed 20261025/data/latency7. No edge mismatch occurred; the final empty-pending assertion found an unfinished transaction at the end of the testbench's N+5 drain. At cutoff there can be one accepted request plus one held offer, so completion needs at most two fixed-latency transactions and the no-replacement bubble. Corrected the bound to 2*N+3 with ready/allow forced high. All assertions, seeds, coverage and model behavior are unchanged. This repairs a testbench completion bound, not a CPU or memory-model functional defect.

Git whitespace also correctly rejected CRLF introduced by my registry serialization using Python's Windows default text translation. Restored LF bytes, with identical registry values and no whitespace-policy change. Archived exact first model/test/registry bytes in evidence/failed_sources/T009/attempt-1/inputs.zip and hash-matched them to the failed receipt. Existing 11 successful case traces and all diagnostics are preserved; the failing subcase did not save a complete trace and is reproduced by the same command/seed set. Next finish consumes attempt 2 of 3 and reruns the same required gates. No owner reopen, source suppression or fabricated pass.


---

<!-- entry:8812957994118a75432392cb68213d89b5228ec6c97a7f34af4d34fb1b363fd7 -->

# T009 completed and expanded regression passed

Attempt 2 receipt evidence/runs/T009/attempt-2-20261026T232236008595Z.json: lint, test-memory and both whitespace checks PASS/exit 0. Lint receipt lint-20261026T232236393311Z.json has 19 checks/11 commands. Memory receipt memory-20261026T232451515660Z.json has 11 tests, no failures/errors/skips, 0.750 s, no source drift. Both seeds (1/20261025), both I/D ports and latencies 1/3/7 passed all declared bins: 49,276 edges, 8,654 accepts exactly equal 7,487 completions + 1,167 reset cancellations. Four deliberate model defects were actually rejected. Source and 12 trace hashes retained. The failed first inputs ZIP/manifest and all logs remain intact; repair changed only the analytical drain bound and registry LF bytes, not model behavior or check requirements.

The expanded regression entrypoint was also executed: python -B scripts/verify.py regress PASS/exit 0, full nested results in evidence/t009-regression-2026-10-26.json. All seven subtargets pass. Six RTL components (fixture, decoder, ALU, RF, branch, LSU) compare 887,108 vectors in 12 seeded positive XSim simulations, with required actual negative rejection. The memory model separately repeats 49,276 edges and 11 tests. This closes the previously unexecuted branch/LSU/regression routing gap; repeated seeds do not expand unique coverage. Pins remain Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2, Vivado/XSim 2025.2/SW6299465. No tool installed.

Reviewed files: memory model, independent integration tests, MEMORY_MODELS.md, registry/state/backlog, README, task evidence, failure ZIP/manifest, run receipts, audit and exactly today's technical/Chinese reports. Earlier reports/RTL/architecture/XPR/XDC/kit remain unchanged. Audit evidence/t009-complete-2026-10-26.json binds current delivery and preservation. T009 is completed, no active task, mandatory total 9/41. Commit inspected files with fail-fast whitespace checks, record SHA, then begin T010 reference CPU. These are unit RTL simulation/structural synthesis and Python model results; integrated CPU execution, formal, routed timing, hardware and ASIC remain NOT RUN. Continue sequential attended work while session budget permits; do not run unrestricted unattended automation.


---

<!-- entry:71fa6ddce71e821234f00ea9a17d9fc4d303dfeac1b84415284a8e4bf71d53e7 -->

# T009 receipt-format check before delivery

The fail-fast staged whitespace gate rejected CRLF in the new memory JSON receipts, which were untracked during finish. It stopped the commit successfully. Preserved exact original bytes for all three receipts in evidence/failed_sources/T009/receipt-format/raw-receipts.zip, with raw and LF SHA-256 pairs in manifest.json. Converted only the JSON review copies to LF and asserted parsed-object equality. No test/model/check source, result field, source hash or trace hash changed. The complete original command streams are also retained in the harness/expanded-regression receipts. This is artifact formatting, requiring no repeated RTL test. Re-run both whitespace gates before committing.

Known tooling follow-up: the new memory evidence writer uses Windows default text newline translation. New generated review JSON files need LF normalization before staging, or a later verified serializer-only fix. Do not change Git whitespace policy or hide this difference. Existing verified source hashes still exactly match delivery sources. Original project files and all previous-day reports remain intact.
