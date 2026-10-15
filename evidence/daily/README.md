# Daily evidence template

Each task produces `<TASK_ID>.md` like this:

```markdown
# Txxx — <title>
Date / branch / commit before changes:
Goal / scope:
Files changed:
Design rationale:
Independent oracle/testcases:
Tool versions:
Commands + exit code (PASS/FAIL/NOT RUN):
Random seeds and replay commands:
Known limitations / TODOs:
Proof/report/waveform paths (if generated):
Why this meets each acceptance criterion:
Manual tests needed and by whom:
```

Do not claim PASS until the command actually exited 0 and test results were checked. `make` existing with no test is not a useful quality gate.
