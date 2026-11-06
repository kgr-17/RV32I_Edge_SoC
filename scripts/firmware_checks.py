#!/usr/bin/env python3
"""T026 real compiler/linker, independent ISS and actual synchronous BRAM DV."""
import datetime as dt
import json
import sys
import harness
import rtl_checks
from firmware_build import build,sha
sys.path.insert(0,str(harness.inside('dv/firmware')))
import memory_model


def main():
    c=rtl_checks.Checks('firmware',task='T026',scope='Compiled RV32I boot/ISS plus primitive memory RTL; no SoC or physical hardware')
    c.result['excluded']=['actual compiled CPU/SoC execution','local-bus adapter','UART/MMIO','IRQ','formal','routed timing','physical hardware','ASIC']
    code=1
    try:
        manifest=rtl_checks.load_manifest()
        sources=['sw/boot.S','sw/smoke.S','sw/linker.ld','.harness/software_toolchain.json','fpga/basys3/rom_init.mem',
            'scripts/firmware_image.py','scripts/firmware_build.py','scripts/firmware_checks.py','scripts/test_firmware.py',
            'scripts/vivado_memory_check.tcl','scripts/rtl_checks.py','scripts/test_rtl_checks.py','config/rtl_checks.json',
            'rtl/memory/boot_rom.sv','rtl/memory/data_ram.sv','dv/lint/memory_lint_top.sv',
            'dv/firmware/memory_model.py','dv/firmware/tb_memories.sv','dv/reference/rv32_iss.py','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources}
        c.versions(manifest)
        raw,symbols=build(c,c.base/'compiler')
        boot=[int.from_bytes(raw[i:i+4],'little') for i in range(0,len(raw),4)]
        cwd=c.base/'memories';cwd.mkdir()
        rom=cwd/'rom_init.mem';harness.atomic_text(rom,harness.inside('fpga/basys3/rom_init.mem').read_text())
        pattern=cwd/'rom_pattern.mem';harness.atomic_text(pattern,''.join('%08x\n'%w for w in memory_model.pattern_words()))
        c.result.setdefault('artifacts',{}).update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (rom,pattern)})
        r=c.vendor('xvlog',['--sv']+[str(harness.inside(f)) for f in ['rtl/memory/boot_rom.sv','rtl/memory/data_ram.sv','dv/firmware/tb_memories.sv']],cwd,15)
        c.require(rtl_checks.successful(r),'Actual memory compile',r)
        r=c.vendor('xelab',['work.tb_memories','--snapshot','memory_snapshot','--timescale','1ns/1ps','--debug','typical'],cwd,30)
        c.require(rtl_checks.successful(r),'Actual memory elaboration',r)
        tcl=cwd/'run.tcl';harness.atomic_text(tcl,'log_wave /tb_memories/clk /tb_memories/rst /tb_memories/ae /tb_memories/be /tb_memories/re /tb_memories/aa /tb_memories/ba /tb_memories/ra /tb_memories/mask /tb_memories/data /tb_memories/pa /tb_memories/pb /tb_memories/boot_a /tb_memories/boot_b /tb_memories/ram_data /tb_memories/pav /tb_memories/pbv /tb_memories/rv\nrun all\nquit\n')
        c.result['artifacts'][tcl.relative_to(harness.ROOT).as_posix()]=sha(tcl)
        def simulate(vector,seed,label):
            wave=cwd/(label+'.wdb')
            record=c.xsim(['memory_snapshot','--tclbatch',str(tcl),'--onerror','quit','--onfinish','quit','--sv_seed',str(seed),
                '--testplusarg','SEED='+str(seed),'--testplusarg','VECTORS='+str(vector),'--wdb',str(wave)],cwd,30,label)
            return record,wave
        for seed in (1,20261104):
            vector=cwd/('vectors_%d.txt'%seed);harness.atomic_text(vector,memory_model.vectors(seed,boot))
            count=len(vector.read_text().splitlines());r,wave=simulate(vector,seed,'seed_'+str(seed))
            c.require(rtl_checks.successful(r,'MEMORY_SIM_PASS seed=%d checked=%d'%(seed,count)),'Independent primitive memory scoreboard seed='+str(seed),r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Positive memory waveform')
            c.result['simulations'].append({'seed':seed,'checked_vectors':count,'vector_path':vector.relative_to(harness.ROOT).as_posix(),'vector_sha256':sha(vector),'waveform':wave.relative_to(harness.ROOT).as_posix(),'waveform_sha256':sha(wave)})
        first=memory_model.vectors(1,boot).splitlines()[0].split();first[9]='1'
        for label,text,diagnostic in [('wrong-expected',' '.join(first)+'\n','MEMORY_MISMATCH'),('empty','','MEMORY_EMPTY_VECTORS')]:
            vector=cwd/(label+'.txt');harness.atomic_text(vector,text);r,wave=simulate(vector,1,label)
            out=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and diagnostic in out and 'MEMORY_SIM_PASS' not in out,'Actual memory negative '+label,r)
            c.require(wave.is_file() and wave.stat().st_size>0,'Negative memory waveform')
            c.result['artifacts'].update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in (vector,wave)})
        synth=c.base/'inference';synth.mkdir()
        harness.atomic_text(synth/'rom_init.mem',harness.inside('fpga/basys3/rom_init.mem').read_text())
        r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('scripts/vivado_memory_check.tcl')),'-tclargs',str(harness.ROOT)],synth,90)
        c.require(rtl_checks.successful(r,'MEMORY_INFERENCE_PASS') and 'SW Build '+manifest['vivado_sw_build'] in r['stdout'],'Actual selected-part ROM and RAM block inference',r)
        for path in (synth/'rom_init.mem',synth/'memory_utilization.rpt',synth/'memory_drc.rpt'):
            c.result['artifacts'][path.relative_to(harness.ROOT).as_posix()]=sha(path)
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'All firmware and memory sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
