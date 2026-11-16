# T043 FPGA implementation review

T043 passed all six registered verification gates and both whitespace checks on
2026-11-08, attempt 1. On 2026-11-15 the saved results were recovered, independently
audited and packaged. The task is **awaiting owner review**, with no active task.
This review supersedes earlier preparation status in this document's Git history.
No physical FPGA connection or programming has occurred.

## Final implementation

Target: Digilent Basys 3, `xc7a35tcpg236-1`, `basys3_top`, one `sys_clk` at
10.000 ns / 100 MHz. Source commit: `a7bf63dbba10f983aa670ba8959b8feeaa0e69b6`.
The canonical image uses the reviewed v0.3 CSR/MRET/timer-interrupt mode.

| Evidence | Final result |
|---|---|
| Routed setup WNS / TNS | +0.123 ns / 0; 0 failing of 7,683 endpoints |
| Routed hold WHS / THS | +0.013 ns / 0; 0 failing of 7,683 endpoints |
| Pulse-width slack | +4.500 ns; 0 failing of 2,619 endpoints |
| Routing | 5,892 / 5,892 routable nets fully routed; 0 errors |
| DRC | 0 violations |
| LUTs | 3,291 / 20,800 (15.82%) |
| Flip-flops | 2,554 / 41,600 (6.14%) |
| Block RAM tiles | 32 / 50 (64.00%) |
| Bonded IOBs | 36 / 106 (33.96%) |
| Physical inventory | 36 pins; 18 exact two-FF synchronizer chains / 36 ASYNC_REG FFs; 11 clocked reset copies |
| Vectorless power | 0.084 W total: 0.014 W dynamic + 0.070 W static; **Low confidence** |
| Conditional bitstream | Generated after setup, hold and DRC guards; header/part/payload validated |

These are native detailed routed reports, rather than the earlier route estimate
or unplaced synthesis timing. The worst setup path runs from
`soc/cpu/ex_stage/payload_q_reg[12]/C` to
`soc/cpu/next_fetch_pc_q_reg[15]/D`, with 9.589 ns data delay, 13 logic levels and
6.949 ns routing delay. Setup and hold margins are small; another source, tool or
constraint change needs fresh implementation and timing evidence.

## What changed and how behavior was protected

T043 implementation changes are already committed in `2494c66`, `eae2291` and
`a7bf63d`. The November 15 session changed documentation, evidence and daily
participation state only; it made no new RTL changes.

- `rtl/core/pipeline_core.sv` and `pipeline_cpu.sv`: factor internal payload,
  PC preparation, FIFO flow and serialized CSR control to remove redundant
  combinational control paths. Valid/reset/flush priority and external request,
  response, retirement and trap contracts remain independently checked.
  Generic stage defaults retain zeroed invalid payload; integrated internal
  stages explicitly choose the optimized payload behavior.
- The branch unit keeps its default masked untaken-target interface. The pipeline
  requests a parallel target candidate; actual taken, alignment, fault and flush
  qualification remain checked by independent tests and deliberate mutations.
- `rtl/soc/soc_fabric.sv`: derive RAM enables from the decoded transaction and
  select active addresses using registered pending state, avoiding unrelated
  peripheral-ready paths. Whole-RAM effects, reset cancellation, response errors
  and the early-store mutation remain checked.
- The canonical Basys 3 reset synchronizes both button transitions and uses
  initialized clocked reset distribution. Hold `btnC` for at least four clock
  edges to guarantee a core reset edge. Generic reset defaults preserve their
  prior behavior. Physical cell inventory and an asynchronous-reset mutation
  check the board-specific implementation.
- `fpga/basys3/build.tcl` uses flattened/rebuilt synthesis and explicit optimization
  without optional BRAM CE power lookahead that produced asynchronous-control
  DRC findings. Native stages remain bounded at 120 seconds each, under the
  registered 600-second composite ceiling. No timing exception, reduced clock,
  MAX_FANOUT property, DRC waiver or timeout-as-success was introduced.
- `scripts/fpga_build.py`, `fpga_checks.py` and `fpga_reports.py` bind actual
  sources, jobs, predecessor checkpoints, results and complete report artifacts.
  Strict native warnings, report contents, pins, CDC structure, power assumptions
  and binary bitstream metadata are checked. Existing XPR/XDC, memory images,
  architecture contracts and original kit remained unchanged during T043.

The final interrupt gate has 144 checks / 74 command records, including seeds
1 and 20261107, nine boot cases, a queued-consumer CSR serialization witness,
and actual faulty RTL variants. The branch gate includes 253,936 vectors with
seeds 1 and 20261025. The full regression runs 28 registered targets. Repeated
seed replays establish reproducibility, without claiming additional unique
coverage or exhaustive ISA proof.

## Reproduction and evidence

The already executed acceptance command was:

```powershell
python -B scripts/harness.py finish T043 --evidence evidence/daily/T043.md
```

Do not execute it again while T043 is awaiting review. Its immutable receipt is
`evidence/runs/T043/attempt-1-20261108T210906188089Z.json`. All of these commands
returned exit 0 / PASS against the same frozen source commit:

```powershell
python -B scripts/verify.py lint
python -B scripts/verify.py test-interrupts
python -B scripts/verify.py regress
python -B scripts/verify.py vivado-synth
python -B scripts/verify.py vivado-impl
python -B scripts/verify.py fpga-reports
git diff --check
git diff --cached --check
```

The FPGA commands require active authorized T043; the list documents the recorded
run, rather than authorizing a new run from the awaiting-review state. Each fresh
acceptance run creates its own synthesis and opt/place/phys_fanout/phys_placement/
phys_logic/phys_pin/route/reports chain. Preparation checkpoints were not reused.
Output, cache, logs and temporary paths stay inside this project.

Tools: Python 3.9.13; Git 2.48.1.windows.1; Vivado/XSim 2025.2 (SW build 6299465);
GNU GCC 13.4.0; ld 2.43.1.20241111; objcopy/readelf/objdump 2.39.0.20220819.
Vivado is at `C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat`; no PATH change.

Final artifacts: `build/T043/fpga-impl-20261108T212739021522Z/reports/artifacts/`.
The final `design.bit` header is dated **2026/11/08 13:31:04**, part
`7a35tcpg236`, payload 2,192,012 bytes. Its SHA-256 is:

`13f3639d2b01feded384a1316207a0ddb02fb5d4036bc399901fc87fd2aacbd9`

`evidence/fpga/manifest.json` binds 52 sources and 71 implementation artifacts.
Its SHA-256 is:

`de60d300cd9b267cca9c25f703b70ae2d5c8367864dc75712ca9c014202fb141`

The November 15 integrity audit is reproducible, before owner approval, with:

```powershell
python -B evidence/fpga/final-audit-2026-11-15.py
```

`final-audit-2026-11-15.json` records PASS: 45 tool receipts, three linked data
reports, 189 sources (181 matched exact source-commit bytes), 2,644 artifact
hashes and 32 protected baseline files. It checks the native checkpoint chain
and independently parses the final reports. Its workflow preconditions are
specific to this awaiting-review, first-attempt snapshot.

`evidence/fpga/T043-implementation-2026-11-15.zip` preserves 176 members, including
all 71 final implementation artifacts, 52 source files, linked receipts, the
journal, manifest and audit helpers. CRC and every member SHA-256 passed.
`review-package-2026-11-15.json` supplies the archive and member hashes; archive
SHA-256 is `fa51f2383865b615bb3ad388e1a5cdaa4e8255315ce24ded2d0d561d9503d9e0`.
The archive is project-local, not an off-machine backup. Restore selected members
only into a fresh project-local recovery directory and compare before replacing
anything. Remaining simulation artifacts stay in their hash-bound `build/` paths.
The package helper refuses to overwrite its existing archive and receipt.

## Required review and remaining evidence gaps

The owner should review the implementation changes, small timing margins, reset
behavior and retained failure history in `evidence/daily/T043.md`. There are 21
retained failed preparation archives, including timing, native warning, DRC and
timeout failures. One earlier XSim process returned nonzero after its completion
marker; it remains FAIL, its root cause is undetermined, and isolated replay plus
the subsequent full gates passed. No process-exit check was bypassed.

Power is vectorless with resets deasserted and default unspecified switching;
there was no SAIF/VCD activity input or measured board power. External delays
remain unspecified for 18 asynchronous inputs and 17 non-synchronous outputs:
there is no off-chip timing closure claim. One-clock native CDC and structural
synchronizer checks provide no metastability proof.

**Formal: T023 owner-skipped / NOT RUN. Physical hardware: NOT RUN. ASIC: NOT RUN.**
Directed ISA testing is not external certification. Passing static timing does
not establish successful physical board operation or overall project completion.

T043 start execution was authorized in
`evidence/owner_reviews/T043-2026-11-07-authorization.json`. Final T043 owner review
is still required by `AGENTS.md` and `docs/BACKLOG.json`. After explicit approval
and exact command authorization, record that approval through the harness. T032
physical programming remains separately gated and must not start from this
implementation authorization alone. No unattended work is authorized under the
current unrestricted runtime.
