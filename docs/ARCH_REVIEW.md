# T002 owner architecture review

Submission: architecture v0.2-proposed, 2026-10-16. No RTL is implemented.
At submission no owner architecture approval has been recorded. Successful
documentation checks only permit awaiting_review, never automatic completion.

Read ARCH_SPEC.md and ARCH_CONTRACT.json together. Prior v0.1 was a draft; these
are proposed decisions to approve or revise before any dependent implementation.
The proposal preserves the original part and ROM/RAM/UART-TX base addresses.
Source references and verification limitations are documented in the specification.

## Decisions to review

| Decision | Concrete proposal | Trade-off / effect |
|---|---|---|
| A1 Target/clock | Basys 3 xc7a35tcpg236-1, 100 MHz W5, one clock domain | 10 ns is a constraint, not achieved timing |
| A2 Reset | active-high synchronous core; all GPRs zero; RAM/ROM retained; shared fabric cancellation | deterministic DV, extra GPR reset logic, isolated core-only reset unsupported |
| A3 Native buses | separate I/D valid-ready request/response, one outstanding each, minimum 1-cycle response | simple verification, extra memory bubbles; byte enable used for reads AND writes |
| A4 Byte lanes | original byte address plus lane mask, aligned response word, no split misaligned access | efficient BRAM/MMIO lanes; misalignment is an explicit fatal EEI fault |
| A5 Control | reset > oldest fault > memory hold > EX redirect > load-use > advance | WB retires once during hold; branch waits behind older memory |
| A6 Fault/ISA | all 40 RV32I mnemonics targeted, full-drain FENCE, precise fatal EEI halt/reset | no software trap handler, CSR, privileged mode, MRET or interrupts in this baseline |
| A7 Map/peripherals | ROM 0..ffff; RAM 10000..1ffff; UART/GPIO/timer register table in spec | ROM D-read allowed; RAM not executable; RX/status/control offsets newly specified |
| A8 Commit/trace | GPR commit in WB; successful MEM side effect may precede its WB trace by one stage | scoreboard must correlate responses; older faults block younger MEM effects |
| A9 Fetch/reset edges | hold offered stale request stable, drain/kill response, shared reset cancels both endpoints | avoids protocol violations; redirect latency may include a drain bubble |
| A10 Later interrupts | mandatory T044 reviewed trap/CSR revision and T045 interrupt verification before final FPGA results | initial fatal EEI is an intermediate contract; interrupt behavior needs a new approved revision |

A6 is an intentional alternative to adding a privileged CSR/trap subsystem now.
If software-resumable machine traps or interrupts are required immediately,
reject/revise A6 before approval. Later interrupt support requires a separate
architecture revision and owner gate (T044/T045), not an undocumented extension
of this EEI. This later support is required by the original project objective.
This is a base-instruction/EEI target, not a certified or privileged RISC-V platform.

Detailed map choices include UART RX one-byte holding slot, low-lane read/pop,
busy-TX backpressure, disabled-TX error, sticky framing/overrun, GPIO set/clear and
a 32-bit timer with W1C status. Review the exact table and collision priorities
rather than approving only the CPU diagram.

## Required acceptance evidence

- All declared core ports, widths and directions are explicit and compared with
  the machine-readable contract.
- Reset/handshake/age ordering and side-effect points have unambiguous rules.
- Every base mnemonic is listed; subset milestones cannot close final ISA scope.
- All map regions/register offsets are in range, aligned and nonoverlapping.
- Requirements map to real backlog IDs with future RTL tests explicitly NOT RUN.
- Target agrees with original XPR and owner-confirmed local configuration.
- Automated consistency checks and their negative mutation tests pass.
- Both dated reports and T002 evidence exist; no approval was fabricated.

## What automation does and does not prove

check_arch_spec.py checks document/JSON consistency and structural invariants.
Its mutation tests deliberately corrupt inputs to ensure errors are detected.
It does not prove protocol timing, RTL behavior, EEI correctness, FPGA timing,
BRAM inference, formal properties or peripheral hardware. All those require the
later tasks listed in VERIFICATION_PLAN and BACKLOG.

## Owner-only action after reviewing the final receipt and diff

Review the contract SHA-256 printed by the checker in the T002 receipt, the
proposed decisions above, source links and all remaining limitations. Request
changes if any decision is unacceptable. Do not approve by default.

If accepting this precise submission, the owner may run:

~~~powershell
python -B scripts/harness.py approve T002 --confirm-owner-review
~~~

The agent must not execute that command for the owner. Keep this review and the
receipt as the identity of the proposal; approval state lives in .harness/state.json.
A new architecture change needs a new reviewed version/ADR. After owner approval,
the next task is T003 on a new eligible day; no second task is started today.

Unattended automation remains disabled under the current unrestricted session.
This review does not authorize downloads/installation, FPGA programming, system
changes, scheduling, new clock domains, a different FPGA or repository publication.
The owner separately authorized read-only official documentation access today.
