# Local toolchain gates - T003

T003 selects the existing Vivado/XSim installation and standard-library Python;
no download, package install or global PATH change is required. The manifest is
config/rtl_checks.json, separate from machine-specific launcher paths in
.harness/toolchain.json. Pins are Python 3.9.13, Git 2.48.1.windows.1, tzdata
2026.2 and Vivado/XSim 2025.2, Vivado SW build 6299465. A mismatch fails the gate;
missing sources/tools are NOT RUN (125).

T003 completed on October 23, attempt 1 of the owner-authorized fresh budget.
The full gate passed 61 Python tests, actual fixture synthesis/structural lint,
XSim compile/elaboration, two 134-vector seeded simulations with waveforms, and
all five intentional failure checks. The three failed October 17 receipts and
their daily claim remain preserved. Final receipt:
evidence/runs/T003/attempt-1-20261023T182351910210Z.json. Detailed EDA evidence:
evidence/toolchain_runs/all-20261023T182408034597Z.json. This is fixture/toolchain
acceptance, not CPU ISA, production implementation, formal or hardware evidence.

Run from C:\RV32I_Edge_SoC:

```powershell
python -B scripts/preflight.py
python -B scripts/verify.py toolchain-rtl
python -B scripts/verify.py lint
python -B scripts/verify.py regress
```

The full toolchain-rtl gate includes runner/policy tests, the existing harness and
architecture-checker tests, document consistency and scripts/rtl_checks.py all.
The lint and regress aliases execute the same respective branches used by all;
there is no alternate weakened CI path. Make is optional and unavailable here.
The project-local Python commands are the supported interface.

## Exact lint and simulation scope

The only current design is dv/toolchain/register_fixture.sv, a 32-bit enabled
synchronous-reset register used to validate infrastructure. It is not a CPU block.
The lint branch uses actual Vivado non-project top-level synthesis, rejects
tool errors/warnings, inferred LD* latch primitives and black boxes, and runs
LUTLP-1/MDRV-1 structural DRC. It saves synthesis/DRC/utilization reports locally.
This is scoped synthesis lint, not comprehensive language/style lint, CDC, a
proof of all widths, timing closure or production design synthesis. Verilator,
formal and ASIC tools are still missing/unverified. Do not infer their results.

The regression branch actually runs xvlog --sv, xelab and xsim. An independent
Python history-based oracle generates 134 input/expected rows per seed; the SV
bench reads expectations rather than duplicating the DUT next-state expression.
Seeds are 1 and 20261017. Checks include reset with enable high, reset during hold,
enable/hold transitions, corner data and randomized histories. Each simulation
requires exactly one completion marker with seed and checked count, exit 0, no
error/warning diagnostics, and a nonempty waveform of clock/reset/enable/data
signals. Zero-test/marker-free exits
cannot pass. Vector and waveform hashes are recorded.

Negative fixtures deliberately contain a syntax error and an inferred latch.
Additional simulation modes inject $fatal, normal exit without a pass marker and
an endless clocked run. A negative case passes only when its expected specific
failure is observed and the positive evidence rules reject it. A missing license,
unrelated error or missing tool cannot count as a successful defect injection.
Intentional negative fixtures are not synthesis design sources.

In the verified run, XSim returned process exit 0 for the injected $fatal and for
the no-completion-marker case. The terminated hang also had raw exit 0, while its
runner status remained TIMEOUT. These were all rejected by semantic completion,
diagnostic and timeout checks. Do not replace the gate with an exit-code-only
wrapper or mistake a process-status PASS in the JSON for bench acceptance.

All production rtl/**/*.sv and rtl/**/*.v files must be registered in the
manifest; an unregistered file blocks the check. Each future module needs its own
sources, top, independent bench and test acceptance; the current fixture cannot
satisfy future CPU/module or ISA tasks. Future changes must extend the manifest
and scoped checks rather than relabel the fixture as CPU verification.

## Process control and evidence

Each invocation creates a unique build/T003/<profile>-<UTC> directory and an
incrementally written evidence/toolchain_runs/<profile>-<UTC>.json. Records include
exact vendor argv, cwd, UTC/duration, timeout, stdout/stderr, actual return code,
seeds, checked-vector counts and hashes. Failed runs are retained. WDB/log/report
files stay under build; compact JSON is committed. Replay the same profile and
manifest seeds to reproduce vectors; a new run directory preserves older failures.

The verified XSim repair passes only snapshot/--file/path through the Windows
batch launcher, placing simulator options/plusargs in a project-local argument
file. Paths use forward slashes to avoid option-file backslash escaping. Its exact
contents, intended argv and SHA-256 are captured in evidence.
Installed rdiArgs.bat reconstructs arguments with %1/shift; unquoted key=value
plusargs are the suspected source of the observed "Expected a switch but found 1"
failure. The --file option is documented by installed XSim help. The repaired
transport, its thirteenth policy test and all five XSim invocations passed their
intended acceptance checks on October 23; exact response files are in the evidence.

scripts/tool_runner.py starts a gated child before releasing the EDA command.
On Windows it attaches a kill-on-close Job Object before sending GO; on timeout
the whole owned job is terminated. Tests verify a spawned descendant cannot
write its delayed output after timeout. POSIX has a process-group fallback that
has not been executed on this Windows host. Each command is bounded to at most
60 seconds; actual EDA stage limits are 10/15/30/45 seconds and the intentional
hang is 2 seconds. Profile/temp/cache directories are project-local. The batch
launcher interface rejects whitespace/cmd metacharacters; the current configured
paths satisfy this restriction. Do not bypass it with string-built shell commands.

Job Objects, profile redirection and manifests are cleanup/workflow mechanisms,
not filesystem/network security isolation. The current session remains
danger-full-access / never; unattended use remains prohibited. No original XPR,
source/constraint, kit, global configuration or physical board is touched by this
non-project fixture flow. Top-level synthesis is deliberate: the earlier
out-of-context candidate skipped connectivity DRCs and was rejected. No such
warning is suppressed or accepted as passing evidence.

## Prepared GitHub Actions configuration

.github/workflows/rtl.yml is manual workflow_dispatch only, with read-only contents
permissions and a dedicated self-hosted Windows/Vivado label. It uses no external
actions, checkout downloads or installation steps. The operator must pre-stage a
clean checkout at the exact dispatched SHA. The job fails before executing tools
if that condition is unmet. It runs the same preflight and toolchain-rtl commands
above. Logs/evidence stay in the checkout; nothing is uploaded or pushed.

This file has not been submitted to or run by GitHub Actions. No remote or runner
was registered and no scheduling/automation was enabled. Before future use the
owner must approve publication/runner setup, configure and inspect actual runtime
sandbox/approval controls and the rtl-owner-review environment, and provision the
pinned tools without modifying this active project. The dispatch checkbox and
environment name alone are not enforcement. Do not run it unattended under the
current unrestricted session. Preserve resulting evidence rather than cleaning
or resetting a dirty checkout automatically.

# Historical toolchain observations - 2026-10-14

Platform: Windows, Windows PowerShell. The active harness supports Python >=3.9,
uses the standard library, and needs IANA timezone data. Installed tzdata 2026.2
already supplies America/Los_Angeles. No dependencies were installed.

| Tool | Observed result | Verification scope |
|---|---|---|
| Python | 3.9.13 | `python --version`, harness tests executed |
| Git | 2.48.1.windows.1 | `git --version`, real disposable repos/commits tested |
| tzdata | 2026.2 | installed package metadata and timezone conversion |
| python3 | WindowsApps alias | not used; use `python` |
| Vivado | 2025.2, C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat | batch version/target-part probe exit 0; no build |
| XSim xvlog/xelab/xsim | launchers found beside Vivado | compilation/elaboration/simulation NOT RUN |
| Verilator / Icarus / vvp | not found on PATH | lint/RTL simulation NOT RUN |
| Yosys / SBY | not found on PATH | synthesis/formal NOT RUN |
| cocotb / pytest | not available in selected interpreter | no dependency installation |
| Make | not found on PATH | Make aliases NOT RUN; use native Python commands |
| Docker | command found | version/daemon/container execution NOT RUN |
| RISC-V GCC | neither rv32 nor rv64 unknown-elf found on PATH | firmware build NOT RUN |

Use `python -B scripts/preflight.py` for a current machine-readable inventory in
`evidence/toolchain.json`. Preflight PASS means metadata and Python/Git readiness,
not RTL, toolchain completeness or FPGA build success. Tool versions are only
reported when an executable was actually queried or installed package metadata
was read. No global PATH, interpreter configuration or installed tools were changed.

Initially `.harness/checks.json` was empty because no RTL or DV tests existed.
T003 now registers real fixture lint/regression commands above. Unimplemented
future unit-test targets still return NOT RUN (125), as do missing input files.
Do not register echo/true commands as engineering gates.

T003 must establish an approved, pinned and locally executable RTL toolchain and
real lint/CI entrypoints before T004. Vivado/XSim paths have now been discovered;
installing or downloading dependencies requires explicit owner approval. Prefer
project-local `.venv/` and supported local tools. No simulator compatibility pair
from the original kit is treated as verified. Selected formal work is mandatory;
ASIC libraries/PDK, licensing and corners require the T037 owner review.

Commands capture outputs under the project. Prefer a reviewed Tcl launcher with
explicit `build/` working/output paths for future Vivado operations. The existing
XPR is empty, so no legitimate synthesis top, design clock or hardware image is
available to build today.

## Authorized discovery follow-up

The owner confirmed Digilent Basys 3 with xc7a35tcpg236-1. The running Vivado
process exposed its installation at `C:\AMDDesignTools\2025.2\Vivado`. No global
PATH change was made. `.harness/toolchain.json` supplies local launcher paths to
preflight. XSim launcher existence is discovery evidence only.

The initial `vivado.bat -version -nolog -nojournal` printed v2025.2 / SW Build
6299465 but returned exit 1; preserve `evidence/vivado_discovery.json` as a failed
command, without inferring a cause. The bounded read-only batch probe
`scripts/vivado_probe.tcl` returned exit 0 and reported `version -short` = 2025.2
and target part availability. Full argv/stdout/stderr are in
`evidence/vivado_probe.json`. Child temp/profile locations and working directory
were project-local. No project was opened, no RTL compiled, and no synthesis,
implementation, license-dependent design build or hardware access was validated.
