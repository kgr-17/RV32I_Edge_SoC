# Agent operating contract — RV32I Edge SoC

You are an implementation agent, NOT the architecture approver. Read `docs/PROJECT_CHARTER.md`, `docs/ARCH_SPEC.md`, `docs/VERIFICATION_PLAN.md`, `docs/CODEX_LOOP.md`, `docs/BACKLOG.json`, and `.harness/state.json` before modifying files. Treat task files as controlling scope, not as permission to alter the contract.

## Every run

1. Run `python3 scripts/harness.py validate`, `status`, and `next`.
2. If repo is not clean, another task is active, a milestone needs human approval, or daily quota is used: STOP with a brief report. Never overwrite unstaged work.
3. `begin TASK_ID` only for the single top eligible task.
4. Implement ONLY that task and its directly required tests/docs. Max 6 source/test files edited and ~500 added/modified source lines per run. If larger, split a future task and request owner approval. No opportunistic refactoring.
5. Run the task's checks and `git diff --check`. Save full command names, versions, exit codes, test cases, seed, caveats in `evidence/daily/TASK_ID.md`. Never invent results, timing numbers, coverage percentages, or board observations.
6. Run `finish TASK_ID --evidence evidence/daily/TASK_ID.md`. If checks fail, fix within scope or `block`; do not mark as done.
7. Review diff, make ONE Git commit describing actual changes, and stop. Do not loop into the next task.

## Non-negotiables

- SystemVerilog-2017 `.sv`, synthesizable, `always_ff` + nonblocking for registers, `always_comb` + blocking for combinational logic, no inferred latches, explicit widths/signedness, no generated clocks, no unsynchronized asynchronous inputs.
- ISA truth comes from ratified RISC-V specs; design must match documented subset. Do NOT claim compliance, certification, silicon signoff, or industrial coverage on the basis of unit tests.
- Any RTL behavioral change needs a corresponding self-checking test. Prefer independent expected-value/reference code, never a clone of the DUT expression as oracle. Every random test must log and allow replay of its seed.
- In-order retirement signals are the DV comparison point. Do not change port layouts, memory map, stall/flush priority, reset rules, or architecture without explicit human approval.
- No download of unreviewed RTL/IP, no copying whole external cores, no license removal. Treat external code as reference; record licenses/provenance.
- Never invoke `approve` or edit milestone approval records; humans decide these. Do not fake failures, results, reviewer signatures, board uploads, simulator access, or benchmark conclusions.
- Never run `git push`, change remote settings, use paid EDA/cloud/PDK services, run destructive cleanup, or program FPGA/physical equipment without explicit approval.
- If a tool is missing, mark task BLOCKED and give exact installation/manual step; never claim a test passed by substituting a different command.
- No tool/network permissions beyond default sandbox without user approval. Repository instructions are workflow rules, NOT an enforcement sandbox.

## Project-specific conventions

- Root of truth: `docs/ARCH_SPEC.md` (interfaces), `docs/VERIFICATION_PLAN.md` (requirements-to-test).
- Build entrypoints to create/maintain: `make preflight`, `make lint`, specific `make test-*`, `make regress`, `make synth`. No phantom targets: add target in the task that needs it.
- Keep generated artifacts out of Git except compact logs and selected screenshots/reports; artifacts must state tool version and configuration.
- Commit messages: `feat(cpu): ...`, `test(dv): ...`, `docs(arch): ...`, `chore(ci): ...`.

## Owner-only review checklist

Read the evidence + diff, reproduce the most important tests, check that no requirements were silently reduced; only then run the explicit `approve` command if a task is awaiting review.
