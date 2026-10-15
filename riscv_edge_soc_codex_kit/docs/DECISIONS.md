# Architecture Decision Records (ADR index)

Status: DRAFT until owner approves T002 milestone.

- ADR-0001: Chosen as 32-bit single-issue 5-stage RV32I teaching-to-portfolio core; not five CPU cores.
- ADR-0002: Initial 64KiB instruction ROM, 64KiB data BRAM. Single clock domain. No caches.
- ADR-0003: A minimal one-outstanding ready/valid local bus with AXI4-Lite optional bridge at extension stage.
- ADR-0004: ISA exceptions/privileged CSR not in MVP; forbid RV32I certification claims.
- ADR-0005: cocotb + Verilator for early simulation; advanced SV/UVM needs a compatible simulator/license.

All changes require a new numbered ADR with trade-offs, backwards compatibility, test impact and owner approval before implementation.
