"""Edge-stepped ROM/RAM models for the reviewed local_mem_v1 protocol.

This is verification infrastructure, not synthesizable RTL or an MMIO model.
tick() observes signals/handshakes at one rising edge, then applies effects.
"""
from dataclasses import dataclass
from typing import Optional


class ProtocolError(ValueError):
    """The request producer violated the local bus contract."""


def _unsigned(value, bits, name):
    if type(value) is not int or not 0 <= value < 2 ** bits:
        raise ProtocolError('%s must be an unsigned %d-bit integer' % (name, bits))


@dataclass(frozen=True)
class Request:
    addr: int
    write: bool = False
    byte_enable: int = 15
    wdata: int = 0

    def __post_init__(self):
        _unsigned(self.addr, 32, 'addr')
        _unsigned(self.byte_enable, 4, 'byte_enable')
        _unsigned(self.wdata, 32, 'wdata')
        if type(self.write) is not bool:
            raise ProtocolError('write must be bool')
        # Lane masks encode naturally aligned byte, halfword or word accesses.
        legal = {0: (1, 3, 15), 1: (2,), 2: (4, 12), 3: (8,)}
        if self.byte_enable not in legal[self.addr % 4]:
            raise ProtocolError('byte enables do not match original byte address')
        selected_bits = sum(255 << (lane * 8) for lane in range(4)
                            if self.byte_enable & (1 << lane))
        if (not self.write and self.wdata != 0) or self.wdata & ~selected_bits:
            raise ProtocolError('read/unused write lanes must contain zero')


@dataclass(frozen=True)
class Response:
    data: int = 0
    error: bool = False


@dataclass(frozen=True)
class Edge:
    cycle: int
    req_ready: bool
    rsp_valid: bool
    response: Response
    request_accepted: bool
    response_accepted: bool


class MemoryImage:
    """64 KiB ROM plus 64 KiB RAM; explicit setup is separate from warm reset."""
    ROM_BASE = 0
    RAM_BASE = 0x10000
    SIZE = 0x10000

    def __init__(self):
        self.rom = bytearray(self.SIZE)
        self.ram = bytearray(self.SIZE)

    def _region(self, addr):
        if 0 <= addr < self.SIZE:
            return self.rom, addr
        if self.RAM_BASE <= addr < self.RAM_BASE + self.SIZE:
            return self.ram, addr - self.RAM_BASE
        raise KeyError('not modeled ROM/RAM: 0x%08x' % addr)

    def initialize(self, addr, payload):
        """Explicit test/firmware setup, never a modeled bus side effect."""
        _unsigned(addr, 32, 'initialization address')
        if not isinstance(payload, (bytes, bytearray)) or not payload:
            raise ValueError('initialization requires nonempty bytes')
        region, offset = self._region(addr)
        if offset + len(payload) > self.SIZE:
            raise ValueError('initialization crosses a region boundary')
        region[offset:offset + len(payload)] = payload

    def read_word(self, addr):
        """Read the containing full aligned word, including for byte requests."""
        region, offset = self._region(addr & ~3)
        return int.from_bytes(region[offset:offset + 4], 'little')

    def _commit_store(self, request):
        # Permissions are checked before constructing a successful response.
        offset = (request.addr & ~3) - self.RAM_BASE
        if not 0 <= offset <= self.SIZE - 4:
            raise AssertionError('attempt to commit a non-RAM store')
        for lane, value in enumerate(request.wdata.to_bytes(4, 'little')):
            if request.byte_enable & (1 << lane):
                self.ram[offset + lane] = value


class FixedLatencyMemory:
    """One outstanding transaction per instance; I and D may share an image.

    allow_request controls request backpressure. latency >= 1 counts complete
    edge intervals from acceptance to the first response-valid edge, regardless
    of rsp_ready. Counters are cumulative diagnostics and survive reset.
    """
    def __init__(self, image, port='data', latency=1, error_words=()):
        if not isinstance(image, MemoryImage):
            raise TypeError('image must be MemoryImage')
        if port not in ('instruction', 'data'):
            raise ValueError('unknown port')
        if type(latency) is not int or latency < 1:
            raise ValueError('latency must be a positive integer')
        self.image, self.port, self.latency = image, port, latency
        self.error_words = frozenset(error_words)
        for addr in self.error_words:
            _unsigned(addr, 32, 'error word')
            if addr % 4:
                raise ValueError('error injection addresses must be aligned')
        self.cycle = self.accepted = self.completed = self.cancelled = 0
        self._pending: Optional[Request] = None
        self._held_offer: Optional[Request] = None
        self._response: Optional[Response] = None
        self._due = 0

    def _make_response(self, req):
        rom = 0 <= req.addr < 0x10000
        ram = 0x10000 <= req.addr < 0x20000
        permitted = rom if self.port == 'instruction' else (ram or (rom and not req.write))
        if not permitted or (req.addr & ~3) in self.error_words:
            return Response(error=True)
        return Response(0 if req.write else self.image.read_word(req.addr))

    def tick(self, req_valid=False, request=None, rsp_ready=False,
             allow_request=True, reset=False):
        """Return pre-effect edge signals, then apply that edge's handshakes.

        reset masks both channels immediately for this sampled edge, cancels
        accepted and offered work, and retains ROM/RAM. Protocol exceptions do
        not advance time. No replacement is accepted on a response-consume edge.
        """
        for name, value in (('req_valid', req_valid), ('rsp_ready', rsp_ready),
                            ('allow_request', allow_request), ('reset', reset)):
            if type(value) is not bool:
                raise ProtocolError(name + ' must be bool')
        if reset:
            self.cancelled += int(self._pending is not None)
            self._pending = self._held_offer = self._response = None
            edge = Edge(self.cycle, False, False, Response(), False, False)
            self.cycle += 1
            return edge
        if req_valid:
            if not isinstance(request, Request):
                raise ProtocolError('valid request requires immutable Request')
            if self.port == 'instruction' and (request.addr % 4 or request.write or
                                               request.byte_enable != 15):
                raise ProtocolError('instruction requests must be aligned full-word reads')
        if self._held_offer is not None and (not req_valid or request != self._held_offer):
            raise ProtocolError('stalled request valid/payload changed before acceptance')

        ready = self._pending is None and allow_request
        if self._pending is not None and self._response is None and self.cycle >= self._due:
            self._response = self._make_response(self._pending)
        valid = self._response is not None
        take_req, take_rsp = req_valid and ready, valid and rsp_ready
        edge = Edge(self.cycle, ready, valid, self._response or Response(), take_req, take_rsp)
        self._held_offer = request if req_valid and not ready else None
        if take_rsp:
            if self._pending.write and not self._response.error:
                self.image._commit_store(self._pending)
            self.completed += 1
            self._pending = self._response = None
        if take_req:
            assert not take_rsp
            self.accepted += 1
            self._pending = request
            self._due = self.cycle + self.latency
        self.cycle += 1
        return edge
