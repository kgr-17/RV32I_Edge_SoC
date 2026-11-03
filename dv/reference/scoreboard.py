"""Streaming architectural scoreboard; independent of RTL and expected rows.

The ISS is the ISA oracle. A separate observed-effect ledger reconstructs GPR
and memory state from matched retirement events and checks terminal dumps.
"""
from collections import Counter
from dv.reference.rv32_iss import RV32ISS, Retirement, Fault


class ScoreboardMismatch(ValueError):
    pass


class ArchitecturalScoreboard:
    def __init__(self, cases):
        self.cases = list(cases)
        if not self.cases or len({case['id'] for case in self.cases}) != len(self.cases):
            raise ValueError('empty or duplicate scoreboard scenarios')
        self.position = self.events = 0
        self.phase = 'start'
        self.failure = None
        self.counts = Counter()
        self.summaries = []

    def reject(self, message):
        if self.failure is None:
            self.failure = 'event%d case%d phase=%s: %s' % (self.events, self.position, self.phase, message)
        raise ScoreboardMismatch(self.failure)

    def observe(self, event):
        if self.failure is not None:
            self.reject('scoreboard already failed')
        event = tuple(event)
        if len(event)<2:
            self.reject('malformed observed event')
        if self.phase=='start':
            if self.position>=len(self.cases):
                self.reject('extra event after final scenario')
            case = self.cases[self.position]
            self.ident = case['id']
            self.iss = RV32ISS(case['image'])
            self.registers = [0]*32
            self.memory = dict(case['image'])
            self.case_counts = Counter()
            self.phase = 'execute'
        if event[1]!=self.ident:
            self.reject('wrong scenario/order: '+repr(event))
        kind = event[0]
        if kind=='R':
            if self.phase!='execute' or len(event)!=15:
                self.reject('unexpected/malformed retirement')
            reference = self.iss.step()
            if not isinstance(reference, Retirement) or event!=('R', self.ident, *reference.fields()):
                self.reject('retirement differs from independent ISS: '+repr(event))
            _, _, _, _, _, _, write, rd, value, mem, store, addr, mask, payload, _ = event
            if write:
                if not 1<=rd<=31:
                    self.reject('invalid architectural destination')
                self.registers[rd] = value
            elif rd or value:
                self.reject('noncanonical disabled GPR metadata')
            if mem:
                self.case_counts['stores' if store else 'loads'] += 1
            if mem and store:
                base = addr//4*4
                for lane in range(4):
                    if mask & 2**lane:
                        self.memory[base+lane] = payload//2**(8*lane)%256
            if self.registers!=self.iss.regs or self.memory!=self.iss.memory:
                self.reject('observed committed effects differ from ISS state')
            self.case_counts['retirements'] += 1
        elif kind=='F':
            if self.phase!='execute' or len(event)!=6:
                self.reject('unexpected/malformed fault')
            fault = self.iss.step()
            if not isinstance(fault, Fault) or event!=('F', self.ident, fault.pc, fault.insn, fault.code, fault.tval):
                self.reject('fault differs from independent ISS: '+repr(event))
            self.case_counts['faults'] += 1
            self.phase = 'gpr'
            self.next_word = 1
        elif kind=='G':
            if self.phase!='gpr' or len(event)!=4 or event[2]!=self.next_word:
                self.reject('missing/duplicate/reordered GPR dump')
            if event[3]!=self.registers[self.next_word] or event[3]!=self.iss.regs[self.next_word]:
                self.reject('terminal GPR differs from committed effects')
            self.case_counts['gpr_words'] += 1
            self.next_word += 1
            if self.next_word==32:
                self.phase = 'ram'; self.next_word = 0
        elif kind=='M':
            if self.phase!='ram' or len(event)!=4 or event[2]!=self.next_word:
                self.reject('missing/duplicate/reordered RAM dump')
            addr = 0x10000+self.next_word*4
            word = int.from_bytes(bytes(self.memory.get(addr+n, 0) for n in range(4)), 'little')
            if event[3]!=word or event[3]!=self.iss._word(addr):
                self.reject('terminal RAM differs from committed effects')
            self.case_counts['ram_words'] += 1
            self.next_word += 1
            if self.next_word==32:
                self.summaries.append({'scenario': self.ident, **dict(self.case_counts),
                                       'operation_hits': dict(Counter(self.iss.operations))})
                self.counts.update(self.case_counts)
                self.position += 1; self.phase = 'start'
        else:
            self.reject('unknown observed event type')
        self.events += 1

    def finish(self):
        if self.failure is not None or not self.events or self.phase!='start' or self.position!=len(self.cases):
            self.reject('empty, failed or incomplete observed execution')
        return {'events': self.events, 'scenarios': self.position, **dict(self.counts), 'cases': self.summaries}


def check_trace(cases, actual):
    scoreboard = ArchitecturalScoreboard(cases)
    for event in actual:
        scoreboard.observe(event)
    return scoreboard.finish()


def inject_actual_errors(cases, actual):
    """Replay deterministic mutations of actual observed RTL events, not mocks."""
    actual = [tuple(event) for event in actual]
    records = []
    for kind, field, label in [('R', 8, 'retirement_data_bit'), ('G', 3, 'terminal_gpr_bit'), ('M', 3, 'terminal_ram_bit')]:
        index = next(n for n, event in enumerate(actual) if event[0]==kind)
        changed = list(actual); row = list(changed[index]); row[field] ^= 1; changed[index] = tuple(row)
        records.append((label, changed, {'index': index, 'before': actual[index], 'after': changed[index]}))
    records += [('empty_trace', [], {'operation': 'remove all events'}),
                ('dropped_retirement', actual[1:], {'index': 0, 'before': actual[0], 'after': None}),
                ('extra_event', actual+actual[:1], {'index': len(actual), 'before': None, 'after': actual[0]})]
    rejected = []
    for label, changed, mutation in records:
        try:
            check_trace(cases, changed)
        except ScoreboardMismatch as exc:
            rejected.append({'case': label, 'mutation': mutation, 'diagnostic': str(exc)})
        else:
            raise RuntimeError('Scoreboard accepted actual injected error: '+label)
    return rejected
