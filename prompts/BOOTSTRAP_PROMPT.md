# Current bootstrap instruction

The active project is C:/RV32I_Edge_SoC. Bootstrap T001 is already reserved; read
root AGENTS.md and the latest technical handoff. Do not bootstrap the original
kit again, create a second project, or start a second task today. The old prompt
below is retained only for background.

# Paste into Codex once

You are starting the RV32I Edge SoC portfolio project in this repository. Read AGENTS.md and all listed project contract documents. FIRST run `python3 scripts/harness.py validate` and `status`, inspect docs/BACKLOG.json and git status. Summarize the frozen scope, major risks and tool availability without changing architecture. Then implement exactly ONE eligible task using `prompts/DAILY_CODEX_PROMPT.md`. Follow single-task daily budget, use a self-checking test, record evidence, and stop. If prerequisites/tools/decisions block the task, report BLOCKED with concrete steps; do not bypass any gate, assert passing tests not run, or implement future tasks.
