# T023 selected bounded-formal package and tool blocker

Current disposition: OWNER-SKIPPED on2026-11-04 under the explicit instruction
"yes, make this task mark as skip. and work on others". Formal evidence remains
NOT RUN, not completed/PASS. See evidence/owner_reviews/T023-skip-2026-11-04.json.
The original failed attempt/budget and drafts below are preserved. T024 can now
proceed with this exception disclosed; a future formal revisit requires an owner
scope change, rather than automatic retries or installation.

Status: NOT RUN. No prover, solver, formal compilation, counterexample or cover
witness has executed. T022 completed in141bc17; T023 began from clean Git.

Actual attempt1 is recorded in
`evidence/runs/T023/attempt-1-20261105T005724903976Z.json`: lint PASS, formal-smoke
NOT RUN125, both whitespace checks PASS. Tool receipt
`formal-smoke-20261105T010204187410Z.json` contains four executed version probes,
each exit125: sby --version, yosys -V, yosys-smtbmc -h, z3 --version. Four Python
acceptance-policy tests PASS; zero formal tasks ran. Active task state is failed,
attempts1, two finish attempts remain. Keep it active for normal resume after
tools are supplied; no reopen/reset or another task is needed/authorized.

Read-only discovery found no yosys, yosys-smtbmc, sby, z3, boolector, yices-smt2
or cvc5 on PATH. Targeted executable checks in C:/msys64/{usr,mingw64,ucrt64,
clang64}/bin and C:/oss-cad-suite/bin, C:/tools/oss-cad-suite/bin found none.
This is a statement about checked locations, not an assertion that every file
on the machine was searched. A shallow C:/ directory-name inventory identified
MSYS2; no contents inside unrelated directories or personal files were read.
No package manager, network, download, installation or global configuration was used.
Evidence: evidence/t023-tool-discovery-2026-11-04.json.

Prepared `formal/core_properties.sby` has five proposed tasks:

| Task | Proposed check and scope | Bound/control |
|---|---|---|
|alu|Actual ALU algebraic ADD/SUB/XOR invariants, zero shifts and arithmetic-shift sign preservation|12-step BMC; all operands/op bits symbolic, selected invariants only|
|forward|Actual forwarding-unit x0/unused/invalid operand zeroing and nearest older producer priority/load blocking|12-step BMC; both ports/producers symbolic|
|stage|Actual32-bit stage reset/clear priority, hold stability, advance/bubble and output masking|12-step BMC; first sampled edge assumes reset|
|cover_stage|Reach a nonzero valid payload while hold is asserted|12-step cover with required nonempty witness|
|negative|Deliberate always-false property under a local formal define|2-step BMC must FAIL with real counterexample|

All wrappers instantiate actual production modules; no DUT translation/copy or
production RTL modification is made. x0 here concerns forwarding inputs, not a
proof of the architectural register-file storage. Stage hold checks concern
storage behavior, not complete CPU ready/valid protocol or liveness. Inputs after
initial reset are unconstrained; no memory fairness/progress assumptions are
introduced. These are bounded searches, not induction or unbounded proof.

The SBY/SMT dialect, package/enum/struct/unpacked-array frontend support and exact
status/model/witness layout remain UNVALIDATED. No formal executable is available
to check them. After tools are supplied, inspect actual local tool help/version
and frontend compatibility before resuming the bounded gates. In particular,
the current production package and multi-module stage source need a capable SV
frontend. A parser failure is FAIL/NOT RUN, never a proof or permission to replace
the production DUT with an easier behavioral model. Do not claim this draft is
portable to an untested tool version.

`scripts/formal_checks.py` probes all four required tool commands through the
existing bounded process-tree runner. Missing commands return125/NOT RUN and
zero formal tasks. The owner can identify existing installations via explicit
argv arrays in .harness/formal_toolchain.json, including {python} for a script.
Observed sby/yosys/z3 versions must be pinned to actual outputs. No version
number is invented. A child launcher adds supplied tool directories only to its
own process environment, preserving global PATH and keeping descendant cleanup.
The SBY child must resolve its normal engine command names; version probes alone
do not establish nested-tool launch compatibility. Verify that actual packaging
after tool paths are supplied; errors cannot satisfy the proof gate.
Each fresh SBY task gets60 seconds under build/T023; existing output directories
are refused, not overwritten/deleted. Composite formal check ceiling600 seconds.

Acceptance requires the actual process status, matching fresh task status file,
nonempty SMT assertion/cover inventory, and nonempty VCD/YW witness for cover and
negative control. A native crash, zero exit without task status, zero properties,
missing engine, timeout or witness-free failure cannot pass. Python acceptance
tests verify those rejection rules; they do not run or substitute for a prover.
All sources/commands/outputs/status/model/witness hashes are recorded when run.

Resume after the owner supplies installed paths or explicitly authorizes a
project-local download/installation: inspect binaries/licenses/versions/frontend,
configure process-local tool commands and observed pins, read latest daily handoff,
run daily --supervised and begin T023 to recover active work, then finishT023
--evidence evidence/daily/T023.md. Preserve current NOT RUN evidence and attempt
budget. No automatic install, global PATH edit, self-reopen, scheduling, push or
physical programming. T024 DV closure cannot start until real T023 gates pass.
