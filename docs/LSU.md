# T008 load/store formatting unit

`lsu` is a stateless little-endian formatter, not a memory bus controller.
Inputs: op_t, byte_offset_i[1:0], store_data_i[31:0], aligned read_word_i[31:0].
Outputs: load_data_o/store_word_o[31:0], byte_enable_o[3:0], write_o,
misaligned_o and supported_o. The caller computes and retains the ORIGINAL
32-bit byte address; only its low two bits enter this unit. Do not replace the
bus address/fault tval with a word-aligned address. There is no address-map check.

LB/LBU/LH/LHU/LW select bytes and sign/zero extend; SB/SH/SW use only the low
source bytes, shifted to the chosen bus lanes. Unselected store lanes are zero.
Byte enables describe reads as well as writes. Halfwords require offset 0/2;
words require offset 0; bytes use every lane. A supported misaligned operation
sets misaligned=1 but zeros byte enables, write flag and both data outputs.
Unsupported selectors output all-zero metadata. supported=1 is not request-valid:
the caller must reject misalignment and form the appropriate precise load/store
fault before offering any bus request. No split access or memory effect occurs
here; store effects still belong to successful response acceptance in the fabric.
Load-to-x0 memory actions must not be gated by a register write flag.

The independent Python oracle works on byte arrays and signed byte conversion,
not RTL shifts/concatenations. It also constructs the expected memory word after
a masked store. The SV bench applies DUT strobes/data to the original memory
word and compares the merged result, proving scoped neighbor-byte preservation
in addition to exact outputs. This is a consumer model, not a real bus handshake.

Seeds 1/20261025 cover every width/lane including all misaligned cases, all byte
values, halfword sign/walking patterns, word walking/complement patterns,
full-width edge crosses, 4,096 random inputs per supported op and unsupported
selectors. Six anchored Python tests and actual corrupt/empty negative runs are
required. A capture/multiplex synthesis probe keeps all meaningful formatter
inputs independently observable; direct DV instantiates the full formatter.

Acceptance commands: verify.py lint and verify.py test-lsu through harness finish.
The registry also extends regress. Source/vector/WDB/Tcl/argv hashes and exact
versions/counts/outputs are retained. No architecture, external core bus, clock,
reset or existing RTL changes. Formal, bus sequencing, CPU, timing and hardware
evidence remain later milestones.

Acceptance passed on attempt 2: 44,872 vectors per seed, 89,744 total;
six Python oracle tests and both actual negative simulations passed. Probe
synthesis took 25.313 s with zero warnings/errors and all structural checks.
Attempt 1's Synth 8-3936 width warning was repaired by making the selected slice
explicitly 16 bits; exact failed source/logs are retained, with no checker or
test changes. See evidence/daily/T008.md and its two attempt receipts.
