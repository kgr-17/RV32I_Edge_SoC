# RV32I Edge SoC — Codex Engineering Kit

**Status: specification + harness only; NO CPU RTL or FPGA/ASIC results have been implemented or measured.**

Goal: build a 5-stage RV32I in-order CPU, a small FPGA SoC on Digilent Basys3, and a repeatable pre-silicon DV/ASIC exploration workflow. This is a portfolio project, not a tapeout-ready chip.

## Quick start

```bash
cd riscv_edge_soc_codex_kit
python3 scripts/harness.py validate
python3 scripts/harness.py status
python3 scripts/harness.py next
```

1. Read `docs/PROJECT_CHARTER.md`, `docs/ARCH_SPEC.md`, `docs/VERIFICATION_PLAN.md`.
2. Open this directory in Codex. Codex automatically reads root `AGENTS.md`.
3. Paste `prompts/BOOTSTRAP_PROMPT.md` in Codex for the first session.
4. For each subsequent session, use `prompts/DAILY_CODEX_PROMPT.md` (or set up a supported scheduled task for this repository).
5. **One task per run**, with recorded tests, reviewable diff, and explicit stop conditions.
6. Owner should review milestone gates and merge only validated changes. No automatic board programming or ASIC purchases.

## Commands

- `python3 scripts/harness.py next` — get next dependency-ready task
- `python3 scripts/harness.py begin T001` — reserve ONE daily task
- `python3 scripts/harness.py finish T001 --evidence evidence/daily/T001.md` — run required checks; close or queue owner review
- `python3 scripts/harness.py approve T006 --confirm-owner-review` — **OWNER ONLY**, after review gate
- `python3 scripts/harness.py block T007 --reason '...'` — mark current item blocked without false pass
- `python3 scripts/harness.py status` — progress dashboard

`docs/BACKLOG.json` is the immutable plan for a session. Any changes to scope/acceptance criteria require owner approval in a separate decision note.

## Schedules

A daily Codex task must be configured separately in a compatible ChatGPT desktop / Scheduled workflow; these files alone do not schedule anything. Desktop project scheduled runs need your computer powered on and the app running. Web scheduled tasks cannot work directly in a local folder. Use a dedicated project checkout for unattended runs; isolated worktrees require integration/merge before the next run sees the changes. See `docs/CODEX_LOOP.md`.

## Scope truth table

| Capability | Status now | Exit criterion |
|---|---|---|
| RV32I CPU | NOT STARTED | instructions tested against independent reference |
| Pipeline hazards | NOT STARTED | directed + randomized tests |
| Basys3 bring-up | NOT STARTED | board log + physical evidence |
| ASIC PPA | NOT STARTED | reproducible synthesis/STA reports with constraints/PDK |
| Architectural certification | NOT CLAIMED | compatible config + supported ACT4 executions |

## Audience

Materials are bilingual: engineering directives in English for Codex; explanation and career mapping in Chinese. Official standards/tool documentation supersede this plan when conflicts arise; record the reason and seek architectural approval before changing accepted interfaces.

## Additional guides

- `docs/GETTING_STARTED_CN.md` — full Chinese setup and scheduling workflow.
- `docs/CAREER_PORTFOLIO.md` — keywords, evidence and interview questions.
- `scripts/test_harness.py` — disposable Git repo self-check (does not test CPU RTL).
