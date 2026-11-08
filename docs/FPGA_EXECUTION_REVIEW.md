# T043 execution review — awaiting owner authorization

The interrupt implementation is committed as **92e3363**. T045 passed all five
acceptance gates on attempt 2. The working tree was clean before preparing this
package. T043 remains pending, with no execution authorization or active task.

The existing flow has now passed an actual Vivado **plan-only** invocation for
the current integrated design. This validates the job, inputs, available Tcl
commands and tool version. It executes none of the planned design commands.

```powershell
python -B scripts/fpga_build.py plan --output build/T043/preauthorization-2026-11-07-92e3363
```

Result: exit 0, `FPGA_BUILD_PLAN_PASS`, 20 planned commands, unchanged input hashes.
The reproducible job and raw result are preserved in
`evidence/prepare/T043-preauthorization-2026-11-07/`.
The exact job is inside `native-job.zip`: its empty checkpoint field requires a
trailing tab, so the raw TSV is archived without changing its bytes. The initial
whitespace-check failure and the final packaging correction are retained.

| Input | Reviewed value |
|---|---|
| Target | Digilent Basys 3, xc7a35tcpg236-1 |
| Clock | One 100 MHz input, 10.000 ns, existing XDC |
| Tool | Vivado 2025.2, SW Build 6299465 |
| Top | basys3_top, 36 physical ports |
| Feature | Approved v0.3 traps/CSR/timer IRQ enabled by default |
| Source graph | 24 RTL files, one XDC, two retained memory images |
| Active firmware | irq_boot.mem; legacy soc_boot.mem retained |
| Input bindings | 33 hashes in the actual plan result |

With authorization, the next attended session will begin T043, implement its
missing verification registrations and report-completeness checks, and execute
the reviewed flow. The backlog's `vivado-synth`, `vivado-impl` and `fpga-reports`
checks are currently unregistered; this plan does not claim those checks ran.

The concrete flow reads the listed RTL, synthesizes the top, reads the existing
XDC, writes synthesis utilization/timing and a checkpoint, then optimizes, places,
physically optimizes and routes. It saves routed utilization, setup/hold timing,
clocks, clock interaction, complete CDC checks, check_timing, DRC, power estimates
and a routed checkpoint. Bitstream generation requires nonempty setup/hold paths
with nonnegative slack and no DRC violations. The T043 report checker must also
check report completeness, unconstrained paths, CDC findings, source/checkpoint/
firmware hashes and power activity/confidence assumptions. Failed or missing
checks remain failed or NOT RUN. No timing or diagnostic waiver is proposed.

All output goes to fresh directories under `build/T043/`. Existing project
sources and constraints are preserved. The current 120-second native-command
limit stays in force; a flow that exceeds it must be recorded as timed out and
reworked into bounded checkpoint stages, or separately reviewed. No timeout is
being extended by this request.

Current limitations to retain during T043:

- Existing source-only XPR integration still reports installed board-catalog
  warnings. Its exact source manifest passed separately. The plan-only command
  passed without those warnings, but does not show that synthesis will be clean.
- Scoped CDC evidence retains the documented GPIO CDC-6 finding. Full-design
  CDC and physical timing closure remain unverified.
- T023 formal proof is owner-skipped and NOT RUN. Simulation and synthesis do
  not replace formal proof or establish full RISC-V privileged compliance.
- Power reports will be estimates, with explicit activity assumptions.
- Vivado startup copies five pinned SDK example DCPs into its project-local
  cache. The plan audit identifies their exact paths and hashes separately;
  they are vendor fixtures and provide no target synthesis evidence.
- Runtime permissions remain unrestricted. The harness is workflow tooling,
  and only attended execution is allowed.

The requested owner action is explicit authorization for T043's local synthesis,
implementation, report checking and conditional bitstream generation, and for
this exact workflow command:

```powershell
python -B scripts/harness.py authorize T043 --confirm-owner-review
```

After that acknowledgment, `begin T043` may select the task. T043's final human
review is a separate gate. Physical FPGA programming remains T032 and requires
separate owner authorization; this flow contains no programming commands.
