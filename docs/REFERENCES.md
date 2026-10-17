# Reference index and source verification status

The links below were imported from the original kit; their presence is not proof
that all resources were fetched or validated. On 2026-10-16 the owner authorized
official documentation reads for T002. The RV32I 2.1 chapter and EEI introduction
at the pinned 20240411 snapshot, plus Digilent's Basys 3 manual, were read.
See ARCH_CONTRACT.json and evidence/t002_sources.json for exact URLs and scope.
Other links remain reference candidates and were not revalidated by this task.

## RISC-V / verification

- RISC-V Architectural Certification Tests and ACT4 (official, not full verification): https://github.com/riscv/riscv-arch-test
- RISC-V ISA manual / specification repository: https://github.com/riscv/riscv-isa-manual
- lowRISC Ibex production-quality core & SV/UVM + ISS cosimulation: https://github.com/lowRISC/ibex
- OpenHW CV32E40P verification and reports: https://github.com/openhwgroup/cv32e40p
- lowRISC SystemVerilog coding guide: https://github.com/lowRISC/style-guides/blob/master/VerilogCodingStyle.md
- lowRISC DV style guide: https://github.com/lowRISC/style-guides/blob/master/DVCodingStyle.md
- cocotb 2.0 simulator support; Verilator >= 5.036 per this release: https://docs.cocotb.org/en/v2.0.0/simulator_support.html
- SymbiYosys SBY proof tool docs: https://github.com/YosysHQ/sby

## FPGA / ASIC

- Digilent Basys3 reference manual: https://digilent.com/reference/programmable-logic/basys-3/reference-manual
- AMD Vivado timing analysis UG906 2026.1: https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Timing-Analysis
- Vivado CDC UG906: https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Report-Clock-Domain-Crossings
- LibreLane (continuation of OpenLane 2): https://github.com/chipfoundry/openlane-2
- OpenROAD: https://github.com/The-OpenROAD-Project/OpenROAD

## Agent engineering

- Codex repository AGENTS.md behavior: https://developers.openai.com/codex/agent-configuration/agents-md
- Codex best practices: https://developers.openai.com/codex/learn/best-practices
- Codex scheduled tasks and desktop/web caveats: https://developers.openai.com/codex/automations

## Inspiration repos: REFERENCE ONLY, NOT copied source

- Berkeley Sodor microarchitecture variants: https://github.com/ucb-bar/riscv-sodor
- Ibex core interfaces and verification approach: https://github.com/lowRISC/ibex
- CV32E40P core/verification strategy: https://github.com/openhwgroup/cv32e40p

Pin and record specific dependency commits/tags before using a third-party tool or reference. Check licenses and do not assert that code was independently written if copied.
