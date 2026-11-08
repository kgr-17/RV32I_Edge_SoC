"""Independent CSR/ISA/peripheral checking for enabled SoC traces."""
from collections import Counter
from soc_model import BusModel,SocISS,decode_uart,Retirement,Fault
from test_mmio import Model as PeripheralModel
from test_csr import Model as CsrModel


class IrqPeripheral(PeripheralModel):
    def __init__(self):super().__init__();self.irq_enable=False
    def decode(self,ch,packet):
        result=super().decode(ch,packet)
        if ch==1 and packet[1]&~3==0x10000108 and not packet[2] and not result['error']:
            result['read']|=int(self.irq_enable)*4
        return result
    def edge(self,reset,raw,g,t):
        pending=self.pending[1]
        update=pending is not None and t[5] and not pending['error'] and pending['op'] is not None and pending['op'][0]==2 and pending['op'][2]&1
        value=bool(pending['op'][1]&4) if update else self.irq_enable
        result=super().edge(reset,raw,g,t);self.irq_enable=False if reset else value
        return result


class IrqBus(BusModel):
    def __init__(self,rom,divider):super().__init__(rom,divider);self.io=IrqPeripheral()
    def irq(self,reset=0):return int(not reset and self.io.flag and self.io.irq_enable)


class InterruptISS(SocISS):
    def reset(self):super().reset();self.csr=CsrModel();self.csr_trace=(0,0,0,0,0,0)
    def csr_inputs(self,irq=0,addr=0,op=0,data=0,sz=1,rz=1,commit=0,trap=0,mret=0,pc=0,cause=0,tval=0):
        return (0,irq,addr,op,data,sz,rz,commit,trap,mret,pc,cause,tval,0,0,0,0,0,0)
    def step_extended(self,completed,irq):
        if self.pc%4 or self.pc>=0x10000 or self.pc in self.error_words:return super().step()
        self.csr_trace=(0,0,0,0,0,0);insn=self._word(self.pc);f3=(insn>>12)&7;rs1=(insn>>15)&31;rd=(insn>>7)&31
        if insn==0x30200073:
            target=self.csr.state[0x341];self.csr.edge(self.csr_inputs(irq,mret=1))
            event=Retirement(self.order,self.pc,insn,target,0,0,0,0,0,0,0,0,0)
            self.pc=target;self.order+=1;return event
        if insn&127==0x73 and f3 in (1,2,3,5,6,7):
            addr=insn>>20;operand=rs1 if f3>=5 else self.regs[rs1]
            x=self.csr_inputs(irq,addr,f3,operand,int(rs1==0),int(rd==0),1);view=self.csr.view(x)
            if view[2]:return self._halt(insn,1,insn)
            self.csr_trace=(1,addr,view[0],view[1],view[3],view[4]);self.csr.edge(x)
            event=Retirement(self.order,self.pc,insn,(self.pc+4)%2**32,int(rd!=0),rd,view[3] if rd else 0,0,0,0,0,0,0)
            if rd:self.regs[rd]=view[3]
            self.pc=event.next_pc;self.order+=1;return event
        if insn&127 in (3,35) and completed and completed[0]['error']:
            return self._halt(insn,7 if insn&127==35 else 5,completed[0]['addr'])
        return super().step_for_bus(completed)
    def trap(self,asynchronous,completed,irq):
        vector=self.csr.state[0x305];pc=self.pc;insn=0;tval=0
        if asynchronous:
            if not(irq and self.csr.state[0x304]&0x800 and self.csr.state[0x300]&8):raise ValueError('IRQ_MASK_OR_LEVEL')
            cause=0x8000000b
        else:
            event=self.step_extended(completed,irq)
            if not isinstance(event,Fault):raise ValueError('IRQ_EXPECTED_SYNCHRONOUS_FAULT')
            cause={1:2,2:0,3:1,4:4,5:5,6:6,7:7,8:11,9:3}[event.code];insn=event.insn;tval=event.tval
            if event.code in (5,7):
                if not completed or not completed[0]['error']:raise ValueError('IRQ_MISSING_ERROR_RESPONSE')
                completed.pop(0)
        self.csr.edge(self.csr_inputs(irq,trap=1,pc=pc,cause=cause,tval=tval));self.pc=vector;self.fault=None
        return (self.order,pc,insn,cause,tval,vector)


def check_trace(text,rom,symbols,divider,aborted_epochs=0):
    rows=[[int(w,16) for w in line.split()] for line in text.splitlines()]
    if not rows or any(len(r) not in (60,61,62) for r in rows):raise ValueError('IRQ_TRACE_SHAPE')
    env=IrqBus(rom,divider);iss=InterruptISS(dict(enumerate(rom))|{a:0 for a in range(65536,131072)})
    prior=None;phase=-1;serial=[];retired=0;causes=Counter();epochs=[];csr_ops=Counter();start_counter=0
    def finish():
        decoded=decode_uart(serial,divider)
        if decoded!=b'IRQ PASS\r\n':raise ValueError('IRQ_UART_PAYLOAD')
        if env.word(symbols['signature'])!=0x600d600d or env.word(symbols['irq_count'])!=1 or env.word(0x1e000)!=start_counter+1:raise ValueError('IRQ_SIGNATURE')
        if bytes(iss.memory.get(65536+b,0) for b in range(65536))!=bytes(env.ram):raise ValueError('IRQ_ARCH_PHYSICAL_RAM')
        if env.completed or env.dp is not None:raise ValueError('IRQ_UNRETIRED_EFFECT')
        if not {0,1,2,3,4,5,6,7,11,0x8000000b}<=set(causes):raise ValueError('IRQ_MISSING_CAUSE')
        if not set((1,2,3,5,6,7))<=set(csr_ops):raise ValueError('IRQ_MISSING_CSR_OPCODE')
        epochs.append({'epoch':phase,'retirements':retired,'causes':dict(causes),'csr_ops':dict(csr_ops),'uart':decoded.decode(),'persistent_counter':env.word(0x1e000)})
    for index,row in enumerate(rows):
        epoch,cycle,reset,rx,sw=row[:5]
        if cycle!=index or epoch not in range(aborted_epochs+2):raise ValueError('IRQ_TRACE_ORDER')
        if epoch!=phase:
            if epoch!=phase+1 or not reset:raise ValueError('IRQ_EPOCH_RESET')
            if phase>=aborted_epochs:finish()
            elif phase>=0:epochs.append({'epoch':phase,'reset_aborted':True,'retirements':retired,'causes':dict(causes)})
            phase=epoch;serial=[];retired=0;causes=Counter();csr_ops=Counter()
            start_counter=env.word(0x1e000)
        iv,ir,ia,ivs,irdy,idata,ie=row[5:12];dv,dr,da,dw,dd,db,ds,dsr,ddata,de=row[12:22]
        gates=row[60] if len(row)>=61 else 15
        drop=row[61] if len(row)==62 else 0
        g=[(gates>>b)&1 for b in range(4)]
        inputs=(reset,rx,sw,iv*g[0],ia,irdy*g[1],dv*g[2],da,dw,dd,db,dsr*g[3]);raw_expected=env.view(inputs)
        expected=(raw_expected[0]*g[0],raw_expected[1]*g[1],raw_expected[2],raw_expected[3],raw_expected[4]*g[2],raw_expected[5]*g[3],*raw_expected[6:])
        if (ir,ivs,idata,ie,dr,ds,ddata,de,row[22],row[23])!=expected:raise ValueError('IRQ_BUS_PRE cycle=%d'%cycle)
        irq=env.irq(reset)*(1-drop)
        if row[45]!=irq:raise ValueError('IRQ_SOURCE_PRE')
        if prior is not None and not reset and not prior[2]:
            if prior[5] and not prior[6] and (not iv or ia!=prior[7]):raise ValueError('IRQ_I_HOLD')
            if prior[12] and not prior[13] and (not dv or row[14:18]!=prior[14:18]):raise ValueError('IRQ_D_HOLD')
        _,post,_=env.edge(inputs)
        if tuple(row[24:26])!=post[8:10] or row[46]!=env.irq(reset)*(1-drop):raise ValueError('IRQ_SOURCE_IO_POST')
        serial.append(row[24]);csr_expected=(0,0,0,0,0,0)
        if row[40] or row[26] and row[47]:raise ValueError('IRQ_OBSERVATION_COLLISION')
        if not row[26] and any(row[27:40]):raise ValueError('IRQ_INVALID_RETIRE_METADATA')
        if not row[47] and any(row[48:54]):raise ValueError('IRQ_INVALID_TRAP_METADATA')
        if any(row[41:45]):raise ValueError('IRQ_INVALID_LEGACY_FAULT_METADATA')
        if reset:
            # Committed physical effects survive reset, including pre-WB stores.
            # Restore from the independent bus oracle, never from DUT storage.
            iss.memory.update({65536+b:value for b,value in enumerate(env.ram)})
            iss.reset()
            if row[26] or row[47]:raise ValueError('IRQ_RESET_EFFECT')
        elif row[47]:
            asynchronous=bool(row[51]&0x80000000)
            if asynchronous and (env.completed or env.ip is not None or env.dp is not None or iv or dv):raise ValueError('IRQ_NONEMPTY_ENTRY')
            event=iss.trap(asynchronous,env.completed,irq)
            if tuple(row[48:54])!=event:raise ValueError('IRQ_TRAP_MISMATCH cycle=%d actual=%r expected=%r'%(cycle,row[48:54],event))
            causes[event[3]]+=1
        elif row[26]:
            event=iss.step_extended(env.completed,irq)
            if not isinstance(event,Retirement) or tuple(row[27:40])!=event.fields():raise ValueError('IRQ_RETIRE_MISMATCH cycle=%d actual=%r expected=%r'%(cycle,row[27:40],event))
            retired+=1;csr_expected=iss.csr_trace
            if csr_expected[0]:csr_ops[(event.insn>>12)&7]+=1
            if event.mem_valid:
                if not env.completed:raise ValueError('IRQ_MEMORY_WITHOUT_RESPONSE')
                packet=env.completed.pop(0)
                if packet['error'] or (event.mem_addr,event.mem_write,event.mem_be,event.mem_wdata,event.mem_rdata)!=(packet['addr'],packet['write'],packet['be'],packet['data'] if packet['write'] else 0,packet['read'] if not packet['write'] else 0):raise ValueError('IRQ_MEMORY_RETIRE_ORDER')
        if tuple(row[54:60])!=csr_expected:raise ValueError('IRQ_CSR_TRACE cycle=%d actual=%r expected=%r'%(cycle,row[54:60],csr_expected))
        prior=row
    if phase!=aborted_epochs+1:raise ValueError('IRQ_MISSING_PHASE')
    finish()
    return {'cycles':len(rows),'epochs':epochs,'uart_bytes':20,'ram_effects':len(env.effects),'requests':env.requests,'replies':env.replies}
