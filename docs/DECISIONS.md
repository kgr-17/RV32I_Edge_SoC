# Architecture Decision Records (ADR index)

Status: DRAFT until owner approves T002 milestone.

- ADR-0001: Chosen as 32-bit single-issue 5-stage RV32I teaching-to-portfolio core; not five CPU cores.
- ADR-0002: Initial 64KiB instruction ROM, 64KiB data BRAM. Single clock domain. No caches.
- ADR-0003: A minimal one-outstanding ready/valid local bus with AXI4-Lite optional bridge at extension stage.
- ADR-0004: ISA exceptions/privileged CSR not in MVP; forbid RV32I certification claims.
- ADR-0005: cocotb + Verilator for early simulation; advanced SV/UVM needs a compatible simulator/license.

All changes require a new numbered ADR with trade-offs, backwards compatibility, test impact and owner approval before implementation.


## ADR-0006: Engineering bootstrap workflow

Status: implemented under the owner's explicit bootstrap authorization on 2026-10-14.
Use the existing Vivado project in place, preserve an original Git/ZIP baseline,
retain the kit untouched, and use root-level portable Python tooling. Keep
America/Los_Angeles daily claims and bilingual append-only reports. Unattended
automation is disabled under unrestricted permissions. This is a workflow
decision, not architecture approval; ADR-0001 through ADR-0005 remain draft.
Trade-off: no enforced isolation exists in this attended session. Before future
unattended work, configure actual sandbox controls and inspect them.


## T002 architecture submission v0.2 - all decisions below PROPOSED

The draft ADR-0001/2/3 remain the starting point. ADR-0004's deferred exceptions
and simulator-only failure policy are superseded in this proposal by ADR-0009.
ADR-0005 is a toolchain candidate, not an established requirement or simulator
compatibility claim; T003 must evaluate installed XSim and any approved alternatives.
The owner has authorized creating the review proposal, not implementing it.

### ADR-0007: One clock and deterministic core reset

Decision: Basys 3 100 MHz W5 input, synchronous active-high core reset, all GPRs
zero, warm-reset memory retained, wrapper synchronized release. Shared local
protocol reset cancels pending transactions. Trade-off: GPR reset logic and a
strict common-reset integration assumption. Verification: reset during every
request/response phase, no stale retirement, real CDC/STA later. No measured Fmax.

### ADR-0008: Separate one-outstanding local request/response buses

Decision: local_mem_v1, byte effective address plus selected-lane enables for both
loads and stores; response latency at least one edge, no cancellation except
shared reset. Redirect marks an offered fetch killed and drains it. Trade-off:
additional bubbles and no AXI-native interface, but explicit stable transactions.
Read/pop and write effects happen only on successful response acceptance.
Verification: variable latency, payload stability, no repeated request/effect,
byte-lane and reset tests. Future AXI adapters need their own reviewed reset policy.

### ADR-0009: Complete base-instruction target with fatal EEI observation

Decision: all 40 RV32I mnemonics, conservative full-drain FENCE and precise
fault/halt outputs for SYSTEM, illegal and access/alignment faults. No Zicsr,
machine-mode handler or in-core resume. This is a selected EEI, not privileged
compliance or certification. Trade-off: no general system calls or resumable
traps, smaller initial scope. Verification: T041 complete ISA/EEI matrix,
wrong-path fault kill and no younger memory effect. Owner may choose a richer
trap/CSR design instead BEFORE approval; that would require a revised contract.

### ADR-0010: Explicit map and byte-aware MMIO proposal

Decision: keep ROM/RAM capacities and original base addresses; ROM is data-readable
but not writable, RAM is nonexecutable, unmapped accesses error. Define RX/control,
GPIO aliases and timer registers in ARCH_SPEC. Trade-off: Harvard permissions,
32-bit timer and simple one-byte RX slot. Verification: linker/fabric consistency,
every permission, lane side effect and peripheral collision. No memory map has
yet been verified in RTL, and software-visible changes need owner review.

### ADR-0011: Age-ordered faults, held-stage rules and WB trace

Decision: extend ordinary priority with oldest-fault termination; loads forward
only from WB; older WB can retire once during MEM hold. Successful MEM effects
may precede their ordered WB trace; older faults must already be excluded.
Trade-off: conservative stalls and a scoreboard that correlates two observations.
Verification: oldest fault vs younger store, stale operand retention, duplicate
retire detection, wrong-path fetch draining, and all hazard/priority pairs.

Approval for ADR-0007 through ADR-0011 is PENDING. The exact proposed 38-port
interface and 22 requirement IDs are in ARCH_CONTRACT.json. The T002 receipt
captures its SHA-256. None of these decisions changes RTL, XPR, XDC or hardware today.

### ADR-0012: Preserve the later interrupt milestone

Status: PROPOSED. The original objective requires later interrupt support; it is
not an optional AXI/DMA extension. Add T044 owner review of the trap/CSR/interrupt
revision and T045 implementation/verification after initial SoC simulation, before
final routed FPGA and physical evidence. The v0.2 fatal EEI is an intermediate
baseline, not an excuse to omit interrupts from project completion. Trade-off:
additional implementation and validation scope, with explicit review before any
new ports/CSR/trap priorities. This task only restores backlog traceability.
