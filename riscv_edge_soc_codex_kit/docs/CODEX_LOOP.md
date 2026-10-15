# Harness / Loop Engineering contract

## Why not `while true: codex ...`

A continuous agent that chooses its own features, edits architecture, marks tests green, and immediately takes another task can silently diverge. This harness creates a **bounded, inspectable single task/run**. Persist state in files and Git, not chat memory alone.

## State machine

`todo → in_progress → done` after automated checks, OR `todo → in_progress → awaiting_review → done` for owner milestone gates. Any `in_progress` may transition to `blocked` on honest failure. A blocked task halts its dependents; it does not silently jump to unrelated downstream features.

## Boundary matrix

| Boundary | Agent may do | Owner gate / forbidden |
|---|---|---|
| Scope | One dependency-ready task/run | Changes to ISA, memory map, buses, acceptance criteria |
| Duration | One scheduled invocation; stop after commit/report | Infinite restart/retry loops, recursive self-prompting |
| Code | RTL + test/docs for selected task, ≤6 files/~500 changed source lines | Broad refactor, cloning whole existing cores |
| Test | Run specified checks, record versions/output/seed | Invented green tests, lowering checks to pass |
| Git | Commit local diff | Push/delete/reset history without approval |
| Environment | Existing sandbox and installed free tools | Network/broad filesystem/paid EDA permissions |
| Hardware | Prepare bitstream, user instructions | Program external board without owner consent |
| ASIC | Synthesis/PDK reports in approved environment | Order fabrication, publish falsely as silicon |
| Review | Explain design decisions and risks | Owner milestone `approve` command |

## Daily deterministic procedure

1. Verify clean checkout; `validate`, `status`, `next`.
2. Choose top eligible ID, `begin ID`; refuse second start the same local calendar day.
3. Read specification and task acceptance, produce concise plan, implement change+test.
4. Execute required commands; save evidence file `evidence/daily/ID.md` and explain test oracle.
5. `finish ID --evidence ...`; blocked if automated checks fail. Never weaken checks to make them pass.
6. Commit source, tests, evidence, harness state. Report task ID, test results, risks, next task. STOP.
7. On `awaiting_review`, only owner can review and call `approve ID --confirm-owner-review`; agent must wait.

## Persistent records

`AGENTS.md` = behavior contract, `docs/ARCH_SPEC.md` = design contract, `docs/BACKLOG.json` = planned tasks, `.harness/state.json` = realized state, `evidence/daily/` = verification claims, Git commits = auditable changes.

## Scheduling notes (as of 2026-10-14)

Codex-style scheduled tasks in ChatGPT desktop can use local repositories/worktrees, but require the desktop app running and local project available. Web scheduled tasks cannot edit a local folder directly. For uninterrupted sequential updates, use a dedicated clone checked out for the schedule. If using a new worktree per run, a human must integrate the prior run before next run assumes it exists. Check each scheduled task's permissions and review early runs.

## Suggested cadence

Daily: 1 task, ≤1 commit, report. Weekly: owner reviews progress/diffs and coverage gaps; adjust backlog only via architecture note. Milestones require explicit approval. No promised completion date.

## Honest limits

`AGENTS.md` and this script guide authorized behavior but do **not** create a security boundary against a model with unrestricted filesystem access. Real protections are sandbox/approval settings, branch protection, restricted credentials and human oversight. The script checks existence/results; it cannot validate the semantic correctness of RTL by itself.
