# RV32I Edge SoC

Status: engineering bootstrap implemented and self-tested. No CPU RTL, FPGA
implementation, hardware validation or ASIC results exist yet.

The existing `RV32I_Edge_SoC.xpr` is the active Vivado project. Its configured part
is `xc7a35tcpg236-1`. The owner confirmed a Digilent Basys 3. Top module, RTL and
constraints are not yet configured. Vivado 2025.2 was located and its batch
startup/target-part catalog verified; local paths are in `.harness/toolchain.json`.

From PowerShell in `C:\RV32I_Edge_SoC`:

```powershell
python -B scripts/preflight.py
python -B scripts/test_harness.py
python -B scripts/harness.py status
python -B scripts/harness.py daily --supervised
```

The last command prepares an attended Codex session. Read the returned handoff
and `prompts/DAILY_RUN.md`, then perform exactly one eligible task. It does not
start a model, run an infinite loop, install a scheduler, or run RTL by itself.
`scripts/daily.ps1` is a PowerShell convenience entrypoint with the same purpose.
Python is the supported native Windows interface; Make targets are optional
aliases and were not executed because Make is not on PATH.

Read `docs/ENVIRONMENT_BOUNDARY.md`, `docs/CODEX_LOOP.md`, the latest technical
handoff under `docs/daily/`, and `docs/BACKLOG.json`. Architecture remains a draft
until T002 owner review. The backlog has 43 tasks: 39 mandatory, 4 optional.

Original work is recoverable from baseline Git commit
`8f16054b24a9d50021f8a805f7f0d78435206daa` and a local hash-verified backup
documented in `docs/PROJECT_BASELINE.json`. The original engineering kit remains
unchanged in `riscv_edge_soc_codex_kit/`; root-level files are the active versions.

This bootstrap session has unrestricted filesystem access. Unattended execution
is disabled pending actual sandbox/approval configuration. No dependencies were
installed, no network downloads were made, and no FPGA was programmed.
