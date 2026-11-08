# FPGA build flow and evidence boundary

T030 prepared November6 from T029 commit1f0be70. All four task gates passed on attempt1.
Confirmed Basys3 xc7a35tcpg236-1, one100MHz clock/10.000ns. T030 preserved the
diagnostic shell. T031 now selects the integrated initial-EEI SoC and the separate
soc_boot.mem image; the original diagnostic and rom_init.mem remain recoverable.
See SOC_BOOT.md for source integration, simulation and retained catalog warnings.
This manifest update does not execute the T043 flow or establish full-target PPA.

T045 selects the owner-reviewed v0.3 interrupt mode in the canonical top and
adds irq_boot.mem alongside the retained legacy image. The existing XPR gains
the CSR/admission sources and new image without removing prior sources. Native
simulation at production divider868 has passed; full FPGA synthesis, placement,
routing, timing, power, complete CDC and bitstream evidence remain T043 work.
Source-only integration retains the installed board-catalog warning failure;
the exact manifest is checked separately. See INTERRUPT_REPORT.md.

## Reproducible project-local commands

config/fpga_build.json lists exact top/part/version/build/clock, sources,
constraints and memory images. scripts/fpga_build.py validates paths, suffixes,
nonempty/unique inputs, image basenames, fresh output and frozen target contract.
It hashes inputs and writes a non-executable TSV job. fpga/basys3/build.tcl
independently parses fixed fields, verifies path/version/target/output/owner-ack
constraints and constructs the nonproject flow without opening/saving an XPR.

```powershell
python -B scripts/fpga_build.py plan --output build/FPGA/review_unique
```

Choose a new path for every invocation; existing directories are rejected without
overwriting or cleaning. Job/inputs/result/log/cache files stay inside that fresh
directory. Tool current directory is a child, and generated design files would
go to artifacts/ only in execute mode. Relative paths and absolute paths resolved
inside this project are supported by the launcher; shared harness.inside remains
unchanged and project-relative. Unknown/escaping paths fail. Current vendor batch
launcher rejects whitespace/metacharacter paths, so this observed workspace path
is supported; no global PATH/tool configuration changes are made.

Plan validates20 actual available Vivado commands for the all-stage flow: source
read/synthesis/XDC, utilization/timing/checkpoint, optimize/place/physical-optimize/
route, routed utilization/timing/clocks/clockinteraction/CDC/check_timing/DRC/power,
checkpoint and bitstream. It prints Tcl list commands and executes none of them.
Plan PASS is input/dispatch evidence, not RTL elaboration, synthesis or timing.

The execution branch is prepared for T043. The Python launcher reads actual
harness state and requires active/authorized T043, completed T031/T044/T045,
recorded T044 owner review and a manifest updated from diagnostic scope. It never
runs approve/authorize/reopen/enable. The Tcl job also requires an explicit T043
workflow acknowledgment. These checks are workflow, not authentication or a
sandbox; actual runtime remains unrestricted. Do not start unattended automation.
No execution-mode run is authorized or performed by T030.

Execution design: sources and XDC read nonproject; memory images copied to a
fresh artifact directory with unique names; checkpoints and reports written
locally without force overwrite. Synthesis and implementation can run separately
using --stage synth / --stage impl --checkpoint <project-build-file.dcp>, or all
together. Native tool jobs retain the existing120-second cap; larger future
flows may need bounded checkpoint stages, never hidden timeout success. Actual
execution branches are code-reviewed but NOT RUN here and must be validated
under T043 authorization. Before bitstream, nonempty max/min timing paths need
nonnegative slack and actual DRC violations must be empty. Reports retain
unconstrained paths/CDC and power assumptions; later parsers must check full
report completeness and final input/firmware bindings, not just a PASS string.

No hardware-server, target connection or programming command exists in this flow.
Generating a bitstream under T043 would still not authorize physical programming;
T032 requires separate owner authorization and board observations.

## Validation and preparation failures

Six policy tests challenge target/schema/input drift, byte-exact existing-output
preservation, memory basename collisions, missing implementation checkpoint,
owner prerequisites and actual unauthorized execution rejection. Synthetic
in-memory policy states test a predicate only; no owner command or state write.
Actual Vivado plan and eight negative jobs test target/clock/source/path/mode/
authorization/output rejection. No target output directory or bitstream is
allowed; every unexpected checkpoint fails.

Three retained preparations: (1) absolute output paths conflicted with the shared
relative-only path API; add launcher-local normalization without changing that
helper. (2) default300-second tool budget exceeded existing120 cap; use120, keep
cap unchanged. (3) plan20commands passed but recursive DCP scan detected five SDK
Tcl Store example checkpoints copied by startup. They match the installed local
2025.2/data/XilinxTclStore files AND an earlier read-only T029 startup copy byte
for byte. The Vivado/data path is a symlink to the installed shared data folder.
config/vivado_vendor_collateral.json pins only those exact paths/hashes. Every
other DCP/any bitstream still fails; requested target artifact directory must
remain absent. This is positive identification of vendor fixtures, not a broad
file/diagnostic exclusion. No tool/package download/install was performed.
All failed source archives, generated hashes and raw logs remain retained.

## Current PPA status

| Evidence | Status |
|---|---|
|Per-unit synthesis lint|Fresh T030 per-unit lint PASS; full-target flow NOT RUN|
|Build plan and input/output guards|T030 actual plan/eight guards PASS; target execution NOT RUN|
|Integrated SoC synthesis/utilization|NOT RUN, T043 after T031/T045 and owner authorization|
|Placement/routing/setup/hold closure|NOT RUN, T043|
|Full integrated/routed CDC|NOT RUN; T029 scoped result retains GPIO CDC-6 Warning|
|Power|NOT RUN; future report must disclose activity/confidence, not claim measurement|
|Bitstream|NOT RUN|
|Physical FPGA programming/UART observations|NOT RUN, separate T032 owner approval|
|ASIC|NOT RUN; no inference from Vivado|

Registry26 retains25 earlier regression targets. Full26 regression is not claimed.
Formal T023 remains owner-skipped/NOT RUN; no other task or review is waived.

## Final T030 evidence

evidence/runs/T030/attempt-1-20261107T032611376979Z.json passedallfour gates,exit0.
Checks/commandrecords: {"lint": [43, 23], "tcl": [33, 13]}. Audit: {"tools": 2, "sources": 49, "artifacts": 149, "preserved": 1170, "planned_commands": 20, "actual_reject_cases": 8, "installed_vendor_examples": 5}.

The13 Tcl-profile command records include one Python launcher; its inner actual
Vivado record is retained in the positive result.json. All failures/SDKprovenance
remain bound in evidence/t030-final-audit-2026-11-06.json. No full-target design
command was executed. Earlier pending descriptions are preparation chronology.

## T043 active execution (2026-11-07)

Owner authorized in7d8ef19. Full synthesis passed; initial routed timing failed
(-5.092ns) and async BRAM control DRC warnings remain retained. See
evidence/daily/T043.md for exact source snapshots, repairs and running gates.
No bitstream or physical programming is claimed. Final current-attempt gates
and human review are still pending. Per-unit and simulation passes do not
establish FPGA timing closure.

## T043 preparation update (2026-11-08)

Execution uses fresh project-local checkpoint stages to preserve the native120s
limit: synth, opt, place, fanout, placement, logic, pin, route, reports. The actual
acceptance gate binds every predecessor checkpoint and current-attempt source,
job, result and artifact hash. The all-stage plan now lists24 commands, adding
route status, effective XDC, physical inventory and explicit vectorless activity.
The combined legacy execution mode remains available but may time out; use the
harness gates for the bounded acceptance flow. No timeout or diagnostic is waived.

Flattened/rebuilt synthesis permits cross-module optimization. Explicit
retarget/propconst/sweep omits optional BRAM CE power lookahead that created
asynchronous-control DRC findings. The DRC ruledeck,10ns clock, board part and
XDC remain unchanged. Physical inventory requires18 exact synchronizer pairs,
36 ASYNC_REG FFs,36 pins and fully clocked reset synchronizer cells. The canonical
board synchronizes both button transitions then distributes reset through a
clocked initialized FF; hold btnC at least4 cycles to guarantee a core reset edge.
Generic reset/stage defaults preserve the previous unit interfaces. See the
T043 technical handoff for implementation details and independent tests.

Retained failed routed preparations improved setup WNS from-5.092ns to-1.657ns
and-0.688ns; none establishes100MHz closure or permits bitstream generation.
The latter two had zero DRC findings, positive hold and complete physical
inventory. Native vectorless estimate for boundedA was0.095W, Low confidence,
resets deasserted, no simulation activity file. It is not measured power.
Source/report archives and raw native result locations are in evidence/daily/T043.md.

Current data-bus/CSR serialization factoring passed interrupt preparation:
interrupts-20261108T193336390320Z,139 checks/71 native commands. One earlier
nonzero XSim exit after completion remains a failed receipt; isolated replay
and the subsequent full suite passed, with root cause not established. Independent
oracles, seeds1/20261107,9 positive boots, CSR queued-consumer witness and real RTL
mutants remain required. The only subsequent RTL change before current synthesis
was a comment clarification. Fresh synthesis passed (3742 LUTs,2544 FFs,32 BRAM,
36 IOB); its-1.291ns unplaced setup estimate is not routed closure. Current physical
preparation is still running. Final manifest remains NOT RUN until all current
harness gates pass. Formal T023 stays skipped/NOT RUN; hardware and ASIC NOT RUN.
