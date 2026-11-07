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
