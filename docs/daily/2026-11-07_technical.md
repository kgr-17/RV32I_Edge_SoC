<!-- entry:5e3cef4ef3144ed5d14d4de511f3dcc5791d07829dbfb26ba23013efdf7e5d37 -->

## November 7 attended T031 recovery

Read the November 6 technical handoff and required engineering contract; ran
daily --supervised (exit 0, .tmp/2026-11-07-daily.txt), inspected Git and resumed
T031 with begin T031 (exit 0). No task verification attempts used. HEAD b94e043.
Earlier fast-divider compiled SoC boot PASS remains preserved, 187 retirements
per boot, PASS CRLF twice, persistent RAM counter 1->2. Production-divider
preparation did run 121330 native cycles but correctly failed its strict gate:
the waveform Tcl referenced inner instead of the wrapper's actual body hierarchy,
causing Simtcl 6-55 WARNING. Preserve the FAIL receipt and sources before repair;
do not reinterpret the process exit 0 as a passed verification.

Continue active T031 only: standalone fabric errors/lanes/stalls/reset cancellation,
production UART boot, independent negative controls, diagnostic compatibility,
recoverable top/project integration. Two-worker independent lint retains every
existing check and 120-second native/600-second aggregate limits; thread-safe
evidence and failure-joining tests are required. Final T031 gates still pending.
Exactly two November 7 reports; prior-day findings retained. Runtime unrestricted,
approval never, attended only. No downloads, installations, global changes,
scheduling, push or FPGA programming. T023 formal skipped/NOT RUN, full FPGA
implementation/timing/bitstream/hardware/ASIC NOT RUN. Next milestone T044 requires
owner architecture review after T031 is completed and committed.


---

<!-- entry:eddd0aae5afd4231fabc606430efc7a6a49171370c5da8af203618fae446efef -->

## T031 implemented; final acceptance gates pending

Actual SoC preparation soc-20261107T205446617903Z PASS60checks/32commands. Fast
seeds1/20261107 each1970cycles/two187-retirement boots; actualcanonicalBasys3top
productiondivider868:121330cycles/two4357-retirement boots,86664Dwaitcycles. Every
phase independently decodes PASS CRLF and matchesISA/bus/entirephysicalRAM;
persistentword1->2. Fabricseeds4006/3970edge rows,268/271distinctRAMwords written
before readback, all64offset/maskcombosperregion, error/fulladdress/ROMwrite/
concurrentROM/heldresponse/UARTbusy/resetcancel.3actualbadinputs, coherentearlyRAM
RTLmutant, corruptactualimage(dataLMAbyte) rejected(cycle39SOC_DMEM_RESPONSE),
9wrong-retirement/truncated/emptytrace controls. No marker-only acceptance.

Saved original10integrationinputs in evidence/prepare/T031-before-integration/
inputs.zip with hashes. diagnostic_top.sv body identical exceptmodulename;
existingboardvectors/negatives/probes preserved. Canonicaltop now reset_sync+
edge_soc withrawRX/switches enteringexisting2FFchainsonce; full23RTL+image+XDC
manifest integrated intoexistingXPR. XPRdiff153addedlinesonly; XDC unchanged.
Sourceintegrationactualreceipt soc-project-integration-20261107T205550441295Z
remainsFAIL because76Board49-26catalog+1emptyBoardPart warning; operationfinished
andindependentexactXMLmanifest PASS. No warnings filtered, noSDKmodified. This
is separatelydisclosed, not warning-free integration. Repro source-onlycommand:
python -B scripts/project_integration.py --apply; checkwithoutmutationomit--apply.

Initialproductionprep soc-production-preparation-20261107T204729669742Z FAIL for
Simtcl6-55(inner vsactualbody hierarchy) despiteprocess0; archived30sources/
64generatedhashes. Lateractualboardtoprunwarningfree. Initialsocdriver
soc-20261107T205408043634Z NOT RUN beforecompilation becausehashmanifestreferenced
dv/unit/test_mmio.py; corrected to existingdv/integration/test_mmio.py. Allreceipts
preserved. Onepureunitassertion used rd_wdata instead of Retirement.rd_data;
corrected test API, no modelbehaviorchange; all7oracletestsPASS.

Standalonefabriclintpreparation soc-fabric-lint-preparation-20261107T205657778564Z
PASS withstrictnative diagnostics. Parallelindependentlintmax2 retainsallprior
designs/negativechecks and120native/600aggregatecaps; RLockserializesreceipt
updates.19policytestsPASS includingboundedconcurrency/failurejoin and12concurrent
command/checkindexbindings.10boardpolicytestsPASS includingexactmanifestnegative
andoldbodyequivalence;6buildpoliciesPASS. NativeTclplan replay PASS(exit0), nofull
targetbuild. Boardcompatibilityreplaystarted, retainactualreceipt. Registry27
retains26earlierregressiontargets; full27regression NOT RUN.

Next finishT031 --evidence evidence/daily/T031.md withallrequiredlint/test-soc/
whitespacegates, atmost3attempts. Auditrawsource/tool/artifact/firmware/trace/wave/
project/snapshotpreservation, appendtodayreports, stage/indexhashcheck/commit then
prepareT044ownerarchitectureproposal. CPU/peripheral/memoryRTL,originalboot/linker/
T026image andapprovedARCH hash403c527d73aeb22de5dee40c2b0a0dbb7175f9f7197a1a35d48f2ff15c10da03
unchanged. Additionalbaselineexistingchanges(test_board_checks.py and
test_fpga_build.py) explicitlyneeded forstrictmanifest/diagnosticequivalence and
config-awareownerpolicytests; baselinearchive retainedunaltered.31complete+1skip/
41untilfinalgate. T023formal NOT RUN/ownerskipped, fulltargetsynth/PPA/CDC/timing/
bitstream/physical/ASIC NOT RUN. Attendedunrestricted/never; noinstall/download/
globalconfig/push/scheduling/programming. ExactlytwoNovember7reports, November6
entries retained. VersionsPython3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim
2025.2 SW6299465; actualGNUtoolpinsunchanged. Every sessionreadlatesthandoffand
requiredcontractfiles,daily--supervised,recoveractivebeforeselectingnext.


---

<!-- entry:c5d51f32ae84076112f2e0fce49d15455ecdb18c00762f20b559f4ec578228c0 -->

## T031 completed: compiled firmware boots on the integrated SoC

All four gates passed on attempt 1, all exit 0: lint, test-soc, git diff --check,
git diff --cached --check. Receipt: evidence/runs/T031/attempt-1-20261107T205937621750Z.json.
Current native receipts: evidence/toolchain_runs/lint-20261107T205938016781Z.json, evidence/toolchain_runs/top-20261107T210340673979Z.json, evidence/toolchain_runs/soc-20261107T210442479446Z.json.
Check/command counts: {"lint": {"checks": 45, "commands": 24}, "top": {"checks": 22, "commands": 13}, "soc": {"checks": 60, "commands": 32}}. Independent policy/oracle tests:
7 SoC, 19 lint, 10 board, 6 build, all PASS. Separate test-top and test-tcl
replays also passed; full 27-target regression NOT RUN. Lint retains all prior
design checks, fixture and latch rejection; two workers completed it in roughly
4 minutes, with native <=120 and aggregate <=600 second limits unchanged.

Final audit evidence/t031-final-audit-2026-11-07.json independently verified
3 receipts, 60 source hashes, 522 artifacts, 1182 unchanged historical files,
125270 positive boot cycles, 9462 retirements, 36 decoded UART bytes and 7976
fabric vectors. Six boots cover two seeds, actual 100MHz board top at divisor868,
cold/warm reset, RAM counter1->2, complete architectural RAM, precise ECALL8
termination after signature600d600d, GPIO/timer/RX and UART busy backpressure.
Actual corrupt-image, early-store RTL mutant and malformed inputs/traces were
rejected. Synthesized fabric and preserved diagnostic are unit evidence only.

Changes: new rtl/soc/{soc_fabric,edge_soc}.sv, sw/soc_smoke.S and separate
soc_boot.mem; native SoC/fabric/board-top DV and independent model; compiler,
integration and validation scripts; canonical top/XPR/source manifest, diagnostic
compatibility and thread-safe bounded lint. Existing CPU/peripheral/memory RTL,
original boot/linker/rom_init.mem, XDC and approved architecture hash are unchanged.
There are 22 canonical RTL files plus one memory image (correction to the earlier
23-RTL shorthand). XPR only adds153 source lines; the original10 integration
inputs remain in a hashed ZIP, and the diagnostic body is byte-equivalent except
module name. Owner approvals, skips, old daily claims/exceptions are unchanged.

Retained limitations: source integration finished but its receipt remains FAIL
for76 installed board-catalog warnings plus1 empty BoardPart warning. Exact XPR
manifest and simulation passed separately; no warning was hidden, no SDK changed.
Initial waveform hierarchy FAIL and missing-source NOT RUN are preserved. Final
whitespace caught my registry CRLF edit (exit2); archived raw ZIP, normalized LF
with identical parsed JSON, then both required whitespace gates passed. Audit-only
unused absolute-path and UTF-8/GBK errors were archived before repair; final audit
passed without changing verified sources. No checks/timeouts were weakened.

Reproduce: python -B scripts/verify.py lint; python -B scripts/verify.py test-soc;
python -B scripts/project_integration.py. Use --apply only for recoverable source
integration into the existing project, no synthesis/programming. Firmware expects
host ASCII A after reset and emits PASS CRLF at approximately115200baud/8N1.
See docs/SOC_BOOT.md. FPGA synthesis/place/route/PPA/fullCDC/timing/bitstream and
physical hardware/ASIC NOT RUN. T023 formal remains owner-skipped/NOT RUN.

Next inspect/stage audited task files, verify all60 index hashes, local commit
from b94e043, then query actual next and begin T044 architecture review. Prepare
a concrete interrupt/CSR/trap proposal without implementing it or altering the
approved v0.2 contract. T044 requires owner review; do not self-approve. Mandatory
progress32 completed plus1 owner skip out of41. Each new session must read latest
handoff/AGENTS/boundary/ARCH/verification/backlog/state/loop and daily --supervised;
recover active task first. Versions Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/
Vivado-XSim2025.2 SW6299465, pinned GNU tools unchanged. Unrestricted/never runtime,
attended only; no download/install/global config/push/scheduler/FPGA programming.
Exactly two November7 reports updated; all prior-date entries retained.


---

<!-- entry:4866761505e224797d0d0e401c8b2de79592a22a52752c232f73eb2639da8b9d -->

## T044 architecture proposal prepared after T031 commit

T031 audited and committed locally as 66bfa46 (65 files, all60 index-source hashes
matched, both whitespace checks exit0). Git was clean; next selected T044 and
begin T044 exit0. Baseline evidence/prepare/T044-baseline-2026-11-07.json records
1245 tracked source hashes. Read current timer/pipeline/decisions before drafting.
Official RISC-V20240411 Zicsr/CSR-list/machine1.13 pages read under existing owner
documentation authorization; exact URLs/sections and engineering inferences in
evidence/t044-sources-2026-11-07.json. No packages/tools/IP downloaded or installed.

New docs/INTERRUPT_SPEC.md is proposal v0.3 only. ADR0013-15 appended toDECISIONS.
Proposes ENABLE_TRAPS legacy-default0 core/SoC, enabled future physical top with
separate firmware; six CSR ops, direct handler, synchronous traps/MRET, specified
CSR masks/resets and new trace fields. CurrenttimerCTRL bit1 is AUTO_RELOAD;
newIRQenable usesbit2, preservesaddresses/count/equality/W1C/reload. Customtimer
drives machine-external cause11, not a claim of standard64-bit mtime or fullM
platform. Drain admittedwork/stablefetch then rechecklevel/masks withpipeline/buses
empty, mepc fromlastretirednext_pc; olderfaultswin, no effectreplay. FullnewCSR/
trap/bus/branch/reset/compiledfirmware/UART/negative/legacyregression acceptance
requirements are explicit. All new featureimplementation/verification NOT RUN.

No RTL/config/XPR/XDC/image/approvedARCH or verification-policy change inT044.
Next run requiredfinishT044 --evidence evidence/daily/T044.md, max3attempts, then
audit baselinepreservation/proposalhashes/ownerstate and commit reviewpackage.
Human review is mandatory perAGENTS/BACKLOG; do not approveonownerbehalf or begin
T045 beforeapproval.32completed+1formalownerskip/41; T023NOT RUN retained. Full
FPGAimplementation/timing/PPA/bitstream/physical/ASIC NOT RUN. BothNovember7reports
appendonly; attendedunrestricted/never, no globalchanges/push/scheduling/programming.
VersionsPython3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465.


---

<!-- entry:cb9a5d115255449ee5da166514fd8e61285659bbe5a48805af1aa1bcbe6ee2a0 -->

## T044 ready for owner architecture review

T031 is committed as66bfa46. T044 document gates passed on attempt1, exit0:
harness validate and both whitespace checks. Receipt evidence/runs/T044/attempt-1-20261107T211422904365Z.json.
This establishes workflow/document readiness only; no trap/CSR/interrupt RTL or
functional result. State is awaiting_review, active=None; next returns planning_only
with no executable task. Human review remains an explicit hold beforeT045.

Review package: docs/INTERRUPT_SPEC.md v0.3, appendedADR0013-15 inDECISIONS.md,
evidence/t044-sources-2026-11-07.json and evidence/t044-review-manifest-2026-11-07.json.
Proposal SHA256: 86dca0ef075734c57029be58c8a4f75a63540ef18384017489db3e2a4626c17d.
Audit preserved1242 baselinefiles, everyRTL/config/XPR/XDC/image/check/approvedARCH
unchanged; threeallowed historicaldocuments retain their exactpriorprefixes.
Allownerreviews/startapprovals/skips/legacyclaims/exceptions unchanged. No owner
command called. ExactlytwoNovember7reports, bothT031 andT044 participation saved.

Owner must review feature-selected compatibility, CSR/mask/reset/trace definitions,
timer CTRLbit2 preservingbit1reload, customtimer via machine-external cause11,
precise drain/IRQ-level recheck, synchronous traps/MRET and T045 acceptance scope.
No standard64-bit timer or fullprivilegedplatform claim. Currentnewfeatures all
NOT IMPLEMENTED/NOT RUN. T023formal remainsownerskipped/NOT RUN; fullFPGA/physical/
ASIC claims remainabsent and executionauthorizations separate. No waiver inferred.

Before stopping review/stage package, verifyindexproposalhashes/whitespace, commit
locally, then present concrete committed package forreview. Nextsession: readthis
latesthandoff andallcontractfiles,daily--supervised,Gitstatus. IfT044stillawaits
review, do notbeginT045. Owner can explicitlyapprove thepackage andrun
python -B scripts/harness.py approve T044 --confirm-owner-review; AGENTS reserves
ownercommands, so do notcallonownerbehalf without explicittask-specific direction.
Afterreviewisrecorded, inspectcleanstate/querynext/beginT045 andimplementexact
approvedproposalwithreproducibleevidence; donotclaimexistingT031tests coverthe
newmode.32mandatorycompleted+1ownerskip/41, T044awaitsreview. Toolsunchanged:
Python3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465.
Attendeddanger-full-access/never; noinstall/download/globalconfig/push/scheduling/
FPGAprogramming. Allrecords/project remainrecoverable inlocalGit andsavedarchives.


---

<!-- entry:59ddb6081930cb7c8bab3a3076c2856bdf9855b3ace2ae437b7e7f2bf79568b9 -->

## Committed review package and shutdown/resume point

T031 implementation/evidence commit66bfa46d08d69dbebaa4ec8d6d60de1cce82fa34.
T044 proposal/evidence package commit80bd35e (all13 inspected files staged, four
review-source index hashes matched, whitespace exit0). Git clean after commit;
status validates32completed,1owner-skipped,1awaiting_review,0blocked/failed/active.
T044 exact proposal SHA256 remains86dca0ef075734c57029be58c8a4f75a63540ef18384017489db3e2a4626c17d.

Present this committed package to the owner; approval is still pending. Stop
implementation at the AGENTS.md architecture-review / BACKLOG T044 gate. No owner
approval command has run. Owner may review docs/INTERRUPT_SPEC.md and explicitly
authorize the task-specific approval command or run it personally. On receipt,
record only that authorized acknowledgment, commit the resulting review state,
then query next and begin T045 from clean Git. Otherwise keep the review hold;
no daily quota or technical-failure claim is involved. The report-only commit
records these known package IDs; it changes no proposal or verified source.


---

<!-- entry:d4f42fabc077ce1044ded72b6a1a9346130e2c48a23e9a3cfd69e9077ab85ff8 -->

## T044 owner approval recorded; proceed to T045

Owner explicitly replied "Approve v0.3 and authorize that command" to review of
package80bd35e. Verified unchanged proposal SHA25686dca0ef075734c57029be58c8a4f75a63540ef18384017489db3e2a4626c17d,
then executed exactly python -B scripts/harness.py approve T044 --confirm-owner-review,
exit0. T044 completed and its owner review is recorded. Supplemental exact owner
authorization: evidence/owner_reviews/T044-2026-11-07-authorization.json.
daily --supervised exit0 saved .tmp/2026-11-07-t045-daily.txt; Git was clean at
b741095. Read latest handoff/AGENTS/boundary/ARCH/verification/backlog/state/loop
and the approved interrupt proposal. Runtime remains unrestricted/never, attended
only; no scheduling/install/global changes/programming. This grants T045 scope,
not T043 or T032 execution permission. Commit acknowledgment, then query/begin
T045 from clean Git and establish baseline before RTL edits.33mandatory completed
plus1owner-skip/41; new feature functionality still NOT RUN; formal T023 retained.


---

<!-- entry:fcc47e48988bc609351da3af9e86c66a68bbe8451bf32afa26c7d8ebf7091251 -->

## T045 active: first enabled CSR/trap/timer SoC boot passed

Owner approval recorded f9d05e0; began T045 from clean Git. Baseline tracked
source hashes in evidence/prepare/T045-baseline-2026-11-07.json. No finish attempts
used. Added csr_file/trap_control, enabled decoder IDs41..47 (packed57-bit legacy
decode unchanged), feature-constant pipeline CSR serialization/precise traps/
drain-recheck and separate observations. Core/SoC default legacy0; timer bit2 IRQ
enabled only with feature, preserves bit1 reload. Existing images/constraints/
approved v0.2 and v0.3 documents untouched. Canonical FPGA top remains legacy
until full enabled native validation and recoverable integration.

Four independent CSR model tests PASS. Actual csr-preparation-20261108T011427355331Z
PASS10checks/8commands:6424 pre/post vectors per seed1/20261107,12848total, CSR
masks/read-only/zero-index-vs-value/trap/MRET/reset/admission cancellation. First
legacy SoC prep soc-boot-preparation-20261108T011559866077Z strictly FAIL on new
unconnected output warning; archived28 sources and generated hashes before binding
all added outputs explicitly. Same legacy expectations then passed in
soc-boot-preparation-20261108T011638471997Z, preserving old compiled program.

Actual pinned GNU RV32I_Zicsr build interrupt-firmware-20261108T011955511938Z PASS;
new sw/interrupt_smoke.S + existing boot/linker produce separate irq_boot.mem.
Enabled interrupt-boot-preparation-20261108T012206694452Z PASS:7318cycles,
two747-retirement boots, all nine synchronous mcause classes plus externalIRQ11,
all six CSR operations, nested synchronous frame save/restore, MRET, timer W1C,
20 independently decoded IRQ PASS CRLF bytes,354RAM effects, persistentword1->2.
Independent CSR/ISA/bus/peripheral/RAM/serial checker passed; no marker-only test.

Continue soleactiveT045: unit defect controls/lint, random bus waits and direct
IRQ mask/cancel/reset/interactions across seeds, production868/actualtop boot,
mode-aware source/image integration, runtime contract and complete test-interrupts
driver. Full27existing regression targets plus new IRQ target must all run;
old19-target run was478seconds, added EDA targets justify bounded2-worker
independent regression under unchanged600 aggregate/120native limits. Preserve
every command, order/evidence/failure and old expectations; test orchestration.
Do not reserve finish until preparation is concrete; max3attempts. Record both
reports before final gates, audit current/source/artifact/baseline and commit.
FormalT023 stays ownerskipped/NOT RUN; fullFPGA synth/route/timing/PPA/fullCDC/
bitstream/physical/ASIC NOT RUN, approvals remain separate. No install/download/
globalconfig/push/scheduling/programming; attendedunrestricted/never. LAdateNov7,
UTCNov8. VersionsPython3.9.13/Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2
SW6299465. New sessionreads latesthandoff plusrequiredcontractfiles/daily and
recoversT045; do notselectanother task orclaimfeaturecomplete from preparations.


---

<!-- entry:713b14720933582767f78422538240208edd29b7706659f7fa6830847c905ae5 -->

## T045 implementation prepared for final gates

Latest full interrupt script preparation interrupts-20261108T014955485553Z PASS
119checks/59commands. Four CSR unit tests and seven independent IRQ model tests
PASS. Both seeds1/20261107 cover CSR/timer vectors, fast boots, random request/
response waits, level cancellation during drain, six reset-aborted states then
two complete boots, and an actual fault/IRQ collision. The latter uses a recorded
verification-only illegal instruction patch after the polling load; source IRQ is
admitted while the fault is in EX, and native IRQ_FAULT_WON>=2 confirms synchronous
fault precedence. All effects/retirements/traps/CSR state/wholeRAM/UART are checked
independently; disabled observation metadata must be zero and RAM cannot execute
CSR/MRET encodings. Native wrong-resume core plus four unit RTL mutants rejected;
six bad-vector, five bad-trace and actual corrupt-image controls rejected.

Actual production Basys3 top at868 passed179302cycles/two2895-retirement boots,
20IRQ PASS CRLF bytes, persistentword1->2. Standalone enabled CPU/CSR/admission
lint PASS6checks/3commands (newCPU49.641s); explicit aligned30-bit internal CSR
trap-PC adapter removed true unused-input warnings without changing32-bit core
PC or masking diagnostics. Enabled timer lint is registered for final full lint.

Project now includes newCSR/admission sources andirq_boot.mem, retainsoldimage,
adds20XPRlines/no deletions. Backup evidence/prepare/T045-before-integration/.
Source-only integration soc-project-integration-20261108T013838027098Z remainsFAIL
forinstalled board-catalog warnings, exactmanifestPASS separately. Newcore/SoC
defaults0 preservelegacy; canonicaltopdefaults1/newimage. LegacyboardTBexplicitly
selects0/soc_boot.mem. New runtimecontract has52ports and binds exactT044specSHA;
approvedv0.2/v0.3 submissions, XDC, boot/linker, priorimages andkit unchanged.

Failures retained before repairs: legacyunconnectedports(28inputs), waitwrapper
syntax(30), unusedCSRalignmentbits(18), cancellationwindow(30), prioritywindow
(62), plusdriverPythonparseZIP. Sourcewindowrepairs changeDVstimulus only; required
cancellation/fault-priority checks remain. Passing108check checkpoint archived
beforepriorityextension. PowerShell redirection gaveNativeCommandError despite
43unittestOK; rawoutputZIPretained. Exactargv policies thenPASS exits[0,0,0]
in evidence/prepare/T045-policy-checks.json (dispatcher2,budget5,harness43).

scripts/verify.py now runs only independent regression targets withmax2 workers,
all28targetsretained, declaredresultindices preserved, each completion flushed
atomically so laterfailure cannot erase earliercommandoutput. Larger appended
suites startfirst; ordinarychecks staysequential. Concurrency/exception/NOTRUN/
ordering tests passed; original600aggregate/120native caps unchanged. Full28
regression NOT RUN yet. Registry/newdriverready; requiredfinishT045 next with
lint,test-interrupts,regress,andwhitespace, max3attempts(current0). Do not reuse
preparationPASS asfinaltaskgate. Onfailure preserveallinputs/receipts beforefix;
never weakenchecks. Nativeartifact roots underbuild/T045; allactual logs/hashes.

Next runcheck_interrupt_contract, inspectdiff, finish, auditallcurrentreceipts/
source/artifacts/baseline/ownerstate, appendbothreports andcommitinspectedfiles.
Thenquerynext expectedT043ownerexecutiongate; prepareconcreteplan andrequestowner
authorization, never self-authorize or programhardware.33mandatorycomplete+1skip/
41 beforeT045finishes. T023formal NOT RUN/ownerskipped. FullSoCimplementation,
timing/PPA/fullCDC/bitstream/physical/ASIC NOT RUN. Runtimeunrestricted/never,
attendedonly. No download/install/globalconfig/push/scheduler/FPGAprogramming.
ExactlytwoNovember7reports, priorentriesretained. VersionsunchangedPython3.9.13/
Git2.48.1.windows.1/tzdata2026.2/Vivado-XSim2025.2 SW6299465, pinnedGNUtools.


---

<!-- entry:70f642940c1341a19e183f58aee81d51f4c3a220a220d6aa387ded4aa41a2978 -->

## T045 first final attempt failed; bounded second attempt prepared

Attempt 1, evidence/runs/T045/attempt-1-20261108T015654747556Z.json:
lint FAIL(1), test-interrupts PASS(0), regress FAIL(1), both whitespace gates PASS(0).
All 27 preceding regression targets passed. The new IRQ target failed because
the production XSim process exited 4294967295 after 0.781s with empty stdout and
stderr and no waveform. This is an actual native failure; root cause remains
unknown. The separate earlier IRQ gate passed 119 checks/59 native commands.
Regression completed all 28 indexed targets in 537.997524s under the unchanged
600s command cap. Attempt-1 sources (200 files), manifest, journal and hashes are
retained in evidence/failed_sources/T045/attempt-1/. One attempt consumed; two
remain. Resume did not reopen or reset the attempt counter.

Strict synthesis exposed unused constant IRQ/observation logic in disabled
configurations. Enabled-only observation registers now use a generate branch;
legacy observations are constant zero. Exact whitelisted legacy lint definitions
omit only inactive IRQ boundary ports in the two disabled probes. Production,
enabled probes and every simulation use the full normal interface without these
definitions. Both native source guards reject an enabled feature combined with
the legacy-port specialization. No warning filters or diagnostic policies changed.
Native Vivado synth_design -help confirmed -verilog_define; read_verilog has no
such option. Supplementary repair receipt disabled-lint-repair-20261108T022124252206Z
PASS 9 checks/5 commands, including both default probes, enabled CPU, wrong-scope
Tcl rejection and enabled-feature source-guard rejection. All 20 lint-policy tests
and all 8 process-runner tests pass. Existing descendant timeout cleanup remains.

Each native command now gets a unique directory under build/tmp and records it
as temporary_directory; TMP/TEMP/TMPDIR are per child process. This prevents
shared fixed temporary filenames. It is not proof of the XSim failure's cause.
The first implementation lacked the parent directory; two preparations failed
before EDA launch and their 20 inputs were archived before the mkdir repair.
Enabled cold/warm boot then passed in interrupt-boot-preparation-20261108T022134468028Z.
Runner tests are added to the required IRQ gate. No timeout cap increased.

Source-only integration soc-project-integration-20261108T023432195703Z still FAIL
for the installed board catalog warnings; project_manifest_matches is true and
the second apply leaves the XPR unchanged. No full synthesis/implementation,
bitstream or programming was invoked. Approved specifications, legacy firmware,
XDC and original kit are retained. Temporary helper discovery used a nonexistent
harness.write API; Python exited 1 before any file write, then atomic was used.

Next: inspect current diff/contract, finish T045 for fresh attempt 2, audit exact
current sources and recursive receipts/artifacts, append these same two dated
reports and commit inspected files if all gates pass. If another failure occurs,
retain its complete input snapshot before repair and observe the three-attempt
limit. No automatic owner approval or task reopening. T043 execution requires
separate owner authorization after its concrete plan is prepared. T023 formal
remains owner-skipped/NOT RUN. Full target timing/PPA/CDC, hardware and ASIC remain
NOT RUN. This runtime is unrestricted; attended execution only. Python3.9.13,
Git2.48.1.windows.1, tzdata2026.2, Vivado/XSim2025.2 SW6299465 unchanged.


---

<!-- entry:b54649aaefd1aebc0b9b2a6f7cc810086cdf70108e46e1369d9bc2b3beda3962 -->

## T045 completed: approved v0.3 implementation and simulation acceptance

Authoritative attempt 2: evidence/runs/T045/attempt-2-20261108T023832980009Z.json. All five gates PASS, exit 0:
python -B scripts/verify.py lint; python -B scripts/verify.py test-interrupts;
python -B scripts/verify.py regress; git diff --check; git diff --cached --check.
Strict lint passed 53 checks/28 native commands. Regression passed all 28 indexed
targets in 567.403s; original 27 commands remain the unchanged prefix.
Two fresh IRQ suites each passed 119 checks/59 commands, with seeds 1/20261107.
Production top at divisor 868 passed 179302 cycles, two boots of 2895 retirements
each, 20 independently decoded IRQ PASS CRLF bytes and persistent RAM counter
1->2. Nine positive runs per suite include random waits, source cancellation,
six reset-aborted states and fault-before-IRQ priority. Four unit RTL mutants,
an actual wrong-return-PC core, malformed/wrong vectors/traces and corrupt ROM
were rejected at their intended checks. Four CSR tests, seven IRQ oracle tests,
two dispatch, five budget, 43 harness and eight native process tests also passed.
No formal proof or certification is inferred from finite simulation.

Implementation: csr_file atomically commits the approved 14-CSR subset with
reset > trap > MRET > software-write priority. trap_control drains and rechecks
the level, saving the latest retired continuation. The pipeline serializes six
CSR operations and MRET; precise exceptions kill younger work and drain stale
fetches. Timer CTRL bit 2 enables synchronous machine-external IRQ cause 11;
bit 1 keeps its existing reload meaning. Separate trap and CSR observations
extend the normal core to 52 ports. Core/SoC default to legacy mode, while the
canonical Basys3 top enables the approved mode and separate irq_boot.mem.
Production and all simulations use the normal interfaces; exact disabled probe
specializations remain guarded and recorded. No warning filter was added.

Main source changes: rtl/core/csr_file.sv, trap_control.sv, pipeline_cpu.sv,
decoder.sv, rv32_pkg.sv; rtl/peripherals/timer.sv; rtl/soc/edge_soc.sv and
soc_fabric.sv; fpga/basys3/top.sv. Verification adds independent CSR and full
ISA/bus/peripheral/serial models, seven testbench snapshots, three lint probes,
scripts/interrupt_checks.py, interrupt_firmware.py and interface-contract check.
sw/interrupt_smoke.S uses the existing boot/linker, saves nested trap frames and
demonstrates timer IRQ/MRET. Registry/manifests/source lists include these files;
existing benches only bind new ports or select their original legacy image.
Config/XPR source graph includes the two RTL files and additional image; XPR
adds 20 lines with no deletion. Recoverable before-image is in
evidence/prepare/T045-before-integration/. Original kit, XDC, prior images,
boot/linker, approved architecture and interrupt specification stay unchanged.

Engineering infrastructure: independent regression targets run with two workers,
retain registered indices and flush complete results. Ordinary checks remain
sequential. Each native command uses its own build/tmp directory. The existing
600s aggregate and 120s native limits and descendant timeout cleanup remain.
First final attempt and all preparatory failures are retained, including native
XSim startup failure with unknown cause. The unique temporary directory change
is isolation evidence, not proof of that failure's cause. Attempt 2 succeeds
without clearing attempt 1; state records 2 attempts and no active task.

Final audit evidence/prepare/T045-final-audit-2026-11-07.json recursively binds
42 tool receipts, 170 source hashes and 2063 artifact hashes;
all are current to this attempt. It also checks exact regression command prefix,
source archive hashes, baseline preservation, report append-only history and
unchanged owner approvals/skips/legacy claims. A copy of the audit helper is
retained for replay. Source-only Vivado integration remains explicitly FAIL for
installed board catalog warnings, with exact manifest PASS and idempotent XPR
hash checked separately. This does not establish a warning-free full FPGA build.

Git baseline f9d05e0 records T044 owner approval; reviewed proposal 80bd35e and
T031 66bfa46 remain in history. Commit this inspected T045 package locally after
the final diff/index review; do not push. Mandatory progress is 34 completed plus
one owner-skipped task out of 41. T023 formal remains NOT RUN and must be disclosed
in final review. Full target synthesis/place/route/timing/power/CDC/bitstream,
physical-board tests and ASIC evidence remain NOT RUN.

Next session: read this handoff and all AGENTS startup files, run daily
--supervised, inspect Git and recover any active task. T045 is complete; do not
rerun finish or reset attempts. Query next; prepare the hashed T043 plan only,
then obtain the owner's explicit T043 execution authorization before authorize/
begin or any full target build. Do not approve final T043 review or program a
physical FPGA on the owner's behalf. Runtime remains unrestricted/never and is
not a sandbox; no unattended runs, downloads, installs, global edits or scheduling.
Versions unchanged: Python 3.9.13, Git 2.48.1.windows.1, tzdata 2026.2 and
Vivado/XSim 2025.2 SW 6299465, with pinned actual GNU compiler components.


---

<!-- entry:132011f6a3e230d19811c0c7c9c9efec4b636b962879c07e06e7832459251f13 -->

## Shutdown/resume point: T045 committed; T043 plan ready for owner authorization

Local commit 92e3363 contains the approved v0.3 implementation, 213 inspected
files (35,915,282 bytes including retained raw evidence/archives), both reports,
and all current acceptance receipts. All 170 audited source hashes matched the
Git index exactly; git diff --cached --check passed. No unstaged edit remained
at commit. The final audit binds 42 tool receipts, 170 sources, 2063 artifacts,
and 1220 unchanged baseline files. Its helper preparation corrected two metadata
assumptions: the unchanged T026 compiler discovery reference is historical config
provenance, and lint includes register_fixture as well as negative_latch. The
helper before correction is archived; no native check or acceptance changed.

After the clean commit, ran plan-only command (exit0):
python -B scripts/fpga_build.py plan --output build/T043/preauthorization-2026-11-07-92e3363
Actual Vivado returned FPGA_BUILD_PLAN_PASS for20 commands/33 input hashes;
all inputs stayed unchanged, target artifacts directory absent. Five DCPs are
exact previously pinned SDK examples, not synthesized target outputs. Job,
raw result and a separate audit are preserved in
evidence/prepare/T043-preauthorization-2026-11-07/. Review package:
docs/FPGA_EXECUTION_REVIEW.md. No target source/synth/place/route/report/bitstream
command in the plan was executed. No hardware connection/programming occurred.

harness next/status exit0: active null, next null/planning_only true, completed34,
pending10 (including4 optional), skipped1, no failed/blocked/review task. T043 is
the next engineering milestone but start authorization is absent. Its three
required verify entries vivado-synth/vivado-impl/fpga-reports are unregistered;
implement them under active T043 after owner authorization, preserving report
completeness, source bindings and failures. Do not claim this plan passed those
checks. Installed board-catalog warning failures and GPIO CDC-6 history remain.
Keep native120/aggregate600 caps and no diagnostic waivers. Formal remains NOT RUN.

Owner must explicitly authorize T043 execution and the exact command
python -B scripts/harness.py authorize T043 --confirm-owner-review
before the agent may record it. No owner command was called for T043. Once an
explicit response arrives, save its exact evidence, record authorization, run
daily --supervised, inspect clean Git and begin T043. Proceed attended; capture
actual synthesis/implementation/timing/CDC/power/DRC/bitstream evidence and finish
with at most3 attempts. Final T043 human approval is separate. T032 physical
programming is separately gated. Do not rerun T045 or reset its two attempts.
Both Nov7 reports append this handoff; no other dated report was created.


---

<!-- entry:60034199d1fc73392cfd7a064233c2e92808b906109d83d5564fd71cb1e31446 -->

## T043 review packaging correction

The initial git diff --cached --check returned exit 2 on job.tsv: its required
empty checkpoint field is represented by a trailing tab. Exact command/output
are retained in evidence/prepare/T043-preauthorization-2026-11-07/whitespace-preparation-failure.json.
The native job was not edited. Its byte-identical review copy is now inside
native-job.zip with member and archive hashes in audit.json; the loose review
copy was moved to the original project-local build folder. The native original
also remains. No whitespace rule or parser was relaxed. This concerns evidence
packaging only; T045 sources and all plan input hashes remain unchanged. Rerun
both whitespace checks and inspect exact indexed bytes before the review-package
commit. T043 remains pending/unauthorized; its final human review and physical
programming remain separately gated.


---

<!-- entry:7786b5a4786149bc583eac91a7e480b9d00ea59e305ec61837f2aadd69a386e7 -->

## T043 execution explicitly authorized

Owner response to question call_75c30f28522746ffb8ef509c1cbefc2a: "Authorize T043
and that command". Exact task-specific authorization and reviewed document hash
are retained in evidence/owner_reviews/T043-2026-11-07-authorization.json. Ran
python -B scripts/harness.py authorize T043 --confirm-owner-review, exit0,
AUTHORIZE. This permits attended local synthesis, place/route, report checking
and conditional bitstream generation, not physical FPGA programming or final
T043 human approval. Read the required startup documents/state/backlog/latest
handoff; daily --supervised exited0, no active task, clean Git baseline121a607.

Next: commit this explicit authority/report update, begin T043, preserve the
baseline and execute synthesis preparation with the reviewed Tcl in a fresh
project-local output. Implement the three missing gates and strict completeness/
source/checkpoint/firmware/report checks. Keep native120/aggregate600 caps;
preserve any failed source/checkpoint inputs before repairs, do not mask warnings
or failed timing. Exactly these two Nov7 reports are appended. Runtime remains
unrestricted/never; attended only. Formal T023 remains owner-skipped/NOT RUN,
physical programming and ASIC remain unverified. Versions unchanged from T045.
