# T029 reset/input synchronization and scoped CDC

Prepared November6 from T028 commit02ff265. All four task gates passed on attempt1.
Existing CPU/UART/GPIO/input_sync/board/XPR/XDC/images unchanged. Single100MHz
production clock and approved reset priorities remain unchanged. This task adds
a reusable reset boundary for T031, not a new clock domain in the target.

## Production boundaries

rtl/peripherals/reset_sync.sv has clk_i, asynchronous active-high arst_i, and
active-high rst_o. Both release_q bits initialize1 for FPGA startup and carry
ASYNC_REG/SHREG_EXTRACT=NO. Assertion asynchronously sets both bits; deassertion
shifts zero through two rising edges. A stopped clock cannot release reset.
Downstream CPU/peripheral state uses synchronous reset and sees the old rst_o
on the release edge, as approved. Physical bring-up still requires explicit
button reset; simulated INIT is not physical startup validation or an ASIC claim.

Existing input_sync.sv accepts WIDTH independent asynchronous levels, two stages
per bit, default16 and supported1..32. Its synchronous rst_i clears both stages.
It serves the GPIO switches. Existing uart_rx.sv separately synchronizes RX idle-
high before center sampling. First-stage Q must drive only its second-stage D;
all synchronization stages share the core clock and carry ASYNC_REG. Do not use
input_sync for a coherent multibit bus, narrow pulse catcher or switch debounce.

The original diagnostic top keeps its tested inline reset until T031 replaces
its diagnostic connections. T031 must instantiate this tested reset_sync once,
feed its rst_o to synchronous CPU/peripheral reset, raw switches to gpio and raw
RX to uart_mmio. Avoid adding redundant undocumented synchronizer latency.

## Actual analysis and the rejected empty-report trap

Installed Vivado2025.2 help confirms report_cdc is structural and needs clocks
on source and destination; I/O paths need delay constraints. Local option/help
receipts are preserved, including the full returned help text. General background:
[AMD UG906 CDC overview](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Report-Clock-Domain-Crossings)
and [detailed report fields](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Detailed-Report?contentId=dpIpapqMwgmTq7Ze_xRGLg).
Those web pages describe2026.1; actual options/results here come from installed
2025.2, not an assumption of version equivalence.

First primary-input probe created a virtual external clock, complete input/output
delays and asynchronous clock groups. check_timing found no missing clocks/delays,
yet report_cdc returned All paths are Safely Timed with zero CDC objects. Batch
-name also emitted an ignored-GUI-option warning. This preparation is FAIL and
does not establish safe synchronization. Its exact5 inputs, raw reports and
warnings are retained. No empty report can pass the current checker.

dv/cdc/cdc_registered_probe.sv now supplies18 analysis-only off-chip launch FFs
on external_model(13ns) to the actual production reset/input/UART primitives
inside cdc_probe. Core is10ns. The source clock/registers exist only in DV and
never enter the production single-clock target. This explicitly exposes the
otherwise unrecognized external launch domain to the tool. I/O delays0 and
asynchronous clock groups model analysis relationships, not measured external
timing or physical board constraints; project XDC remains unchanged.

Actual synthesized report(all_checks_per_endpoint/no_waiver, no severity filter):

| Rule | Severity | Groups | Inputs | Depth | Meaning |
|---|---|---:|---:|---:|---|
|CDC-3|Info|1|1|2|RX synchronizer with ASYNC_REG|
|CDC-9|Info|1|1|2|asynchronous reset synchronized with ASYNC_REG|
|CDC-6|Warning|1|16|2|multibit switch synchronizer with ASYNC_REG|

CDC-6 remains Warning and is NOT waived. The16 GPIO inputs are independent level
signals; a software snapshot does not promise atomic coherence across unrelated
switches. This primitive is appropriate only under that stated use. The report
is not a zero-warning CDC signoff. New/unknown rules, Critical findings, missing
attributes/stages, incorrect clocks/endpoints or any waived path fail the checker.
Actual structural checks count18 chains/36 stages and enforce attributes, common
clock and exclusive first-to-second-stage fanout for every chain. check_timing
must report zero missing/unconstrained-clock/I/O/loop checks under this analysis.

Two isolated actual-synthesis faults validate the CDC gate: removing RX ASYNC_REG
produces CDC-2 Warning and is rejected; bypassing GPIO second stages produces
CDC-4 Critical and is rejected. Raw faulty reports/constraints remain saved.
No message severity override, create_waiver, quiet error suppression or existing
verification change is used. Earlier report-capture PASS is preparation only;
fresh full task gates still required.

## Digital verification

dv/cdc/test_cdc.py uses last-assert/elapsed-edge and sample-history expectations.
Three policy tests verify manual release/data timing, short-pulse restart and
replay. tb_cdc.sv checks INIT before any clock, asynchronous assertion while the
clock is stopped, no stopped-clock release, and pre/post reset/data for widths
1/16/32. Two seeds1/20261106 each produce1645 rows,49 held-reset edges,36 subcycle
pulses, four0..3ns phases and all32 one-hot input bits. The modeled0.2ns pulse
is an ideal RTL event test, not proof of silicon minimum reset pulse width,
recovery/removal timing or analog metastability behavior.

Actual wrong-reset/empty/truncated inputs and WIDTH33 must reject precisely.
Three actual digital RTL mutations test one-edge release, missing asynchronous
assertion and input-stage bypass. Clock-stop and startup hooks execute in native
SV. Actual native preparation cdc-20261106T223420874717Z passed50 checks/25 commands.
It does not substitute for the final lint/test-cdc/whitespace gates.

```powershell
python -B dv/cdc/test_cdc.py
python -B scripts/harness.py finish T029 --evidence evidence/daily/T029.md
```

Registry25 targets retain24 predecessors. This is scoped synthesized primitive
analysis and finite digital simulation, not complete SoC or routed CDC/MTBF,
formal(T023 skipped/NOT RUN), timing/power, physical FPGA or ASIC signoff.
T031/T043 must retain these external-boundary limitations and inspect the final
integrated/routed target; an empty primary-input CDC report is insufficient.

## Final measured evidence

evidence/runs/T029/attempt-1-20261106T223751516977Z.json passedallfour gates,exit0.
Native checks/commands {"lint": [43, 23], "cdc": [50, 25]}. Final audit {"tools": 2, "sources": 49, "artifacts": 128, "preserved": 1140, "edge_rows": 3290, "chains": 18, "stages": 36, "retained_cdc_warnings": 1, "raw_report_members": 25}.

Fresh3290row digital comparison and all native/synthesis negatives passed.
CDC6 remains unwaivedWarning; the18chain36stage result has the scope described
above. Exact raw reports are preserved in evidence/prepare/T029-raw-cdc-reports-2026-11-06.zip.
The post-gate clock alias assumption/correction is retained separately; RTL and
required task gates were unchanged. Earlier pending text is preparation chronology.
