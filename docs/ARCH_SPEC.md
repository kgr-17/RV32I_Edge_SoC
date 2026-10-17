# Architecture v0.2 - proposed contract for owner review

Status: PROPOSED, NOT APPROVED, NOT IMPLEMENTED. Task T002, 2026-10-16.
This replaces the ambiguous v0.1 proposal; the prior draft remains recoverable in
Git at c3035b9 and in the untouched original kit. No RTL/XDC/XPR change is made.
Approval of this proposal does not establish functional compliance or timing.

The machine-readable companion is docs/ARCH_CONTRACT.json. Its approval field
remains pending_owner_review. Document and contract must be reviewed together.
Only the owner may approve T002; no agent approval record is being created.

## 1. Target, scope and sources

Owner-confirmed Digilent Basys 3, part xc7a35tcpg236-1. The original XPR has no
sources, constraints or top. Vivado 2025.2 startup/part availability was verified
on day 1; synthesis, implementation and hardware have NOT RUN.

One hart, 32-bit little-endian data, 32 GPRs, fixed 32-bit instructions. The initial
reference core and final five-stage core implement the same proposed architectural
and bus contract. Baseline final ISA target is RV32I 2.1, pinned to the ratified
20240411 manual for reproducibility. No M/A/F/D/C, Zicsr or Zifencei is claimed;
no privileged machine mode, CSR trap handler, MMU, cache, predictor or Linux.

Sources read with explicit owner authorization on 2026-10-16:

- [S-ISA: RV32I 2.1](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html):
  instruction behavior and the permitted EEI/fence choices.
- [S-EEI: execution environment](https://docs.riscv.org/reference/isa/v20240411/unpriv/intro.html):
  address-space permissions and fatal-trap policy.
- [S-BOARD: Basys 3 manual](https://digilent.com/reference/_media/reference/programmable-logic/basys-3/basys3_rm.pdf):
  sections 4/5, printed page 7 in the fetched edition; clock and UART connections.

The remaining behavior below is a project design proposal, not copied third-party
RTL. No tool, package, IP, full core or board constraints were downloaded.

## 2. Clock and reset [R-CLOCK, R-RESET, R-CDC]

Use the documented 100 MHz oscillator on W5, one core/SoC clock and a proposed
10.000 ns implementation constraint. This is an input/constraint, not measured
Fmax or timing closure. UART and timer use clock enables; no fabric-created clock.

Core rst_i is active-high and synchronous to clk_i. At a rising reset edge:
PC becomes 0; x1..x31 become 0; x0 remains 0; interstage valid bits, request state,
fetch kill state, retire_valid/order and fault outputs clear. Outputs carrying
unused metadata are zero. No request, response acceptance or retirement counts
while reset is asserted. Gate combinational valid/ready enables with reset too.

The SoC wrapper and local memories share reset, cancel pre-reset protocol
transactions and discard pending responses. ROM and RAM contents survive warm
reset; already committed memory/peripheral effects are not rolled back. Memory
initialization is a separate firmware/build action. Isolated core reset against
a live non-reset memory/fabric is unsupported by this v1 protocol.

External reset assertion may asynchronously set a wrapper synchronizer; deassertion
must pass at least two clk_i edges before the core reset releases. External
switches/UART RX require separate synchronizers. The core itself has no async
register reset. T025/T029 must review startup and reset constraints; physical
bring-up requires an explicit reset rather than assuming a power-on sequence.

## 3. Pipeline and architectural state [R-RF, R-X0]

| Stage | Responsibility | State carried forward |
|---|---|---|
| IF | request PC, accept/kill fetch response | valid, PC, instruction or fetch fault |
| ID | decode, read GPRs, immediate, operand-use flags | source/destination IDs, controls, fault token |
| EX | ALU, effective address, branch/JAL/JALR compare/target | result, original byte address, store data, fault token |
| MEM | issue exactly one local data transaction and wait | completed data/error, byte enables, trace metadata |
| WB | one in-order successful retire or precise fault | GPR write, retire trace, sticky fault observation |

Interstage valid bits govern every effect; an invalid bubble cannot write a GPR,
request data memory, redirect, or retire. The register file has two combinational
read ports and one rising-edge WB write. WB-to-ID read bypass returns the retiring
value when source==nonzero destination. x0 never changes. Do not infer latches.

ID operand values held through a long stall must not become stale after the
producing WB event disappears: capture the forwarded value while held or reread
the GPR when resuming. A corresponding directed test is mandatory.

## 4. Control priority and hazards [R-FWD, R-LOAD-USE, R-HOLD, R-REDIRECT]

Priority for conflicting age-eligible events:

reset > oldest_fault > memory_hold > redirect > load_use > advance

oldest_fault means the oldest fault token at the architectural termination point,
not any younger illegal decode. All exceptions obey instruction age. An older
taken branch kills younger instruction/fetch faults. The quoted order extends
v0.1's ordinary priority by explicitly adding precise fault termination.

While MEM waits for request acceptance or response, hold IF/ID, ID/EX and EX/MEM.
WB may retire an already-complete older instruction exactly once, then clear its
valid bit while younger stages remain held. MEM must remember that its request
was accepted, so a held MEM instruction cannot reissue it.

EX resolves BEQ/BNE/BLT/BGE/BLTU/BGEU, JAL and JALR. Legal redirect wins over a
younger dependency stall and kills younger instructions. A pending redirect waits
behind older MEM backpressure. A bad target becomes a fault on the branch/jump
itself; a legal but inaccessible target faults later as that target fetch.

Forwarding priority: nearest valid older EX/MEM result, then MEM/WB, then captured
operand. Only enabled nonzero GPR destinations forward. Load results forward
from WB only, never from an unreturned response or an address-generation result.
The consumer waits until WB forwarding is actually available; no one-cycle CPI
promise is made. Store payload, branch compare and JALR base use the same rules.

## 5. Local memory protocol v1 [R-MEM, R-LANES, R-FETCH-KILL]

Separate instruction and data request/response buses; at most one accepted
unanswered transaction PER bus. Signals are sampled at clk_i rising edges.
A transfer occurs only with valid && ready && !rst_i. There are no request IDs.

Once request-valid is offered, hold valid AND all payload stable until accepted,
unless shared reset cancels it. After acceptance do not issue that request again.
Every accepted request produces exactly one response, with at least one full
clock-edge interval of latency. A response cannot complete in its request's
acceptance edge. Response producer holds valid/data/error until ready. The CPU
does not issue a replacement on the same edge as consuming the previous response;
a bubble is acceptable and makes the initial one-outstanding implementation clear.

imem_req_addr_o is a four-byte-aligned byte address. A successful response contains
the aligned 32-bit instruction. Instructions are never split across two requests.
A fetch error creates an instruction-access-fault token, with instruction bits 0.

dmem_req_addr_o is the ORIGINAL byte effective address. The fabric selects the
containing aligned word with addr & ~3. dmem_req_be_o identifies lanes for BOTH
reads and writes; it is not just AXI WSTRB. Legal masks are 0001/0010/0100/1000,
0011/1100 and 1111, consistent with the address and naturally aligned access size.
Read wdata is 0. Store data is shifted into selected word lanes, unused lanes 0.
Read data returns the aligned full word; LSU shifts and sign/zero extends.

Misaligned halfword/word operations fault before emitting a data request.
No split transaction, partial store or misalignment emulation occurs. Alignment
checking precedes address-map checking for a single misaligned data operation.
Loads targeting x0 still access memory and preserve errors/MMIO side effects.

No memory or peripheral write effect occurs at request acceptance. Successful
response acceptance is the transaction's one effect point. An error response
must not change memory/peripheral state. If response-valid stalls, its payload
is held and its side effect is deferred. A read snapshot may be captured when
response-valid is created; any consume/pop effect waits for its handshake.

No request may be lost during redirect: a previously offered/accepted stale
instruction fetch is marked killed, completes under the same stability rules,
and is drained/discarded. A saved target PC is fetched after that drain. A killed
fetch fault cannot become an architectural fault. On fatal halt, drain already
offered instruction work but do not initiate new fetches.

Example: request accepted at edge n, no completion at n; earliest response
acceptance n+1; no replacement request at that same response edge. If request
ready is low at n/n+1, keep address/data/be/write/valid unchanged. Reset is the
explicit exception and cancels both ends of the local interface.

## 6. Precise execution-environment termination [R-FAULT, R-STORE-ORDER]

Propose a small bare-metal EEI with observable fatal traps, not privileged mode.
ECALL is an environment request and EBREAK is a debugger request. This EEI records
them as distinct fatal fault events and halts until reset. It does not provide
system-call services, an in-core handler, MRET, CSRs or interrupt support in v0.2.
The owner's requested later interrupt support remains mandatory: T044 reviews
the trap/CSR/interrupt revision, and T045 implements/verifies it before final
FPGA implementation/hardware evidence. Do not add IRQ ports or CSRs implicitly
to this initial contract or declare the whole project complete without that work.

Illegal instructions, instruction/data misalignment, inaccessible addresses and
bus errors also terminate through this channel. Known faults travel as age-tagged
tokens to WB; they cannot immediately stop older work. Older instructions finish,
the faulting instruction does not retire/write, and every younger effect is killed.
An older WB fault suppresses a younger MEM request BEFORE its acceptance.

A successful store or MMIO read may affect the fabric in MEM before its WB trace,
but only after every older instruction is known nonfaulting. It retires once in
WB next, in order. Scoreboard correlates the one accepted response with the later
retire metadata; timing of an effect is not falsely equated with the trace pulse.
A failing store response never commits any bytes.

fault_valid_o is sticky until reset; fault_pc/insn/code/tval remain stable while
it is set. Observe its first assertion as one termination event, not repeated
events. Drain any stale fetch; no new architectural work may start. Codes are
project-defined 4-bit diagnostics, NOT mcause or a privileged-ISA claim:

| Code | Name |
|---|---|
| 1 | ILLEGAL_INSN |
| 2 | INSTR_ADDR_MISALIGNED |
| 3 | INSTR_ACCESS_FAULT |
| 4 | LOAD_ADDR_MISALIGNED |
| 5 | LOAD_ACCESS_FAULT |
| 6 | STORE_ADDR_MISALIGNED |
| 7 | STORE_ACCESS_FAULT |
| 8 | ECALL |
| 9 | BREAKPOINT |

tval is the bad target/address for address faults, the instruction word for illegal
decode, and 0 for ECALL/EBREAK. fault_pc names the causing instruction; an
inaccessible redirected fetch names its target PC, not the prior legal jump.
For an inaccessible instruction fetch, fault_insn=0. A not-taken conditional
branch never faults merely because its hypothetical target is misaligned.

## 7. Core ports [R-RETIRE]

All directions below are relative to rv32_core. Both reference and pipelined
cores must expose this contract or an explicitly reviewed adapter.

| Signal | Direction | Bits |
|---|---|---|
| clk_i | input | 1 |
| rst_i | input | 1 |
| imem_req_valid_o | output | 1 |
| imem_req_ready_i | input | 1 |
| imem_req_addr_o | output | 32 |
| imem_rsp_valid_i | input | 1 |
| imem_rsp_ready_o | output | 1 |
| imem_rsp_rdata_i | input | 32 |
| imem_rsp_err_i | input | 1 |
| dmem_req_valid_o | output | 1 |
| dmem_req_ready_i | input | 1 |
| dmem_req_addr_o | output | 32 |
| dmem_req_write_o | output | 1 |
| dmem_req_wdata_o | output | 32 |
| dmem_req_be_o | output | 4 |
| dmem_rsp_valid_i | input | 1 |
| dmem_rsp_ready_o | output | 1 |
| dmem_rsp_rdata_i | input | 32 |
| dmem_rsp_err_i | input | 1 |
| retire_valid_o | output | 1 |
| retire_order_o | output | 64 |
| retire_pc_o | output | 32 |
| retire_next_pc_o | output | 32 |
| retire_insn_o | output | 32 |
| retire_rd_write_o | output | 1 |
| retire_rd_o | output | 5 |
| retire_rd_wdata_o | output | 32 |
| retire_mem_valid_o | output | 1 |
| retire_mem_write_o | output | 1 |
| retire_mem_addr_o | output | 32 |
| retire_mem_be_o | output | 4 |
| retire_mem_wdata_o | output | 32 |
| retire_mem_rdata_o | output | 32 |
| fault_valid_o | output | 1 |
| fault_pc_o | output | 32 |
| fault_insn_o | output | 32 |
| fault_code_o | output | 4 |
| fault_tval_o | output | 32 |

retire_valid_o pulses for one successful instruction, with no input backpressure.
retire_order_o starts at 0 on the first event and increments once per event.
retire_pc_o/next_pc_o describe actual control flow. GPR write metadata is enabled
only for a real nonzero register write; otherwise rd/write/data are 0.

Memory metadata records the original byte address, mask, shifted store word or
aligned raw read word from the accepted response. A load to x0 still has memory
metadata. Non-memory instructions report zero memory metadata. Capture values
for WB so a later transaction cannot overwrite them. Faulting instructions
have no successful retire event. After reset valid is 0 until a real retirement.
The trace is project-specific, not RVFI compliant merely because it is similar.

## 8. ISA scope and decode contract [R-ISA, R-FENCE]

- upper: LUI, AUIPC.
- jump: JAL, JALR.
- branch: BEQ, BNE, BLT, BGE, BLTU, BGEU.
- load: LB, LH, LW, LBU, LHU.
- store: SB, SH, SW.
- op_imm: ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI.
- op: ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND.
- ordering: FENCE.
- system: ECALL, EBREAK.

That is 40 base mnemonics; intermediate MVP subsets are implementation steps only.
NOP and legal HINT encodings execute with their ordinary harmless behavior.
Reserved/nonimplemented instruction encodings are illegal under this project EEI.
The decoder must validate funct fields and shift-immediate encodings rather than
accept every matching major opcode. MUL, DIV, compressed, CSR and FENCE.I are
outside the declared target; no -march=rv32im or privileged binary support.

Select a conservative serializing FENCE: wait for all older memory/I/O responses,
block younger effects, then retire. Ignore its rd/rs1/fm/pred/succ for purposes of
choosing this stronger full drain, including reserved FENCE configurations.
Do not classify those ignored FENCE fields as illegal; this preserves base
forward compatibility. No cache, write buffer, DMA or second hart exists.

Control-target arithmetic wraps to 32 bits; JALR clears bit 0 before four-byte
alignment checking. Signedness, byte lanes, immediates and all fault cases need
independent tests. T041 must close the full matrix against the selected EEI;
no RISC-V certification or privileged compliance claim follows from this proposal.

## 9. Proposed memory map [R-MAP]

| Region | First byte | Last byte | D load | D store | I fetch |
|---|---|---|---|---|---|
| ROM/BRAM | 0x00000000 | 0x0000ffff | yes | fault | yes |
| RAM/BRAM | 0x00010000 | 0x0001ffff | yes | yes | fault |
| UART | 0x10000000 | 0x1000001f | defined registers | defined registers | fault |
| GPIO | 0x10000020 | 0x1000003f | defined registers | defined registers | fault |
| Timer | 0x10000100 | 0x1000010f | defined registers | defined registers | fault |

All unallocated addresses/register offsets and writes to read-only words produce
an error response. ROM is separately accessible from both I and D ports, permitting
read-only constants without writable code. Linker will place code/rodata in ROM,
data/BSS/stack in RAM. No executable RAM or self-modifying code in this EEI.

ROM and RAM are 64 KiB each, preserving v0.1 capacities. Their logical total is
1,048,576 data bits, below the board's documented 1,800 Kbit BRAM capacity. Actual
BRAM packing, inference, extra buffers and utilization require synthesis; no
resource result is claimed. Firmware initialization and reset policy must agree.

## 10. Peripheral map proposal [R-UART]

All registers occupy aligned 32-bit words with defined little-endian byte enables.
Reserved bits read 0 and ignore writes. Reads of write-only words return 0.
Read-only writes fault. Selected low byte controls byte-wide data/pop behavior;
accesses to unrelated byte lanes cannot consume RX data. No interrupts initially.

| Address | Register | Proposed contract |
|---|---|---|
| 0x10000000 | UART_TXDATA | write low byte once; busy backpressures; reads 0 |
| 0x10000004 | UART_STATUS | RO: bit0 TX_READY, bit1 RX_VALID, bit2 OVERRUN, bit3 FRAME_ERROR |
| 0x10000008 | UART_RXDATA | RO: low byte head; successful low-lane read consumes; empty returns 0 |
| 0x1000000c | UART_CTRL | bit0 RX_ENABLE, bit1 TX_ENABLE, reset 3; bits8/9 W1C overrun/frame-error |
| 0x10000020 | GPIO_OUT | RW lower 16-bit LED latch, reset 0 |
| 0x10000024 | GPIO_IN | RO lower 16-bit synchronized switch sample |
| 0x10000028 | GPIO_SET | WO selected 1 bits set output latch |
| 0x1000002c | GPIO_CLEAR | WO selected 1 bits clear output latch |
| 0x10000100 | TIMER_COUNT | RW 32-bit counter, reset 0 |
| 0x10000104 | TIMER_COMPARE | RW 32-bit compare, reset 0 |
| 0x10000108 | TIMER_CTRL | bit0 enable, bit1 auto-reload; reset 0 |
| 0x1000010c | TIMER_STATUS | bit0 sticky match, W1C, reset 0 |

UART: proposed 115200 baud, 8 data bits, no parity, one stop bit, idle high.
TX completes an active frame if disabled; a new TXDATA write while disabled
errors instead of deadlocking. RX has one pending-byte slot; overrun retains
the old byte and sets sticky error. Bad stop bit discards the new byte and sets
FRAME_ERROR. RX disable aborts partial reception; accepted read responses still
complete. A simultaneous valid receive and old-byte consume keeps the new byte;
new error events win over same-edge W1C. Busy-TX writes eventually complete only
with a running clock; no zero-latency UART result is assumed.

Timer runs from clk_i, independently of pipeline stalls. With old enable set,
increment COUNT each edge modulo 2^32; a match is next_count==old_compare. Optional
auto-reload sets count 0 on match; otherwise wrap naturally. A COUNT write takes
priority over increment/match for that edge. New compare/control values apply
subsequently. A real match wins over same-edge status W1C. Snapshot read data is
held stable while awaiting response acceptance. No software interrupt is asserted.

T027/T028/T042 still need executable peripheral and collision tests; refinement
that changes this reviewed software-visible contract requires a new owner review.
Full pin mapping and XDC remain T025 work; only source documentation was checked
today, not physical wiring, ports or constraints in the XPR.

## 11. Verification, review and completion

docs/ARCH_REVIEW.md lists explicit decisions to approve or revise.
docs/ARCH_CONTRACT.json maps 22 requirement IDs to backlog tasks. The consistency
checker validates structure, address overlap/alignment, target agreement, port
table drift, instruction inventory and task traceability. Mutation tests challenge
that checker. These checks are documentation validation, not RTL or ISA tests.

T002 ends at awaiting_review after automated checks and daily reports. It must
not be marked completed or used to start T003 before owner approval. No RTL,
source integration, XDC, synthesis, physical programming or architecture approval
is performed by this task. No timing, coverage, formal or PPA number is invented.
