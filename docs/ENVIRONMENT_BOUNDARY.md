# Environment boundary — observed 2026-10-14

## Actual enforcement and authorization

The owner explicitly authorized in-place development in `C:\RV32I_Edge_SoC`.
The existing Vivado project is active engineering work, not a read-only reference.
This supersedes the original requirement for a separate project directory.

Actual session settings are **danger-full-access**, approval policy **never**,
with network access enabled. There is no enforced workspace-only filesystem
sandbox in this session. This is a reported limitation, not a claim of isolation.
The owner authorized attended bootstrap under this limitation. Neither this
document, `.harness/environment.json`, the Python harness nor a virtual environment
changes runtime permissions. Do not start unattended automation under these settings.

All writes made for this bootstrap are project-local. Do not modify unrelated
files, home configuration, global PATH, installed tools, OS scheduling or external
repositories. Actual restrictions must be configured outside this session by the
owner before unattended work. Prefer enforced workspace-write with on-request
approval, restricted network access and no writable external mounts; inspect the
actual next-session policy rather than trusting the observation JSON.

## Project-local locations

| Purpose | Location |
|---|---|
| Active project and Git root | `C:\RV32I_Edge_SoC` |
| Existing Vivado project | `RV32I_Edge_SoC.xpr` |
| Untouched original kit | `riscv_edge_soc_codex_kit/` |
| Recoverable original snapshot | `.baseline/20261015T051119Z/original.zip` |
| Original SHA-256 inventory | `.baseline/20261015T051119Z/manifest.json` |
| Persistent task state and lock | `.harness/` |
| Test/build output and caches | `build/` |
| Temporary files | `.tmp/` |
| Future optional virtual environment | `.venv/` |
| Compact committed evidence | `evidence/` |
| Exactly two dated reports | `docs/daily/` |

Baseline archive and build artifacts are ignored by Git. The baseline commit
tracks the original XPR and kit; the archive additionally preserves the original
small generated metadata files. No original files have been deleted or changed.
No junctions or symbolic links were found during the initial recursive inventory.
New generated file paths must resolve inside this workspace; do not introduce
links or mounts that escape it.

The harness sets TMP/TEMP/TMPDIR, Python cache controls, pip cache and XDG cache
paths for verification subprocesses. It uses exact argv without a shell, an
exclusive Windows byte-range lock, atomic state replacement and project-local
self-test repositories. These are workflow protections, not security enforcement.
Future EDA launchers must also explicitly set their working/output/cache paths
inside `build/`; no EDA tool was launched during bootstrap.

## Protected work and recovery

Inspect existing sources and constraints before editing; preserve a Git baseline
and document necessary XPR/XDC/RTL modifications. Do not delete sources/constraints,
reset Git history, clean the project destructively, alter hardware configuration,
or program an FPGA without owner authorization. No Git remote has been configured.
Commits use a per-command engineering identity; no global identity was changed.

For recovery, inspect baseline commit `8f16054` or extract selected archive members
to a NEW project-local recovery directory first. Compare bytes and review the diff
before restoring. Do not overwrite current user work or use destructive reset/clean.
The archive is not an off-machine disaster-recovery backup.

## Tool and network limits

Python 3.9.13 and Git 2.48.1.windows.1 were executed. Installed tzdata 2026.2
provides America/Los_Angeles date handling. No virtual environment is necessary
for the current standard-library harness, and no package was installed.
Vivado, Verilator, Icarus/vvp, Yosys, SBY and Make were not found on PATH.
Cocotb and pytest are unavailable in the selected interpreter. This does not
prove the EDA executables are absent elsewhere; request owner-supplied paths.
Docker's command was found, but the daemon was not queried or started.

No external downloads, paid/cloud EDA, publication, remote pushes, physical board
operations or system scheduler changes are authorized by this bootstrap.
Owner approval is required before installing dependencies or enabling scheduling.
Do not use privileged containers, Docker socket mounts or global package installs.

Residual risks: unrestricted processes can reach outside the project and use the
network; inherited environment variables and installed tools are not isolated;
future third-party tools may ignore cache settings or spawn surviving child
processes. Missing licenses/tools, an unknown physical board and unreviewed
architecture remain technical blockers for later milestones, not bootstrap passes.
