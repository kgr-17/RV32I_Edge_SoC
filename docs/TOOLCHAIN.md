# Observed toolchain — 2026-10-14

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

Check targets are explicitly registered in `.harness/checks.json`. The initial
registry is empty because no RTL or DV tests exist. Therefore `verify.py lint`,
`regress`, or a future unit-test target returns NOT RUN (125) until the task adds
real inputs and exact commands. Do not register echo/true commands as engineering
gates. Missing input files also return NOT RUN.

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
