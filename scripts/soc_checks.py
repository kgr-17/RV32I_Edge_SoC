"""Actual T031 fabric and compiled SoC checks; no full FPGA implementation."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
import harness,rtl_checks,soc_firmware
from firmware_image import words
sys.path.insert(0,str(harness.inside('dv/integration')))
from test_soc_boot import fabric_vectors,pattern_rom
from soc_model import check_trace


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(manifest):
    core=next(d['sources'] for d in manifest['lint_designs'] if d['top']=='pipeline_cpu_lint_top')
    return list(dict.fromkeys([n for n in core if n.startswith('rtl/')]+[
        'rtl/memory/boot_rom.sv','rtl/memory/data_ram.sv','rtl/peripherals/uart_tx.sv',
        'rtl/peripherals/uart_rx.sv','rtl/peripherals/uart_mmio.sv','rtl/peripherals/input_sync.sv',
        'rtl/peripherals/gpio.sv','rtl/peripherals/timer.sv','rtl/peripherals/reset_sync.sv',
        'rtl/soc/soc_fabric.sv','rtl/soc/edge_soc.sv']))


def compile_design(c,work,rtl,benches):
    r=c.vendor('xvlog',['--sv']+[str(harness.inside(n)) for n in rtl+benches],work,30)
    c.require(rtl_checks.successful(r),'Actual SoC/fabric compile '+work.name,r)


def elaborate(c,work,top,snapshot):
    r=c.vendor('xelab',['work.'+top,'--snapshot',snapshot,'--timescale','1ns/1ps','--debug','typical'],work,45)
    c.require(rtl_checks.successful(r),'Actual elaboration '+top,r)


def simulate(c,work,snapshot,label,arguments,scope,timeout=45):
    tcl=work/(label+'.tcl');wave=work/(label+'.wdb')
    harness.atomic_text(tcl,'log_wave '+scope+'\nrun all\nquit\n')
    args=[snapshot,'--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit','--wdb',str(wave)]
    for arg in arguments:args+=['--testplusarg',arg]
    r=c.xsim(args,work,timeout,label)
    c.require(wave.is_file() and wave.stat().st_size>0,'Waveform retained '+label)
    return r


def check_boot(c,work,snapshot,label,seed,divider,raw,symbols,negative=False):
    trace=work/(label+'.trace');scope='/tb_soc_board' if divider==868 else '/tb_soc_boot'
    r=simulate(c,work,snapshot,label,['SEED='+str(seed),'TRACE='+str(trace)],
        ' '.join(scope+'/'+n for n in ('clk','rst','rx','tx','leds','rv','pc','fv')),60)
    # Completion alone never implies firmware/serial/ISA correctness.
    marker='SOC_RUN_COMPLETE seed=%d divisor=%d'%(seed,divider)
    c.require(rtl_checks.successful(r) and sum(s.startswith(marker+' ') for s in r['stdout'].splitlines())==1,'Native boot completed '+label,r)
    if negative:
        try:check_trace(trace.read_text(),raw,symbols,divider)
        except ValueError as exc:
            c.require(str(exc).startswith('SOC_DMEM_RESPONSE'),'Actual corrupt-ROM rejected by bus oracle')
            c.result['corrupt_rom_diagnostic']=str(exc)
        else:raise RuntimeError('SOC_CORRUPT_ROM_ACCEPTED')
        return
    summary=check_trace(trace.read_text(),raw,symbols,divider)
    harness.atomic(work/(label+'.summary.json'),summary)
    c.require(summary['uart_bytes']==12 and len(summary['epochs'])==2,'Independent bus/ISA/RAM/UART cold+warm boot '+label)
    c.result.setdefault('boots',[]).append(dict(label=label,seed=seed,divider=divider,trace=trace.relative_to(harness.ROOT).as_posix(),summary=summary))
    # Corrupt actual observations, without modifying expected architectural state.
    rows=trace.read_text().splitlines();retire=next(i for i,line in enumerate(rows) if int(line.split()[26],16))
    changed=list(rows);row=changed[retire].split();row[29]='00000000';changed[retire]=' '.join(row)
    for mode,text,diagnostic in [('wrong-retirement','\n'.join(changed)+'\n','SOC_RETIRE_MISMATCH'),
            ('truncated','\n'.join(rows[:retire+1])+'\n','SOC_MISSING_PHASE'),('empty','','SOC_TRACE_SHAPE')]:
        path=work/(label+'-'+mode+'.trace');harness.atomic_text(path,text)
        try:check_trace(text,raw,symbols,divider)
        except ValueError as exc:c.require(str(exc).startswith(diagnostic),'Trace checker rejects '+label+' '+mode)
        else:raise RuntimeError('SOC_BAD_TRACE_ACCEPTED '+mode)


def main():
    c=rtl_checks.Checks('soc',task='T031',scope='Actual compiled RV32I CPU/memory/peripheral simulation, independent architectural/bus/serial checks; fabric unit DV')
    c.result['excluded']=['formal (T023 owner-skipped)','full FPGA synthesis/implementation/timing/power/bitstream','physical hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest();rtl=sources(manifest)
        names=rtl+['dv/integration/tb_soc_boot.sv','dv/integration/tb_soc_board.sv','dv/integration/tb_soc_fabric.sv','dv/integration/test_soc_boot.py',
            'dv/integration/soc_model.py','dv/unit/test_uart_rx.py','dv/integration/test_mmio.py','dv/firmware/memory_model.py',
            'dv/reference/rv32_iss.py','scripts/soc_checks.py','scripts/soc_firmware.py','scripts/firmware_image.py',
            'scripts/firmware_build.py','scripts/rtl_checks.py','scripts/tool_runner.py','scripts/tool_child.py',
            'sw/boot.S','sw/linker.ld','sw/soc_smoke.S','fpga/basys3/soc_boot.mem','config/rtl_checks.json',
            'config/fpga_build.json','fpga/basys3/top.sv','RV32I_Edge_SoC.xpr','docs/ARCH_CONTRACT.json','.harness/software_toolchain.json']
        c.result['source_sha256']={n:sha(harness.inside(n)) for n in names};c.versions(manifest)
        raw,symbols=soc_firmware.build(c,c.base/'compiler')
        work=c.base/'simulation';work.mkdir();harness.atomic_text(work/'soc_boot.mem',words(raw));harness.atomic_text(work/'fabric_pattern.mem',words(pattern_rom()))
        compile_design(c,work,rtl+['fpga/basys3/top.sv'],['dv/integration/tb_soc_boot.sv','dv/integration/tb_soc_board.sv','dv/integration/tb_soc_fabric.sv'])
        for top,snapshot in [('tb_soc_boot','soc_fast'),('tb_soc_board','soc_default'),('tb_soc_fabric','fabric')]:elaborate(c,work,top,snapshot)
        for seed in (1,20261107):
            text,summary=fabric_vectors(seed);path=work/('fabric-'+str(seed)+'.txt');harness.atomic_text(path,text)
            r=simulate(c,work,'fabric','fabric-'+str(seed),['SEED='+str(seed),'VECTORS='+str(path)],'/tb_soc_fabric/clk /tb_soc_fabric/rst /tb_soc_fabric/ir /tb_soc_fabric/is /tb_soc_fabric/dr /tb_soc_fabric/ds /tb_soc_fabric/leds')
            c.require(rtl_checks.successful(r,'FABRIC_SIM_PASS seed=%d checked=%d'%(seed,summary['cycles'])),'Independent fabric vectors '+str(seed),r)
            c.result.setdefault('fabric_runs',[]).append(summary)
        text,_=fabric_vectors(1);first=text.splitlines()[0].split();first[12]='1'
        for mode,body,diagnostic in [('wrong-expected',' '.join(first)+'\n','FABRIC_MISMATCH'),('empty','','FABRIC_EMPTY_VECTORS'),('truncated',text.splitlines()[0]+'\n0 1\n','FABRIC_MALFORMED_VECTOR')]:
            path=work/('fabric-'+mode+'.txt');harness.atomic_text(path,body)
            r=simulate(c,work,'fabric','fabric-'+mode,['SEED=1','VECTORS='+str(path)],'/tb_soc_fabric/clk /tb_soc_fabric/rst')
            output=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and diagnostic in output and 'FABRIC_SIM_PASS' not in output,'Actual fabric negative '+mode,r)
        for seed in (1,20261107):check_boot(c,work,'soc_fast','fast-'+str(seed),seed,8,raw,symbols)
        check_boot(c,work,'soc_default','production',1,868,raw,symbols)
        corrupt=bytearray(raw);corrupt[symbols['__data_load']]^=1
        harness.atomic_text(work/'soc_boot-corrupt.mem',words(corrupt))
        try:
            harness.atomic_text(work/'soc_boot.mem',words(corrupt))
            check_boot(c,work,'soc_fast','corrupt-rom',1,8,raw,symbols,True)
        finally:harness.atomic_text(work/'soc_boot.mem',words(raw))
        # A real early-store mutant must corrupt RAM even though reset cancels reply.
        mutant=c.base/'early-store';mutant.mkdir();harness.atomic_text(mutant/'fabric_pattern.mem',words(pattern_rom()))
        original=harness.inside('rtl/soc/soc_fabric.sv').read_text();changed=original.replace('wire logic ram_write=!rst_i && d_pending_q', 'wire logic early_write=!rst_i && dq_accept && decoded==RAM && d_req_write_i;\n    wire logic ram_write=!rst_i && d_pending_q')
        changed=changed.replace('.en_i(ram_read || ram_write)', '.en_i(ram_read || ram_write || early_write)').replace('.addr_i(ram_read ? d_req_addr_i[15:2] : pending_addr_q)', '.addr_i((ram_read || early_write) ? d_req_addr_i[15:2] : pending_addr_q)').replace('.write_be_i(ram_write ? pending_be_q : 4\'b0000),.write_data_i(pending_data_q)', '.write_be_i(early_write ? d_req_be_i : (ram_write ? pending_be_q : 4\'b0000)),.write_data_i(early_write ? d_req_wdata_i : pending_data_q)')
        c.require(changed!=original and 'early_write ? d_req_be_i' in changed,'Complete coherent early-write RTL mutation')
        path=mutant/'soc_fabric.sv';harness.atomic_text(path,changed)
        mutation_rtl=[path.relative_to(harness.ROOT).as_posix() if n=='rtl/soc/soc_fabric.sv' else n for n in rtl]
        compile_design(c,mutant,mutation_rtl,['dv/integration/tb_soc_fabric.sv']);elaborate(c,mutant,'tb_soc_fabric','early_store')
        vector=mutant/'vectors.txt';harness.atomic_text(vector,text)
        r=simulate(c,mutant,'early_store','early-store',['SEED=1','VECTORS='+str(vector)],'/tb_soc_fabric/clk /tb_soc_fabric/rst')
        c.require(r['status'] in ('PASS','FAIL') and 'FABRIC_MISMATCH' in r['stdout']+r['stderr'] and 'FABRIC_SIM_PASS' not in r['stdout'],'Actual early-store/reset-cancellation RTL defect rejected',r)
        c.require(all(sha(harness.inside(n))==h for n,h in c.result['source_sha256'].items()),'All SoC inputs unchanged through validation')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['artifacts']={p.relative_to(harness.ROOT).as_posix():sha(p) for p in c.base.rglob('*') if p.is_file()}
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps(dict(status=c.result['status'],evidence=c.path.relative_to(harness.ROOT).as_posix(),error=c.result.get('error'))));return code


if __name__=='__main__':sys.exit(main())
