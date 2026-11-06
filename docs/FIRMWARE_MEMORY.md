# T026 compiled boot image and synchronous memory banks

Completed 2026-11-06 from clean T025 checkpoint1dd3dae. All four required gates
PASS on attempt3; initial preparation was November4. Earlier failures are retained.
No approved architecture, ISA, map, clock, reset priority or CPU RTL change.

## Toolchain and reproducible image

Existing AMD tools were found under C:/AMDDesignTools/2025.2/gnu/riscv/nt/bin.
The riscv64-unknown-elf-gcc.exe filename is a wrapper that reports the actual
target riscv32-xilinx-elf/GCC13.4.0 and supports rv32i/ilp32. Its linker reports
GNU2.43.1.20241111; objcopy/readelf/objdump report2.39.0.20220819. Use observed
versions, not filename assumptions. Project-local .harness/software_toolchain.json
pins absolute commands, version lines, wrapper hashes and actual cc1/as/ld
components. No installation, download or global PATH/config change occurred.

sw/boot.S and smoke.S assemble explicitly with -march=rv32i -mabi=ilp32,
-misa-spec=20191213 and no relaxation. There are no compressed/CSR/privileged
instructions, libc, crt, implicit runtime library or UART dependencies. Actual
GNU ld uses elf32lriscv, fatal warnings and the project linker script. Tool output,
ELF, map, disassembly and readelf reports are retained per invocation under build/.

The linker uses approved ROM0x00000000..0x0000ffff and RAM0x00010000..0x0001ffff.
Code/rodata run and load in ROM. Initialized data runs in RAM and loads immediately
after ROM code. BSS is NOLOAD. Stack begins at0x20000, grows downward and reserves
the top4KiB; actual ROM overflow and RAM/stack collision must cause specific link
failures. Startup copies aligned data, clears BSS, calls main and terminates via
the approved initial fatal-halt ECALL. It does not configure future trap CSRs.
This small assembly startup does not provide a complete C/C++ runtime.

The initial actual build has236 code bytes,8 initialized data bytes loaded at
ROM0xec and run at RAM0x10000; RAM segment size20 includes12 BSS bytes. Code and
data together occupy244 ROM bytes. The full64KiB image pads remaining words0,
which are illegal instructions if executed, rather than silently extending code.
scripts/firmware_image.py independently parses ELF32 little-endian RISC-V class,
machine/entry/flags, bounds, permissions, LMA/VMA segments and required symbols.
Its64KiB image must equal actual objcopy output byte-for-byte. The committed
rom_init.mem has16384 complete8-hex-digit words, little-endian within each word.
Every verification rebuilds it and compares; no stale prebuilt image fallback or
automatic source-image overwrite is allowed by the verification gate.

The documented linker mechanisms are GNU [MEMORY](https://sourceware.org/binutils/docs/ld/MEMORY.html),
[LMA/AT>](https://sourceware.org/binutils/docs/ld/Output-Section-LMA.html) and GCC
[RISC-V architecture/ABI options](https://gcc.gnu.org/onlinedocs/gcc/RISC-V-Options.html),
read as official documentation only. No compiler package or third-party RTL was fetched.

## Independent boot scope

The existing independent RV32ISS executes the real compiled ROM with two dirty
RAM seeds1/20261104, then each warm reset. It checks copied data, cleared BSS,
restored stack, a0=0, signature0x600d600d and precise ECALL fault at halt_ecall.
Each of four preparation model runs retires72 instructions. Memory outside data/
BSS/used stack retains a warm-reset witness. Actual corrupted code must fault
illegal at PC0; corrupted ROM data must reach the smoke program's a0=1 failure.
These are compiled firmware/independent-model results, not actual pipeline or
SoC execution. T031 must execute this image with the real SoC/fabric later.

## Primitive RTL interfaces and reset

rtl/memory/boot_rom.sv: fixed64KiB, two independently enabled14-bit WORD-address
read ports on one clk_i, each32-bit data and registered valid. INIT_FILE defaults
to rom_init.mem. Addresses/enables sample on a rising edge; outputs update after
that edge, hold when disabled, and valid clears when disabled. Synchronous rst_i
clears output data/valid and dominates read enables; it never changes ROM contents.

rtl/memory/data_ram.sv: fixed64KiB,14-bit word address, enable,4 byte write enables
and32-bit write data, registered read data/valid. FPGA initialization sets memory
to0. Enabled access reads the OLD word at the same edge as any selected byte write
(read-first). Disabled access has no write and holds data/clears valid. Reset
clears outputs/valid, blocks writes and retains all contents. Byte0 is bits7:0.
The module contains no fabric clock, asynchronous memory read or reset loop over
memory state. Only FPGA initialization uses a memory initialization loop.

These are memory primitive ports, not a local req/rsp adapter. T031 must select
regions/permissions, retain/stall responses, enforce at least one edge between
local request and response consumption, and gate a store at its successful
response handshake. Primitive write enable must never be tied unconditionally to
request acceptance. No such adapter or SoC hookup is implemented by T026.

## Independent memory tests and inference

Seven ELF/memory policy tests challenge wrong class/target/flags/table bounds,
overlap, outside ROM/RAM, missing symbols, word order/capacity, read-first byte
updates, independent ROM enables and warm-reset retention. Seventeen general
acceptance-policy tests include new missing/aliased initialization input checks.
Generic lint validates init files and copies declared images only into its own
project-local probe directory, retaining all existing diagnostic/failure rules.

The memory testbench instantiates two actual boot_rom modules: a unique full-range
address-pattern ROM and the real compiled-image ROM, plus data_ram. Two seeds each
drive33125 edge vectors (66250 total expected): all16384 addresses on both ROM
ports, complete RAM write/read traversal, all16 lane masks at boundaries, enable
holds, read-first collisions, random accesses and resets with retained contents.
The independent Python reference represents RAM as bytes; expected read data is
captured before writes. The SV test also checks outputs remain unchanged between
edges after address/control changes. Wrong-expected and empty-vector actual XSim
runs must fail with exact diagnostics and no success marker. Every run saves WDB,
vectors and argument/Tcl files with hashes. No analog/CDC or bus-fabric proof.

Actual selected-part Vivado must infer RAMB cells in BOTH the ROM and RAM bank
hierarchies, with no latch/black box and clean structural DRC. Resources are
reported from that actual probe, not estimated as timing/hardware evidence.
No placement, routing, bitstream, physical board or ASIC operation occurs here.

## Commands and remaining work

```powershell
python -B scripts/test_rtl_checks.py
python -B scripts/test_firmware.py
python -B scripts/harness.py finish T026 --evidence evidence/daily/T026.md
```

The preparation compiler/ISS/overflow run passed; its9 exact source versions are
archived under evidence/prepare/T026-initial-build-sources.* before adding component
hash pins. It is historical, not the current gate. Fresh full gates remain
pending: lint/test-firmware/both whitespace, max3 finish attempts. Registry now
has21 regression targets, retaining all20 earlier targets. Full21 regression is
not yet run for this bounded task. Current XPR remains the T025 diagnostic shell;
it is not changed to a partially integrated SoC. T023 stays owner-skipped/NOT RUN.

## Retained first attempt and mapping repair

First full attempt `evidence/runs/T026/attempt-1-20261105T044625439841Z.json`
reports FAIL/FAIL/PASS/PASS. All compiler/ISS/overflow controls,66250 memory
vectors and intended XSim negatives passed. Both synthesis probes inferred
16ROM+16RAM RAMB36E1 cells with no errors/critical warnings, but each emitted
two Synth8-6841 byte-write decomposition warnings at14-bit address width. Strict
warning rejection correctly kept both gates failed despite success markers.

Archived120 source inputs and2124 generated artifact hashes under
evidence/failed_sources/T026/attempt-1/. Add only ram_decomp="power" to the RAM
array, as the actual Vivado diagnostic recommends and AMD [UG901](https://docs.amd.com/api/khub/documents/4JeDC1EhFUthUXDz8CF50w/content)
documents. This explicitly selects depth banking for native byte-write handling;
the memory/reset/latency contract, tests, seeds, checks and budgets stay unchanged.
This mapping can add address decode delay; no routed timing or measured power
improvement is claimed. No warning filter/severity change is made. Attempt2 must
rerun every required gate and report its actual inferred resources.

## November 6 recovery of completed second attempt

Attempt2 `evidence/runs/T026/attempt-2-20261105T045329256744Z.json` finished with
FAIL/PASS/PASS/PASS. The RAM mapping change removed both warnings. Fresh firmware
gate passed44 checks/27 commands, all66250 memory vectors, model/overflow/negative
controls and actual16ROM+16RAM BRAM inference. Generic lint passed the memory
probe but Vivado crashed after the unchanged register_fixture probe had completed
zero-warning/error synthesis, DRC and its exact marker. Native exit4294967295 and
EXCEPTION_ACCESS_VIOLATION remain a failure. The small crash log says no stack
trace is available; its native cause remains undetermined.

Archived120 exact inputs and2284 generated hashes under
evidence/failed_sources/T026/attempt-2/, including the text crash report. All current
firmware source hashes still match the passing second-attempt receipt. November6
resumes the same task with one finish attempt remaining. Retry all gates without
changing RTL, checks, seeds or timeouts; do not substitute the earlier partial
successes. Prior November4 reports remain unchanged by this recovery session.

## Final verified results

`evidence/runs/T026/attempt-3-20261106T205251043860Z.json` reports all four gates
PASS/exit0: lint, test-firmware, working and staged whitespace. Lint passed33
checks/18 commands, including the unchanged fixture and intended latch rejection.
Firmware gate passed17 general policy tests,7 independent ELF/memory tests and
44 actual tool checks/27 commands. Current tool receipts:
`lint-20261106T205251466810Z.json` and `firmware-20261106T205810599677Z.json`.

Both seeds passed33125 memory vectors,66250 total. The final audit independently
reads the actual vector artifacts: each seed enabled all16384 addresses on ROM A,
ROM B and RAM, all16 RAM byte masks and12 reset edges. Nonzero retained-memory
witnesses remain after the final reset. Four independently modeled compiled boots
each retire72 instructions and terminate at the expected ECALL; these are model
observations, not actual compiled pipeline/SoC execution. Both memory negatives,
corrupt-code/data controls and real linker overflow controls passed unchanged.

Actual synthesized memory banks contain16 ROM and16 RAM RAMB36E1 cells, with no
warnings/errors and clean structural DRC. These are standalone memory synthesis
resources, not complete SoC utilization, timing or measured power.
`evidence/t026-final-audit-2026-11-06.json` binds two current tool receipts,
46 source hashes,92 distinct artifact hashes and1017 preserved tracked files.
It validates both120-input failure archives,2124/2284 earlier generated hashes,
the9-source initial preparation archive, compiler components and exact pre-gate
evidence texts. The two November4 reports are unchanged during November6 recovery;
the original kit/XPR/cache match their already documented prior checkpoint.

T026 is completed without owner approval being generated. Mandatory progress is
26 completed plus one owner-skipped(T023) out of41. After inspected local commit,
query the harness and begin T027 from a clean baseline. Current XPR stays the
diagnostic board shell; full21-target regression, compiled SoC execution, complete
CDC, formal proof, routed timing, hardware and ASIC evidence are not claimed here.
