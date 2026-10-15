# Toolchain manifest (planned — install/verify in T001)

On initial setup record operating system, Python, Verilator, cocotb, RISC-V GCC/binutils, Yosys/SBY, Vivado, and optional LibreLane versions. Pin simulator/plugin versions before relying on CI.

- Python >= 3.10 (harness standard library only); cocotb 2.0 + Verilator >=5.036 is a documented compatible combination, actual local behavior must be verified.
- macOS M3 development host may be used for general development, but Vivado 2025.2 Linux host is the likely FPGA implementation environment; never claim native macOS Vivado support.
- No simulator, Vivado, board, chip fabrication or commercial UVM license is presumed installed/available.
- Makefile targets are created progressively. `make preflight`/`lint` must execute real checks, not `echo PASS`.
