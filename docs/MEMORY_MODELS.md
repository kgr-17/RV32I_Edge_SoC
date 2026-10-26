# T009 memory protocol models

`dv/models/memory.py` provides standard-library Python behavior models, not RTL.
`MemoryImage` contains the reviewed 64 KiB ROM at 0 and 64 KiB RAM at 0x10000.
Initialization is an explicit setup action. Warm reset never reinitializes bytes.
Instruction fetches read ROM only. Data reads access ROM/RAM; only RAM writes
succeed. Unmapped addresses and injected aligned error words return zero/error.
MMIO is outside this bounded model and returns error; UART/GPIO/timer behavior
belongs to later peripheral/fabric milestones. This does not revise their map.

Create `FixedLatencyMemory(image, port='instruction'|'data', latency=N)` for
each bus; N is a positive integer. Both instances may share one MemoryImage,
but have independent outstanding slots. Their caller must apply shared reset
to both on the same simulated edge. No internal clock, scheduler or RTL adapter
is introduced here. Integration must drive/sample the real DUT at clock edges.

`Request(addr, write=False, byte_enable=15, wdata=0)` is immutable. addr is the
original unsigned 32-bit byte address. Masks 1/2/4/8/3/12/15 must match the lane
and natural access alignment. Read wdata and unused write lanes must be zero.
Malformed requests raise ProtocolError; they are producer bugs, not bus-error
responses. Instruction requests must be aligned full-word reads. Data reads
return the containing full aligned word; the LSU handles extension/selection.

Call `tick(req_valid, request, rsp_ready, allow_request=True, reset=False)` once
per edge, starting at edge 0. The immutable returned Edge reports pre-effect
ready/valid, Response(data,error), and actual request/response handshakes.
An accepted request at n first asserts response valid at n+N; ready does not
change that fixed latency. allow_request injects request-side backpressure.
Hold valid and all request fields stable while ready is false; the model checks
this obligation, including offers behind another outstanding transaction. An
exception does not advance the model's edge. Response payload stays frozen
through all stalls. Inactive response metadata is zero.

Stores change selected RAM bytes only when a successful response is accepted.
Error responses and cancelled work have no effects. A stalled read snapshot may
be captured at its first valid edge. Reset masks both handshakes, cancels pending
and offered work, and prevents ghost responses. Already committed bytes persist.
No replacement request is accepted on the previous response's consume edge.
Accepted/completed/cancelled counters are cumulative diagnostic history, not
architectural state; reset does not erase that test accounting.

`python -B scripts/verify.py test-memory` runs anchored directed tests and an
independent byte/event ledger. Seeds 1/20261025 cover I/D ports at latencies
1/3/7, 4,096 randomized edges each plus a drain, deterministic backpressure,
resets, mapped/unmapped/error reads and writes, every data lane mask, and exact
single-effect accounting. The ledger independently computes response snapshots
and byte effects from accepted-edge history; it does not call model helpers.
Four deliberately faulty variants must be rejected: early store, changing
stalled snapshot, same-edge replacement acceptance and ignored reset. Producer
payload/valid changes are also explicit negative cases. No zero-test pass.

Replay the command to reproduce the fixed seed set. A UTC-stamped compact JSON
receipt records versions, command, source hashes, coverage/counts, failure
details and source drift. Successful per-case edge traces are retained with
SHA-256 under build/T009; failed cases identify seed/port/latency in diagnostics.
`harness.py finish T009 --evidence evidence/daily/T009.md` additionally runs
unchanged real RTL synthesis lint and both Git whitespace gates. No new tool,
package, architecture, production RTL, XPR or constraints are needed. This is
model-level evidence; real CPU/fabric bus verification, formal, routed timing,
hardware and ASIC evidence remain future work.

Acceptance passed on attempt 2: all 11 Python tests, 12 seeded I/D/latency
cases, 49,276 edges, 8,654 accepted = 7,487 completed + 1,167 cancelled.
All declared per-case bins and four defective-model rejection probes passed;
no skipped tests or source drift. A testbench drain-bound error on attempt 1
was repaired using the bound for a pending transaction plus a held offer.
No model behavior, assertion, seed or coverage requirement changed. Both
attempt receipts and the exact first inputs ZIP are preserved. RTL lint passed
19 checks/11 commands; both Git whitespace gates passed after restoring LF
registry bytes. See evidence/daily/T009.md for receipts and replay details.

T010 integration follow-up changes only receipt serialization to explicit UTF-8
bytes with LF, avoiding Windows text translation. The full regression executes
the unchanged model assertions/seeds again and checks the new receipt format;
T009's original raw/normalized receipts and tested-source snapshots remain intact.
