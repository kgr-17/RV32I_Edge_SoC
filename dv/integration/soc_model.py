"""Independent cycle bus environment plus ISA/serial checks for the real SoC.

Reuses previously independent peripheral oracles, not RTL tables or enums.
Physical bus effects and architectural retirement are checked separately.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dv/unit'));sys.path.insert(0,str(ROOT/'dv/reference'))
from test_uart_rx import Model as UartModel
from test_mmio import Model as PeripheralModel
from rv32_iss import RV32ISS,Retirement,Fault,signed

LANES={(0,1),(0,3),(0,15),(1,2),(2,4),(2,12),(3,8)}


class BusModel:
    def __init__(self,rom,divider):
        if len(rom)!=65536:raise ValueError('SOC_ROM_SIZE')
        self.rom=rom;self.ram=bytearray(65536);self.uart=UartModel(divider);self.io=PeripheralModel();self.n=0
        self.ip=None;self.dp=None;self.completed=[];self.requests=[0,0];self.replies=[0,0];self.canceled=[0,0];self.effects=[]
    def word(self,addr):
        region=self.rom if addr<65536 else self.ram;index=(addr&65535)&~3
        return int.from_bytes(region[index:index+4],'little')
    @staticmethod
    def target(addr,write,mask):
        if (addr%4,mask) not in LANES:return 'bad'
        if addr<0x10000:return 'bad' if write else 'rom'
        if addr<0x20000:return 'ram'
        if 0x10000000<=addr<0x10000020:return 'uart'
        if 0x10000020<=addr<0x10000040:return 'gpio'
        if 0x10000100<=addr<0x10000110:return 'timer'
        return 'bad'
    def device_inputs(self,x):
        reset,rx,sw,iv,ia,iready,dv,da,dw,dd,db,dready=x
        target=self.target(da,dw,db);idle=self.dp is None
        uart=(reset,rx,0,int(idle and dv and target=='uart'),da,dw,dd,db,int(self.dp is not None and self.dp['target']=='uart' and dready),1)
        g=(int(idle and dv and target=='gpio'),da,dw,dd,db,int(self.dp is not None and self.dp['target']=='gpio' and dready))
        t=(int(idle and dv and target=='timer'),da,dw,dd,db,int(self.dp is not None and self.dp['target']=='timer' and dready))
        return target,uart,g,t
    def view(self,x):
        reset,rx,sw,iv,ia,iready,dv,da,dw,dd,db,dready=x
        target,ui,g,t=self.device_inputs(x);uv=self.uart.view(ui);mv=self.io.view(reset)
        if reset:return (0,0,0,0,0,0,0,0,uv[4],self.io.led())
        i=(int(self.ip is None),int(self.ip is not None),self.ip['read'] if self.ip else 0,self.ip['error'] if self.ip else 0)
        ready=int(self.dp is None and (uv[0] if target=='uart' else mv[0] if target=='gpio' else mv[5] if target=='timer' else 1))
        if self.dp is None:d=(ready,0,0,0)
        elif self.dp['target']=='uart':d=(0,*uv[1:4])
        elif self.dp['target']=='gpio':d=(0,*mv[1:4])
        elif self.dp['target']=='timer':d=(0,*mv[6:9])
        else:d=(0,1,self.dp['read'],self.dp['error'])
        return (*i,*d,uv[4],self.io.led())
    def edge(self,x):
        pre=self.view(x);reset,rx,sw,iv,ia,iready,dv,da,dw,dd,db,dready=x
        target,ui,g,t=self.device_inputs(x);accepted=[bool(iv and pre[0]),bool(dv and pre[4])]
        if reset:
            self.canceled[0]+=int(self.ip is not None);self.canceled[1]+=int(self.dp is not None)
            self.ip=None;self.dp=None;self.completed=[]
        else:
            if self.ip is not None:
                if iready:self.ip=None;self.replies[0]+=1
            elif accepted[0]:
                error=ia%4!=0 or ia>=65536
                self.ip={'read':0 if error else self.word(ia),'error':int(error)};self.requests[0]+=1
            if self.dp is not None:
                if pre[5] and dready:
                    record=dict(self.dp,read=pre[6],error=pre[7],response_cycle=self.n)
                    self.completed.append(record);self.replies[1]+=1
                    if not pre[7] and record['target']=='ram' and record['write']:
                        address=(record['addr']&65535)&~3
                        for lane in range(4):
                            if record['be']&(1<<lane):self.ram[address+lane]=(record['data']>>(8*lane))&255
                        self.effects.append({'cycle':self.n,'addr':record['addr'],'be':record['be'],'data':record['data']})
                    self.dp=None
            elif accepted[1]:
                read=self.word(da) if target in ('rom','ram') and not dw else 0
                self.dp={'target':target,'addr':da,'write':dw,'data':dd,'be':db,'read':read,'error':int(target=='bad'),'request_cycle':self.n}
                self.requests[1]+=1
        self.uart.step(ui);self.io.edge(reset,sw,g,t);self.n+=1
        return pre,self.view(x),accepted


class SocISS(RV32ISS):
    def step_for_bus(self,completed):
        insn=self._word(self.pc);opcode=insn&127;rs1=(insn>>15)&31;rs2=(insn>>20)&31;rd=(insn>>7)&31;f3=(insn>>12)&7
        if opcode not in (3,35):return super().step()
        writing=opcode==35;immediate=signed(((insn>>25)<<5)|((insn>>7)&31),12) if writing else signed(insn>>20,12)
        addr=(self.regs[rs1]+immediate)%2**32
        if addr<0x10000000:return super().step()
        kinds={0:(1,True),1:(2,True),2:(4,False),4:(1,False),5:(2,False)} if not writing else {0:(1,False),1:(2,False),2:(4,False)}
        if f3 not in kinds or not completed:raise ValueError('SOC_MMIO_RETIRE_WITHOUT_RESPONSE')
        size,sign=kinds[f3];packet=completed[0];lane=addr%4
        if addr%size or packet['error']:raise ValueError('SOC_UNEXPECTED_MMIO_FAULT')
        mask=((1<<size)-1)<<lane;payload=((self.regs[rs2]%(1<<(8*size)))<<(8*lane)) if writing else 0
        if (addr,int(writing),mask,payload)!=(packet['addr'],packet['write'],packet['be'],packet['data'] if writing else 0):raise ValueError('SOC_MMIO_REQUEST_ORDER')
        value=0
        if not writing:
            value=(packet['read']>>(8*lane))%2**(8*size)
            if sign:value=signed(value,8*size)
        value%=2**32;real_write=not writing and rd!=0
        event=Retirement(self.order,self.pc,insn,(self.pc+4)%2**32,int(real_write),rd if real_write else 0,value if real_write else 0,
            1,int(writing),addr,mask,payload,0 if writing else packet['read'])
        if real_write:self.regs[rd]=value
        self.regs[0]=0;self.memory_events.append((1,int(writing),addr,mask,payload,0 if writing else packet['read']))
        self.order+=1;self.pc=event.next_pc
        return event


def decode_uart(lines,divider):
    data=[];n=1
    while n<len(lines):
        if lines[n-1]==1 and lines[n]==0:
            if n+10*divider>len(lines):raise ValueError('SOC_UART_TRUNCATED')
            samples=[lines[n+divider//2+k*divider] for k in range(10)]
            if samples[0]!=0 or samples[9]!=1:raise ValueError('SOC_UART_FRAMING')
            # Every interval in this ideal digital serializer must be constant.
            for k in range(10):
                if any(v!=samples[k] for v in lines[n+k*divider:n+(k+1)*divider]):raise ValueError('SOC_UART_BIT_WIDTH')
            data.append(sum(samples[k+1]<<k for k in range(8)));n+=10*divider
        else:n+=1
    return bytes(data)


def check_trace(text,rom,symbols,divider):
    rows=[[int(word,16) for word in line.split()] for line in text.splitlines()]
    if not rows or any(len(row)!=45 for row in rows):raise ValueError('SOC_TRACE_SHAPE')
    env=BusModel(rom,divider);iss=SocISS(dict(enumerate(rom))|{addr:0 for addr in range(65536,131072)})
    # Python3.9 dict union above is intentional and does not alter original ISS.
    prior=None;phase=-1;fault_seen=False;retired=0;epochs=[];serial=[];waits=[0,0]
    for index,row in enumerate(rows):
        epoch,cycle,reset,rx,sw=row[:5]
        if cycle!=index or epoch not in (0,1):raise ValueError('SOC_TRACE_ORDER')
        if epoch!=phase:
            if epoch!=phase+1 or not reset:raise ValueError('SOC_EPOCH_RESET')
            if phase>=0:
                if not fault_seen:raise ValueError('SOC_MISSING_FAULT')
                decoded=decode_uart(serial,divider)
                if decoded!=b'PASS\r\n':raise ValueError('SOC_UART_PAYLOAD')
                epochs.append({'epoch':phase,'retirements':retired,'uart':decoded.decode('ascii'),'persistent_counter':env.word(0x1e000)})
            phase=epoch;fault_seen=False;retired=0;serial=[]
        iv,ir,ia,iv_rsp,iready,idata,ierror=row[5:12]
        dv,dr,da,dw,dd,db,dv_rsp,dready,ddata,derror=row[12:22]
        inputs=(reset,rx,sw,iv,ia,iready,dv,da,dw,dd,db,dready);expected=env.view(inputs)
        observed=(ir,iv_rsp,idata,ierror,dr,dv_rsp,ddata,derror,row[22],row[23])
        if observed!=expected:
            name='SOC_DMEM_RESPONSE' if observed[5:8]!=expected[5:8] else 'SOC_FABRIC_PRE'
            raise ValueError('%s cycle=%d actual=%r expected=%r'%(name,cycle,observed,expected))
        if prior is not None and not reset and not prior[2]:
            if prior[5] and not prior[6] and (not iv or ia!=prior[7]):raise ValueError('SOC_I_PRODUCER_HOLD')
            if prior[12] and not prior[13] and (not dv or row[14:18]!=prior[14:18]):raise ValueError('SOC_D_PRODUCER_HOLD')
        waits[0]+=int(iv and not ir);waits[1]+=int(dv and not dr)
        _,post,_=env.edge(inputs)
        if row[24:26]!=list(post[8:10]):raise ValueError('SOC_IO_POST')
        serial.append(row[24])
        if reset:
            iss.reset();fault_seen=False
            if row[26] or row[40]:raise ValueError('SOC_RESET_VISIBLE_EFFECT')
        elif row[26]:
            event=iss.step_for_bus(env.completed)
            if not isinstance(event,Retirement) or tuple(row[27:40])!=event.fields():raise ValueError('SOC_RETIRE_MISMATCH cycle=%d'%cycle)
            retired+=1
            if event.mem_valid:
                if not env.completed:raise ValueError('SOC_MEMORY_WITHOUT_RESPONSE')
                packet=env.completed.pop(0)
                if packet['error'] or (event.mem_addr,event.mem_write,event.mem_be,event.mem_wdata,event.mem_rdata)!=(packet['addr'],packet['write'],packet['be'],packet['data'] if packet['write'] else 0,packet['read'] if not packet['write'] else 0):raise ValueError('SOC_MEMORY_RETIRE_ORDER')
        if not reset and row[40]:
            if not fault_seen:
                fault=iss.step()
                if not isinstance(fault,Fault) or (fault.pc,fault.insn,fault.code,fault.tval)!=tuple(row[41:45]):raise ValueError('SOC_FAULT_MISMATCH')
                if fault.code!=8 or fault.pc!=symbols['halt_ecall'] or iss.regs[10]!=0 or env.word(symbols['signature'])!=0x600d600d:raise ValueError('SOC_BOOT_SIGNATURE')
                if env.completed or env.dp is not None or env.word(0x1e000)!=epoch+1:raise ValueError('SOC_PENDING_OR_WARM_MEMORY')
                if bytes(iss.memory.get(65536+b,0) for b in range(65536))!=bytes(env.ram):raise ValueError('SOC_ARCH_PHYSICAL_RAM')
                if env.io.led()!=((sw|0xf0)&0xfff0):raise ValueError('SOC_GPIO_RESULT')
                fault_seen=True
            elif tuple(row[41:45])!=(iss.fault.pc,iss.fault.insn,iss.fault.code,iss.fault.tval):raise ValueError('SOC_STICKY_FAULT')
        prior=row
    if phase!=1 or not fault_seen:raise ValueError('SOC_MISSING_PHASE')
    decoded=decode_uart(serial,divider)
    if decoded!=b'PASS\r\n':raise ValueError('SOC_UART_PAYLOAD')
    epochs.append({'epoch':phase,'retirements':retired,'uart':decoded.decode('ascii'),'persistent_counter':env.word(0x1e000)})
    if not all(env.requests[ch]==env.replies[ch]+env.canceled[ch] for ch in range(2)):raise ValueError('SOC_BUS_ACCOUNTING')
    if not waits[1]:raise ValueError('SOC_NO_BUSY_BACKPRESSURE')
    return {'cycles':len(rows),'epochs':epochs,'requests':env.requests,'replies':env.replies,'canceled':env.canceled,'request_wait_cycles':waits,'ram_write_effects':len(env.effects),'uart_bytes':12}
