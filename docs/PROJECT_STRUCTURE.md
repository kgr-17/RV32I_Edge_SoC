# Existing project audit

Inspected the XML and filesystem without opening or saving Vivado.

- XPR: `RV32I_Edge_SoC.xpr`, created by Vivado v2025.2 according to its comment.
- Part: `xc7a35tcpg236-1` in project, synthesis and implementation settings.
- BoardPart is empty; no physical board has been verified.
- `sources_1`, `constrs_1`, `sim_1` and `utils_1` have no File entries.
- No top module is specified; automatic top selection is enabled.
- No RTL, testbench, XDC, create_clock constraint or external source references exist.
- `synth_1` and `impl_1` describe default Vivado 2025 strategies. Their presence
  and XML State fields are not proof that either run executed successfully.
- Existing `.cache`, `.hw`, `.ip_user_files` and `.sim` directories are generated
  project structure. No synthesis or implementation reports were found.
- There was no Git repository in the root or kit at initial inspection.

Reusable assets: the existing XPR/device configuration and the kit's architecture
draft, 40-task plan, DV hierarchy and review concepts. The kit harness required
repair because it imported Linux-only fcntl and assumed make/python3 availability.

Active additions live at the root: `AGENTS.md`, `docs/`, `scripts/`, `prompts/`,
`evidence/`, `.harness/`, `Makefile` and `.gitignore`. The original kit is retained
unchanged. Only the root backlog/state control current work.

Future Vivado source integration should use a reviewed project-relative Tcl
script, preserve recoverability and direct generated output into `build/`.
No integration Tcl was fabricated for the currently empty source sets. T025/T030
will add real board constraints and reproducible build scripts after owner review.
