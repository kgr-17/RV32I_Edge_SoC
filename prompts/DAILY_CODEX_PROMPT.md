# Superseded entrypoint

Use prompts/DAILY_RUN.md in the official project root. The older kit prompt below
is historical context only; do not use its Python3/Make assumptions or discard
an interrupted task.

# Daily Codex execution prompt — paste into scheduled task or chat

Continue the existing RV32I Edge SoC repository as a bounded hardware engineering agent. Do not start a new project or optimize for quantity of code.

1. Read `AGENTS.md`, `docs/CODEX_LOOP.md`, `docs/ARCH_SPEC.md`, `docs/VERIFICATION_PLAN.md`, `docs/BACKLOG.json`, and `.harness/state.json`.
2. Run `python3 scripts/harness.py validate`, `status`, `next`, and `git status --short`. If another task is in progress, a milestone awaits owner review, working tree is dirty from someone else, or one task was already started today, STOP and report why.
3. Select exactly the FIRST dependency-ready task, run `python3 scripts/harness.py begin <ID>`, and implement only its specified deliverable, tests and minimal documentation.
4. Be a skeptical verification engineer: test the expected behavior independently, run commands specified in the backlog, and do not weaken existing checks. Save test versions, stdout/exit codes/seeds/known failures in `evidence/daily/<ID>.md`.
5. Run `python3 scripts/harness.py finish <ID> --evidence evidence/daily/<ID>.md`. If checks fail or tool missing, block with diagnosis and STOP. Do not call `approve`.
6. Review `git diff --check`, record any unavailable checks as NOT RUN, make one local commit for this task, and STOP. Do not push, change next task or invoke another run.

Final message: task ID, exact work done, PASS/FAIL/NOT RUN table of checks, evidence path, git commit hash if committed, outstanding risks and next unblocked task. If blocked, do not claim the feature is implemented.
