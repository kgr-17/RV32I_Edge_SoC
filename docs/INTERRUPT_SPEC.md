# Interrupt and trap proposal v0.3

Status: PROPOSED for T044 owner review on November 7, 2026. No implementation or
new architecture approval is claimed. T031 baseline commit: `66bfa46`. The approved
v0.2 contract and all current RTL, images, constraints and project settings remain
unchanged by this proposal. T045 implements only after owner approval.

## Decision requested

Approve an opt-in trap configuration with CSR instructions, resumable synchronous
exceptions, MRET and one synchronous interrupt input. Route the existing custom
32-bit timer through the machine-external interrupt class, cause 11. Preserve its
counter, comparison, automatic reload and sticky status behavior; add a distinct
IRQ-enable bit. Preserve the fatal-halt configuration and all its verification.

This is a bounded bare-metal execution environment. It does not establish full
privileged-ISA, platform, certification, operating-system or security compliance.
The implementation must document the supported subset accurately.

## References and scope of inference

The official 20240411 library provides [CSR instruction semantics](https://docs.riscv.org/reference/isa/v20240411/unpriv/zicsr.html),
[CSR addresses and access conventions](https://docs.riscv.org/reference/isa/v20240411/priv/priv-csrs.html),
and [machine trap definitions](https://docs.riscv.org/reference/isa/v20240411/priv/machine.html).
Relevant sections are Zicsr 6.1 and machine 2.1.6, 2.1.7, 2.1.9, 2.1.13-16,
2.3.1-2.3.2. These reads were authorized documentation access, not tool installs.

Source-derived summary: CSR operations exchange or modify a register atomically;
zero register/immediate fields suppress selected accesses. Machine traps save a
PC and cause, mask interrupts and transfer to a vector. MRET restores interrupt
enable and returns through mepc. CSR numbering distinguishes register permissions.
Machine-external pending state may come from platform hardware. The following
configuration, register subset, timer wiring, draining policy, traces and acceptance
tests are this project's proposed engineering choices.

## Configuration and compatibility

- Add a constant `ENABLE_TRAPS` parameter, default 0, to the production pipeline
  and SoC wrappers. Default 0 preserves the tested v0.2 fatal-halt behavior,
  project fault codes, instruction legality, retirement and bus protocol.
- The canonical Basys 3 top will expose the parameter and default to 1 in T045,
  with a new interrupt firmware image. Its 36 physical ports, part, clock and XDC
  stay fixed. Its legacy DV configurations explicitly select 0 and soc_boot.mem.
- The decoder must retain legacy legality when the feature is off. All legacy
  vectors, oracles and expected outcomes remain, with explicit new port ties and
  feature selection where needed. Add separate enabled-feature tests.
- In enabled mode, add all six Zicsr operations and exact MRET encoding 0x30200073.
  ECALL, EBREAK and other synchronous faults enter the handler; ordinary successful
  RV32I execution and FENCE keep their existing behavior. WFI, SRET, debug return,
  counters, other extensions, privilege transitions and unlisted CSRs are outside
  this subset and produce illegal-instruction traps. No U/S mode or MMU is added.

## CSR register choices

All registers are 32 bits. Writable masks define readback and accepted state;
reserved bits read zero and ignore writes. Unsupported CSR addresses trap as
illegal instructions. Register-level read-only writes trap; writes to read-only
fields inside an implemented read/write CSR are ignored. The address assignments
follow the linked official CSR listing; reset values and supported fields below
are the proposed implementation contract.

| Address | Register | Reset | Writable state / fixed readback |
|---|---|---|---|
| 0x300 | mstatus | 0x00001800 | MIE bit3, MPIE bit7; MPP bits12:11 fixed3 |
| 0x301 | misa | 0x40000100 | Fixed RV32I identification, writes ignored |
| 0x304 | mie | 0 | MEIE bit11; all other fields zero |
| 0x305 | mtvec | 0 | BASE bits31:2; direct mode, low2 bits zero |
| 0x310 | mstatush | 0 | Fixed zero, writes ignored |
| 0x340 | mscratch | 0 | All32 bits |
| 0x341 | mepc | 0 | Bits31:2; low2 bits zero |
| 0x342 | mcause | 0 | All32 stored bits; generated causes restricted below |
| 0x343 | mtval | 0 | All32 bits |
| 0x344 | mip | 0 | MEIP bit11 reflects irq_external_i; writes ignored |
| 0xF11..0xF14 | mvendorid, marchid, mimpid, mhartid | 0 each | Register-level read-only |

misa's I bit and MXL identify the fixed integer base; the software capability
document separately advertises the CSR subset. No MTIP, standard 64-bit mtime /
mtimecmp, PLIC, external pin interrupt, Zicntr or full machine profile is claimed.
The custom timer IRQ is a platform source for MEIP.

CSRRW/CSRRWI always attempt a write and omit the read when rd=x0. CSRRS/CSRRC
omit a write only when the rs1 *index* is x0; their immediate counterparts do so
when the five-bit immediate is zero. A nonzero register index containing zero
still requests a write. The operand is read before rd changes, including rd=rs1.
The old CSR value reaches rd only when rd is nonzero. CSR reads have no side
effects here; access legality still observes the requested operations. A suppressed
write may read the ID registers; CSRRW to an ID register traps even with rd=x0.

Serialize CSR instructions and MRET: older architectural work finishes first;
the operation samples current GPR/CSR state and commits its CSR/GPR changes once
at retirement. Younger work cannot issue memory effects or observe intermediate
state. Reevaluate interrupt eligibility immediately after enabling CSR writes and
MRET, before creating a new fetch; do not add a fixed post-enable blind window.

## Timer source and MMIO

Existing timer registers stay at 0x10000100/104/108/10C. COUNT, COMPARE, STATUS,
natural byte enables, response snapshots, successful-response effect points,
COUNT-write precedence and match-over-W1C priority remain unchanged.

CTRL already uses bit0 COUNT_ENABLE and bit1 AUTO_RELOAD. Add bit2 IRQ_ENABLE
only in the enabled configuration; reset it to zero, selected byte writes update
it atomically with the other low-byte fields. Preserve ignored bit2/read-zero
behavior in legacy mode using an `ENABLE_IRQ` constant default 0 in timer.

In the enabled SoC, `timer.irq_o = STATUS.MATCH && CTRL.IRQ_ENABLE && !reset`.
Connect it directly through the fabric/SoC to core irq_external_i. All logic is
on the same 100MHz clock, with no additional asynchronous source or clock. CSR
masks affect CPU delivery, not the timer's sticky status or peripheral IRQ level.
Disabling the counter does not clear an already pending match. The handler can
W1C STATUS or mask IRQ_ENABLE; a coincident match retains pending state. There is
no automatic acknowledgment on CPU entry or MRET and no new MMIO address.

## Precise entry, priority and return

Eligibility is the sampled conjunction of irq_external_i, mie.MEIE and
mstatus.MIE. The input is a level, not a pulse-capture service. The timer's sticky
status preserves pending events while masked. Direct core tests may deassert the
level during draining; a canceled level must not force a later stale interrupt.

Interrupt admission has three steps:

1. At eligibility, stop creating fresh fetches. Drain every already offered or
   accepted fetch under the existing hold/response rules, discarding its eventual
   result. Already queued decode entries and EX/MEM/WB instructions finish in age
   order. Redirects still kill younger work and define the continuation PC.
2. Track the architectural continuation PC from each successful retirement's
   next_pc, starting at reset PC0. Wait until the decode queue, stages and both
   bus transactions are empty. Every completed store or MMIO pop must already
   have its single retirement record before interrupt entry.
3. Recheck the level and masks at that empty boundary. If eligible, enter once
   with mepc equal to the continuation PC, mcause=0x8000000B, mtval=0, and target
   mtvec.BASE. Otherwise resume fetching the continuation PC without a trap.

Do not withdraw a stalled valid request, discard an unanswered data transaction,
replay a committed effect or capture speculative next_fetch_pc as mepc. No new
request is admitted on a previous response's consume edge. Memory waits extend
interrupt latency; this proposal adds no bus timeout or hard real-time guarantee.
With responding buses, draining is finite and accepts no fresh instruction work.

Priority is age-based: reset cancels all work; an older synchronous fault takes
precedence over the interrupt; unresolved older data waits must finish; ordinary
redirects/retirements during drain retain their architectural effects. An older
branch kills younger wrong-path faults. When a synchronous fault wins, cancel the
IRQ-drain request and reevaluate after entering its handler with interrupts masked.
This specifies ordering without allowing a global IRQ signal to defeat age.

Synchronous traps suppress retirement and effects of the faulting instruction,
kill younger work, and drain stale instruction traffic before handler fetch.
Older effects/retirements remain. Save the causing instruction PC in mepc and
use the following mapping; legacy diagnostic numbers remain separate.

| Existing diagnostic | Enabled mcause | mtval |
|---|---|---|
| 1 illegal instruction / illegal CSR | 2 | Instruction word |
| 2 instruction address alignment | 0 | Bad target |
| 3 instruction access | 1 | Failing fetch PC |
| 4 load alignment | 4 | Effective byte address |
| 5 load access | 5 | Effective byte address |
| 6 store alignment | 6 | Effective byte address |
| 7 store access | 7 | Effective byte address |
| 8 ECALL | 11 | 0 |
| 9 EBREAK | 3 | 0 |

At trap commit, set MPIE to the previous MIE and clear MIE; MPP remains3. Trap
entry writes no GPR and leaves memory intact. It does not increment retirement
order. MRET retires once, redirects through aligned mepc, restores MIE from MPIE
and sets MPIE=1. GPR save/restore and exception-PC advance are software duties.

There is one hardware CSR frame. Software must save it before allowing nesting;
a nested trap overwrites the live frame. No implicit hardware stack or double-
trap extension is added. An invalid handler address can repeatedly fault; firmware
must install a valid ROM handler before enabling interrupts. Masking avoids normal
interrupt nesting, but synchronous handler faults still trap.

## Interface and observation changes

Retain all current local bus and retirement widths. Add these core ports and
propagate observation outputs through edge_soc for DV; physical top pins stay fixed.

| Direction | Port | Width / meaning |
|---|---|---|
| in | irq_external_i | 1, synchronous level |
| out | trap_valid_o | 1, one-cycle committed-entry pulse |
| out | trap_order_o | 64, number of successful retirements before entry |
| out | trap_pc_o | 32, saved mepc |
| out | trap_insn_o | 32, synchronous offending word; 0 for IRQ/fetch error |
| out | trap_cause_o | 32, complete cause including interrupt bit |
| out | trap_tval_o | 32 |
| out | trap_target_o | 32, selected direct vector |
| out | retire_csr_valid_o | 1, successful CSR operation, including read-only form |
| out | retire_csr_addr_o | 12 |
| out | retire_csr_read_o, retire_csr_write_o | 1 each, requested access qualifiers |
| out | retire_csr_rdata_o, retire_csr_wdata_o | 32 each, zero when qualifier is0 |

CSR wdata reports the normalized resulting CSR state; a write to ignored fields
can therefore report unchanged state. mip's source bit reports the pre-edge
sample if accessed, and ignored writes never alter the wire. MRET has no CSR
operation record; its successful instruction trace and independent CSR model
observe its implicit state change. All invalid observation fields are zero.
Reset clears observation outputs, order, CSRs, draining and masks as specified;
mstatus/misa keep their fixed reset fields. No entry/retirement is visible in reset.

For deterministic scoreboarding, trap_valid and retire_valid are mutually
exclusive. A trap may follow the previous retirement on the next edge. Enabled
mode uses the new trap channel and keeps legacy fault outputs zero; legacy mode
keeps new trap/CSR outputs zero and retains its sticky fault channel. There is
no ambiguous reuse of a four-bit project fault code as mcause.

## T045 implementation and acceptance requirements

1. Implement csr_file.sv and trap_control.sv, feature-aware decode/pipeline/SoC/
   timer integration and a separate real compiled interrupt firmware image.
   Preserve the v0.2 specification as historical evidence; publish a new runtime
   contract and verify both configurations explicitly. Update source/image Tcl
   manifests only after native validation, retaining recoverable prior versions.
2. Use independent CSR/trap/ISA models plus randomized responding memory and
   replayable seeds1 and20261107. Check all six CSR encodings, zero-index versus
   zero-value suppression, rd=x0/rd=rs1, writable masks, read-only/unimplemented
   accesses, serialize hazards and all reset values. Include actual defect mutants.
3. Test IRQ masking/pending/deassertion, timer bit2 and legacy bit1 reload, W1C
   collisions, enable/MRET reevaluation, repeated level IRQ, nested frame handling,
   empty pipeline and each occupied stage, branch redirects, held requests and
   long responses. Match every store/pop exactly once to retirement before entry;
   kill wrong-path faults/effects, and test synchronous trap priority and all causes.
4. Execute compiled software on actual RTL, save/restore a context, service timer,
   MRET and continue an exact instruction sequence without loss/duplication. Add
   signature-based completion plus independently decoded UART IRQ PASS output
   at production divider868. The old fatal-EEI program/expectations remain tested
   in legacy configuration; ECALL cannot be reused as a halt in enabled mode.
5. Run required lint, test-interrupts and the full regression with retained evidence
   and finite native/aggregate limits. Preserve any failed attempt; missing checks
   are NOT RUN. Audit hashes, code/config modes, images, raw bus/retire/trap traces,
   negative controls and both report languages. No formal PASS claim: T023 remains
   owner-skipped. T043 synthesis/route/timing and T032 physical programming keep
   their separate owner authorization gates.

T044 is a document review only. Every feature above is currently NOT IMPLEMENTED /
NOT RUN. Approval selects this design scope; it does not establish compliance,
functional results, timing, resource fit, physical operation or ASIC readiness.
