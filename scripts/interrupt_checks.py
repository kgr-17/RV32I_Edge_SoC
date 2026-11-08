"""Real enabled-mode unit/SoC/board-top DV, exact defects and trace evidence."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
import harness,rtl_checks,interrupt_firmware,soc_checks
from firmware_image import words
sys.path.insert(0,str(harness.inside('dv/unit')));sys.path.insert(0,str(harness.inside('dv/integration')))
import test_csr,test_interrupts,interrupt_model


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected(c,record,diagnostic,marker,label):
    output=record['stdout']+record['stderr']
    c.require(record['status'] in ('PASS','FAIL') and diagnostic in output and marker not in output,'Actual defect rejected '+label,record)


def vector_run(c,work,snapshot,top,label,text,seed,marker,negative=None):
    vector=work/(label+'.txt');harness.atomic_text(vector,text)
    r=soc_checks.simulate(c,work,snapshot,label,['SEED='+str(seed),'VECTORS='+str(vector)],'/'+top+'/clk /'+top+'/rst',30)
    if negative:rejected(c,r,negative,marker,label)
    else:c.require(rtl_checks.successful(r,'%s seed=%d checked=%d'%(marker,seed,len(text.splitlines()))),'Independent vector run '+label,r)
    return r


def boot(c,work,snapshot,top,label,seed,divider,raw,symbols,aborts=0,corrupt=False):
    trace=work/(label+'.trace')
    r=soc_checks.simulate(c,work,snapshot,label,['SEED='+str(seed),'TRACE='+str(trace),'SIG=%x'%symbols['signature']],
        ' '.join('/'+top+'/'+n for n in ('clk','rst','pc','tv','tc','tx')),60)
    marker='IRQ_RUN_COMPLETE seed=%d divisor=%d'%(seed,divider)
    c.require(rtl_checks.successful(r) and sum(line.startswith(marker+' ') for line in r['stdout'].splitlines())==1,'Native enabled boot completed '+label,r)
    if aborts:c.require(all(r['stdout'].splitlines().count('IRQ_ABORT_PHASE phase=%d'%n)==1 for n in range(aborts)),'Every requested reset-abort point reached '+label)
    if top in ('tb_interrupt_waits','tb_interrupt_aborts'):
        c.require(any(line.startswith('IRQ_CANCELED_DRAINS count=') and int(line.split('=')[1])>=2 for line in r['stdout'].splitlines()),'Actual source cancellation during drain '+label)
    if top=='tb_interrupt_priority':
        c.require(any(line.startswith('IRQ_FAULT_WON count=') and int(line.split('=')[1])>=2 for line in r['stdout'].splitlines()),'Actual older synchronous fault wins IRQ drain '+label)
    text=trace.read_text(encoding='ascii')
    if corrupt:
        try:interrupt_model.check_trace(text,raw,symbols,divider)
        except ValueError as exc:c.require(str(exc).startswith('IRQ_BUS_PRE'),'Actual corrupt image rejected by independent bus oracle')
        else:raise RuntimeError('IRQ_CORRUPT_IMAGE_ACCEPTED')
        return
    summary=interrupt_model.check_trace(text,raw,symbols,divider,aborted_epochs=aborts)
    harness.atomic(work/(label+'.summary.json'),summary)
    c.require(summary['uart_bytes']==20,'Independent ISA/CSR/trap/bus/wholeRAM/UART check '+label)
    c.result.setdefault('boots',[]).append(dict(label=label,seed=seed,divider=divider,aborted_epochs=aborts,trace=trace.relative_to(harness.ROOT).as_posix(),summary=summary))
    if label=='fast-1':
        rows=text.splitlines()
        controls=[('retirement',26,29,'IRQ_RETIRE_MISMATCH'),('trap',47,49,'IRQ_TRAP_MISMATCH'),('csr',54,59,'IRQ_CSR_TRACE')]
        for mode,valid,column,diagnostic in controls:
            index=next(i for i,line in enumerate(rows) if int(line.split()[valid],16))
            changed=list(rows);row=changed[index].split();row[column]='%x'%(int(row[column],16)^4);changed[index]=' '.join(row)
            path=work/('negative-'+mode+'.trace');bad='\n'.join(changed)+'\n';harness.atomic_text(path,bad)
            try:interrupt_model.check_trace(bad,raw,symbols,divider)
            except ValueError as exc:c.require(str(exc).startswith(diagnostic),'Observed trace defect rejected '+mode)
            else:raise RuntimeError('IRQ_BAD_TRACE_ACCEPTED '+mode)
        for mode,bad,diagnostic in [('empty','','IRQ_TRACE_SHAPE'),('truncated','\n'.join(rows[:100])+'\n','IRQ_MISSING_PHASE')]:
            harness.atomic_text(work/('negative-'+mode+'.trace'),bad)
            try:interrupt_model.check_trace(bad,raw,symbols,divider)
            except ValueError as exc:c.require(str(exc).startswith(diagnostic),'Incomplete trace rejected '+mode)
            else:raise RuntimeError('IRQ_INCOMPLETE_TRACE_ACCEPTED')


def main():
    c=rtl_checks.Checks('interrupts',task='T045',scope='Enabled CSR/trap/timer CPU and SoC simulation, unit mutants, random waits/reset/cancellation, actual production top and compiled firmware')
    c.result['excluded']=['formal T023 skipped/NOT RUN','full FPGA synthesis/place/route/timing/power/CDC/bitstream','physical board','ASIC']
    code=1
    try:
        m=rtl_checks.load_manifest();rtl=soc_checks.sources(m)
        benches=['dv/unit/tb_csr.sv','dv/integration/tb_timer_irq.sv','dv/integration/tb_interrupts.sv','dv/integration/tb_interrupt_waits.sv','dv/integration/tb_interrupt_aborts.sv','dv/integration/tb_interrupt_board.sv','dv/integration/tb_interrupt_priority.sv']
        extra=['fpga/basys3/top.sv','dv/integration/irq_wait_soc.sv']
        names=list(dict.fromkeys(rtl+benches+extra+['dv/unit/test_csr.py','dv/integration/test_interrupts.py','dv/integration/interrupt_model.py','dv/integration/soc_model.py','dv/integration/test_mmio.py','dv/unit/test_uart_rx.py','dv/reference/rv32_iss.py',
            'scripts/interrupt_checks.py','scripts/interrupt_firmware.py','scripts/soc_checks.py','scripts/firmware_image.py','scripts/firmware_build.py','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py','scripts/verify.py','scripts/test_verify.py',
            'sw/boot.S','sw/interrupt_smoke.S','sw/linker.ld','fpga/basys3/irq_boot.mem','fpga/basys3/soc_boot.mem','config/rtl_checks.json','config/fpga_build.json','RV32I_Edge_SoC.xpr','docs/INTERRUPT_SPEC.md','docs/INTERRUPT_CONTRACT.json','docs/ARCH_CONTRACT.json','.harness/checks.json','.harness/software_toolchain.json']))
        c.result['source_sha256']={n:sha(harness.inside(n)) for n in names};c.versions(m)
        raw,symbols=interrupt_firmware.build(c,c.base/'compiler');work=c.base/'simulation';work.mkdir();harness.atomic_text(work/'irq_boot.mem',words(raw))
        soc_checks.compile_design(c,work,rtl+extra,benches)
        for top,snapshot in [('tb_csr','csr'),('tb_timer_irq','timer'),('tb_interrupts','fast'),('tb_interrupt_waits','waits'),('tb_interrupt_aborts','aborts'),('tb_interrupt_board','board'),('tb_interrupt_priority','priority')]:soc_checks.elaborate(c,work,top,snapshot)
        for seed in (1,20261107):
            for snapshot,top,generator,marker in [('csr','tb_csr',test_csr.corpus,'CSR_SIM_PASS'),('timer','tb_timer_irq',test_interrupts.timer_corpus,'TIMER_IRQ_SIM_PASS')]:
                text=generator(seed);vector_run(c,work,snapshot,top,snapshot+'-'+str(seed),text,seed,marker)
                c.result.setdefault('unit_runs',[]).append(dict(unit=snapshot,seed=seed,vectors=len(text.splitlines())))
        for snapshot,top,generator,marker,prefix,index in [('csr','tb_csr',test_csr.corpus,'CSR_SIM_PASS','CSR',19),('timer','tb_timer_irq',test_interrupts.timer_corpus,'TIMER_IRQ_SIM_PASS','TIMER_IRQ',32)]:
            text=generator(1);row=text.splitlines()[0].split();row[index]='1'
            for mode,bad,diagnostic in [('wrong-expected',' '.join(row)+'\n',prefix+'_MISMATCH'),('empty','',prefix+'_EMPTY_VECTORS'),('truncated',text.splitlines()[0]+'\n0 1\n',prefix+'_MALFORMED_VECTOR')]:
                vector_run(c,work,snapshot,top,snapshot+'-'+mode,bad,1,marker,diagnostic)
        for seed in (1,20261107):
            boot(c,work,'fast','tb_interrupts','fast-'+str(seed),seed,8,raw,symbols)
            boot(c,work,'waits','tb_interrupt_waits','waits-'+str(seed),seed,8,raw,symbols)
            boot(c,work,'aborts','tb_interrupt_aborts','aborts-'+str(seed),seed,8,raw,symbols,6)
        boot(c,work,'board','tb_interrupt_board','production',1,868,raw,symbols)
        # A deliberate illegal instruction after the polling load creates an
        # age-ordered synchronous fault while the external IRQ becomes eligible.
        enable=(0x30046073).to_bytes(4,'little');c.require(raw.count(enable)==1,'Unique global-enable instruction in actual firmware')
        fault_pc=raw.index(enable)+16;c.require(int.from_bytes(raw[fault_pc:fault_pc+4],'little')&127==0x63,'Selected post-load branch for directed priority case')
        priority=bytearray(raw);priority[fault_pc:fault_pc+4]=(0xffffffff).to_bytes(4,'little')
        harness.atomic_text(work/'irq_boot-priority.mem',words(priority));c.result['priority_patch']={'address':fault_pc,'old_word':int.from_bytes(raw[fault_pc:fault_pc+4],'little'),'new_word':0xffffffff}
        try:
            harness.atomic_text(work/'irq_boot.mem',words(priority))
            for seed in (1,20261107):boot(c,work,'priority','tb_interrupt_priority','priority-'+str(seed),seed,8,bytes(priority),symbols)
        finally:harness.atomic_text(work/'irq_boot.mem',words(raw))
        corrupt=bytearray(raw);corrupt[symbols['__data_load']]^=1;harness.atomic_text(work/'irq_boot-corrupt.mem',words(corrupt))
        try:
            harness.atomic_text(work/'irq_boot.mem',words(corrupt));boot(c,work,'fast','tb_interrupts','corrupt-image',1,8,raw,symbols,corrupt=True)
        finally:harness.atomic_text(work/'irq_boot.mem',words(raw))
        mutants=[('csr-zero-index','rtl/core/csr_file.sv','|| !source_zero_i','|| (operand_i!=32\'d0)','tb_csr','csr',test_csr.corpus,'CSR_MISMATCH','CSR_SIM_PASS'),
            ('mret-mpie','rtl/core/csr_file.sv',"mpie_q<=1'b1;","mpie_q<=1'b0;",'tb_csr','csr',test_csr.corpus,'CSR_MISMATCH','CSR_SIM_PASS'),
            ('admission-pc','rtl/core/trap_control.sv','continuation_q<=retire_next_pc_i;','continuation_q<=retire_next_pc_i+32\'d4;','tb_csr','csr',test_csr.corpus,'CSR_MISMATCH','CSR_SIM_PASS'),
            ('timer-pending','rtl/peripherals/timer.sv','ctrl_q[2] && matched_q','ctrl_q[2] && ctrl_q[0] && matched_q','tb_timer_irq','timer',test_interrupts.timer_corpus,'TIMER_IRQ_MISMATCH','TIMER_IRQ_SIM_PASS')]
        for label,name,before,after,top,snapshot,generator,diagnostic,marker in mutants:
            original=harness.inside(name).read_text(encoding='utf-8');c.require(original.count(before)==1,'Unique actual RTL mutation '+label)
            folder=c.base/label;folder.mkdir();path=folder/Path(name).name;harness.atomic_text(path,original.replace(before,after))
            changed=[path.relative_to(harness.ROOT).as_posix() if n==name else n for n in rtl]
            soc_checks.compile_design(c,folder,changed,[benches[0] if top=='tb_csr' else benches[1]]);soc_checks.elaborate(c,folder,top,snapshot)
            vector_run(c,folder,snapshot,top,label,generator(1),1,marker,diagnostic)
        folder=c.base/'core-resume';folder.mkdir();name='rtl/core/pipeline_cpu.sv';original=harness.inside(name).read_text(encoding='utf-8')
        before='w.result.pc[31:2] : irq_resume[31:2]';after="w.result.pc[31:2] : (irq_resume[31:2]+30'd1)"
        c.require(original.count(before)==1 and original.count('w.result.pc : irq_resume;')==1,'Coherent saved-PC core mutation sites')
        mutated=original.replace(before,after).replace('w.result.pc : irq_resume;',"w.result.pc : (irq_resume+32'd4);")
        path=folder/'pipeline_cpu.sv';harness.atomic_text(path,mutated);harness.atomic_text(folder/'irq_boot.mem',words(raw))
        changed=[path.relative_to(harness.ROOT).as_posix() if n==name else n for n in rtl]
        soc_checks.compile_design(c,folder,changed,['dv/integration/tb_interrupts.sv']);soc_checks.elaborate(c,folder,'tb_interrupts','core_bad')
        trace=folder/'mutant.trace';r=soc_checks.simulate(c,folder,'core_bad','core-resume',['SEED=1','TRACE='+str(trace),'SIG=%x'%symbols['signature'],'STOP_AT_IRQ'],'/tb_interrupts/clk /tb_interrupts/tv /tb_interrupts/tp',60)
        c.require(rtl_checks.successful(r,'IRQ_MUTANT_CAPTURE'),'Actual wrong-resume core trace captured without timeout',r)
        try:interrupt_model.check_trace(trace.read_text(encoding='ascii'),raw,symbols,8)
        except ValueError as exc:c.require(str(exc).startswith('IRQ_TRAP_MISMATCH'),'Independent checker rejects actual wrong-resume core')
        else:raise RuntimeError('IRQ_BAD_CORE_ACCEPTED')
        c.require(all(sha(harness.inside(n))==h for n,h in c.result['source_sha256'].items()),'All interrupt validation inputs unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['artifacts']={p.relative_to(harness.ROOT).as_posix():sha(p) for p in c.base.rglob('*') if p.is_file()}
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save();print(json.dumps(dict(status=c.result['status'],evidence=c.path.relative_to(harness.ROOT).as_posix(),error=c.result.get('error'))));return code


if __name__=='__main__':sys.exit(main())
