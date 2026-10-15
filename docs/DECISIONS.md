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
