"""Independent RV32I 2.1 interpreter for the reviewed fatal-halt EEI.

No RTL, decoder metadata, operation enums, directed expectations or simulator
helpers are imported. Architectural memory effects are atomic with retirement;
the RTL fabric's earlier response effect point is checked separately by the DV.
"""
from dataclasses import dataclass

MOD = 2 ** 32


def field(word, high, low):
    return word // (2 ** low) % (2 ** (high - low + 1))


def signed(value, width=32):
    return value - 2 ** width if value >= 2 ** (width - 1) else value


@dataclass(frozen=True)
class Fault:
    pc: int
    insn: int
    code: int
    tval: int


@dataclass(frozen=True)
class Retirement:
    order: int
    pc: int
    insn: int
    next_pc: int
    rd_write: int
    rd: int
    rd_data: int
    mem_valid: int
    mem_write: int
    mem_addr: int
    mem_be: int
    mem_wdata: int
    mem_rdata: int

    def fields(self):
        return tuple(getattr(self, name) for name in self.__dataclass_fields__)


class RV32ISS:
    def __init__(self, image=None, error_words=()):
        self.memory = dict(image or {})
        if any(type(addr) is not int or not 0 <= addr < 0x20000 or
               type(value) is not int or not 0 <= value < 256 for addr, value in self.memory.items()):
            raise ValueError('image must contain ROM/RAM byte addresses and byte values')
        self.error_words = frozenset(error_words)
        if any(type(addr) is not int or not 0 <= addr < MOD or addr % 4 for addr in self.error_words):
            raise ValueError('injected error words must be aligned uint32')
        self.reset()

    def reset(self):
        self.regs = [0] * 32
        self.pc = self.order = 0
        self.fault = None
        self.operations = []
        self.memory_events = []

    def _halt(self, insn, code, tval):
        self.fault = Fault(self.pc, insn, code, tval % MOD)
        return self.fault

    def _word(self, addr):
        return int.from_bytes(bytes(self.memory.get(addr + n, 0) for n in range(4)), 'little')

    def step(self):
        if self.fault is not None:
            return self.fault
        pc = self.pc
        if pc % 4:
            return self._halt(0, 2, pc)
        if pc >= 0x10000 or pc in self.error_words:
            return self._halt(0, 3, pc)
        insn = self._word(pc)
        opcode, rd = field(insn, 6, 0), field(insn, 11, 7)
        f3, ra, rb, f7 = field(insn, 14, 12), field(insn, 19, 15), field(insn, 24, 20), field(insn, 31, 25)
        a, b = self.regs[ra], self.regs[rb]
        imm_i = signed(field(insn, 31, 20), 12)
        next_pc, value, write_rd, name = (pc + 4) % MOD, 0, False, None
        mem = (0, 0, 0, 0, 0, 0)
        store = None
        if opcode in (0x37, 0x17):
            upper = field(insn, 31, 12) * 4096
            name = 'LUI' if opcode == 0x37 else 'AUIPC'
            value, write_rd = (upper if opcode == 0x37 else pc + upper), True
        elif opcode in (0x6f, 0x67):
            if opcode == 0x67 and f3 != 0:
                return self._halt(insn, 1, insn)
            if opcode == 0x6f:
                immediate = signed(field(insn, 31, 31) * 2**20 + field(insn, 19, 12) * 4096 +
                                   field(insn, 20, 20) * 2048 + field(insn, 30, 21) * 2, 21)
                target, name = (pc + immediate) % MOD, 'JAL'
            else:
                target, name = (a + imm_i) % MOD, 'JALR'
                target -= target % 2
            self.operations.append(name)
            if target % 4:
                return self._halt(insn, 2, target)
            next_pc, value, write_rd = target, (pc + 4) % MOD, True
        elif opcode == 0x63:
            predicates = {0: ('BEQ', a == b), 1: ('BNE', a != b),
                          4: ('BLT', signed(a) < signed(b)), 5: ('BGE', signed(a) >= signed(b)),
                          6: ('BLTU', a < b), 7: ('BGEU', a >= b)}
            if f3 not in predicates:
                return self._halt(insn, 1, insn)
            name, take = predicates[f3]
            self.operations.append(name)
            if take:
                displacement = signed(field(insn, 31, 31) * 4096 + field(insn, 7, 7) * 2048 +
                                      field(insn, 30, 25) * 32 + field(insn, 11, 8) * 2, 13)
                next_pc = (pc + displacement) % MOD
                if next_pc % 4:
                    return self._halt(insn, 2, next_pc)
        elif opcode in (0x03, 0x23):
            loads = {0: ('LB', 1, True), 1: ('LH', 2, True), 2: ('LW', 4, False),
                     4: ('LBU', 1, False), 5: ('LHU', 2, False)}
            stores = {0: ('SB', 1, False), 1: ('SH', 2, False), 2: ('SW', 4, False)}
            writing = opcode == 0x23
            kinds = stores if writing else loads
            if f3 not in kinds:
                return self._halt(insn, 1, insn)
            name, size, sign_load = kinds[f3]
            self.operations.append(name)
            immediate = signed(field(insn, 31, 25) * 32 + field(insn, 11, 7), 12) if writing else imm_i
            addr = (a + immediate) % MOD
            if addr % size:
                return self._halt(insn, 6 if writing else 4, addr)
            accessible = 0x10000 <= addr < 0x20000 if writing else addr < 0x20000
            if not accessible or addr // 4 * 4 in self.error_words:
                return self._halt(insn, 7 if writing else 5, addr)
            lane = addr % 4
            be = sum(2**n for n in range(lane, lane + size))
            if writing:
                payload = b.to_bytes(4, 'little')[:size]
                word_data = int.from_bytes(bytes(lane) + payload + bytes(4 - lane - size), 'little')
                mem = (1, 1, addr, be, word_data, 0)
                store = addr, payload
            else:
                raw = self._word(addr // 4 * 4)
                payload = bytes(self.memory.get(addr + n, 0) for n in range(size))
                value, write_rd = int.from_bytes(payload, 'little', signed=sign_load), True
                mem = (1, 0, addr, be, 0, raw)
        elif opcode in (0x13, 0x33):
            immediate_form = opcode == 0x13
            operand = imm_i if immediate_form else b
            if f3 == 0:
                if immediate_form or f7 == 0:
                    name, value = ('ADDI' if immediate_form else 'ADD'), a + operand
                elif f7 == 32:
                    name, value = 'SUB', a - b
            elif f3 == 1 and f7 == 0:
                amount = rb if immediate_form else b % 32
                name, value = ('SLLI' if immediate_form else 'SLL'), a * 2**amount
            elif f3 == 2 and (immediate_form or f7 == 0):
                name, value = ('SLTI' if immediate_form else 'SLT'), int(signed(a) < (imm_i if immediate_form else signed(b)))
            elif f3 == 3 and (immediate_form or f7 == 0):
                name, value = ('SLTIU' if immediate_form else 'SLTU'), int(a < operand % MOD)
            elif f3 == 4 and (immediate_form or f7 == 0):
                name, value = ('XORI' if immediate_form else 'XOR'), a ^ operand
            elif f3 == 5 and f7 in (0, 32):
                amount = rb if immediate_form else b % 32
                arithmetic = f7 == 32
                name = ('SRAI' if immediate_form else 'SRA') if arithmetic else ('SRLI' if immediate_form else 'SRL')
                value = (signed(a) if arithmetic else a) // 2**amount
            elif f3 == 6 and (immediate_form or f7 == 0):
                name, value = ('ORI' if immediate_form else 'OR'), a | operand
            elif f3 == 7 and (immediate_form or f7 == 0):
                name, value = ('ANDI' if immediate_form else 'AND'), a & operand
            if name is None:
                return self._halt(insn, 1, insn)
            write_rd = True
        elif opcode == 0x0f and f3 == 0:
            name = 'FENCE'  # All other fields ignored by conservative drain EEI.
        elif insn in (0x00000073, 0x00100073):
            self.operations.append('ECALL' if insn == 0x73 else 'EBREAK')
            return self._halt(insn, 8 if insn == 0x73 else 9, 0)
        else:
            return self._halt(insn, 1, insn)
        if opcode not in (0x6f, 0x67, 0x63, 0x03, 0x23):
            self.operations.append(name)
        value %= MOD
        real_write = write_rd and rd != 0
        event = Retirement(self.order, pc, insn, next_pc, int(real_write), rd if real_write else 0,
                           value if real_write else 0, *mem)
        if store is not None:
            addr, payload = store
            self.memory.update({addr + n: byte for n, byte in enumerate(payload)})
        if mem[0]:
            self.memory_events.append(mem)
        if real_write:
            self.regs[rd] = value
        self.regs[0] = 0
        self.order += 1
        self.pc = next_pc
        return event

    def run(self, limit=10000):
        events = []
        for _ in range(limit):
            event = self.step()
            if isinstance(event, Fault):
                return events, event
            events.append(event)
        raise RuntimeError('ISS bounded progress limit reached')
