#!/usr/bin/env python3
"""Real installed RV32 assembler/linker build, strict ELF image and ISS smoke."""
import argparse
import datetime as dt
import hashlib
import json
import random
import sys
from pathlib import Path
import harness
import rtl_checks
from firmware_image import parse_elf,words
sys.path.insert(0,str(harness.inside('dv/reference')))
from rv32_iss import RV32ISS


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(c, directory, prepare=False):
    config=harness.read(harness.inside('.harness/software_toolchain.json'))
    for file,digest in config['components_sha256'].items():
        if sha(file)!=digest:raise ValueError('Compiler component changed: '+file)
    def command(name,args):
        tool=config['tools'][name]
        if sha(tool['command'][0])!=tool['sha256']:raise ValueError('Installed executable changed: '+name)
        return c.command(tool['command']+args,directory,30)
    for name,tool in config['tools'].items():
        r=command(name,['--version'])
        c.require(rtl_checks.successful(r) and r['stdout'].splitlines()[0]==tool['version_line'],'Pinned software tool '+name,r)
    r=command('gcc',['-dumpmachine'])
    c.require(rtl_checks.successful(r) and r['stdout'].strip()==config['target'],'Actual RV32 compiler target',r)
    c.result['software_toolchain']=config
    for source in ('boot','smoke'):
        r=command('gcc',['-march=rv32i','-mabi=ilp32','-misa-spec=20191213','-mno-relax','-Wa,--fatal-warnings',
            '-c',str(harness.inside('sw/'+source+'.S')),'-o',str(directory/(source+'.o'))])
        c.require(rtl_checks.successful(r),'Actual RV32I assembly '+source,r)
    elf=directory/'firmware.elf';binary=directory/'firmware.bin';mapfile=directory/'firmware.map'
    linker=['-m','elf32lriscv','--no-relax','--fatal-warnings','-T',str(harness.inside('sw/linker.ld')),
        '-Map',str(mapfile),'-o',str(elf),str(directory/'boot.o'),str(directory/'smoke.o')]
    r=command('ld',linker)
    c.require(rtl_checks.successful(r),'Actual approved-map link',r)
    raw,segments,symbols=parse_elf(elf.read_bytes())
    r=command('objcopy',['-O','binary','--gap-fill','0','--pad-to','0x10000',str(elf),str(binary)])
    c.require(rtl_checks.successful(r) and binary.read_bytes()==raw,'Independent ELF LMA image equals objcopy,64KiB',r)
    for tool,args,file in [('readelf',['-h','-lW','-sW','-A'],'readelf.txt'),('objdump',['-d','-M','no-aliases'],'disassembly.txt')]:
        r=command(tool,args+[str(elf)]);c.require(rtl_checks.successful(r),'Actual '+tool+' report',r)
        harness.atomic_text(directory/file,r['stdout'])
    generated=directory/'rom_init.mem';harness.atomic_text(generated,words(raw))
    target=harness.inside('fpga/basys3/rom_init.mem')
    if prepare and not target.exists():harness.atomic_text(target,words(raw))
    c.require(target.is_file() and target.read_bytes()==generated.read_bytes(),'Complete committed ROM image matches fresh actual build')
    boot_runs=[]
    for seed in (1,20261104):
        rng=random.Random(seed)
        image=dict(enumerate(raw));image.update({addr:rng.randrange(1,256) for addr in range(0x10000,0x20000)})
        model=RV32ISS(image)
        for phase in ('dirty-start','warm-reset'):
            if phase=='warm-reset':
                for addr in range(symbols['__data_start'],symbols['__bss_end']):model.memory[addr]=0xa5
                model.memory[0x1e000]=0x5a;model.reset()
            events,fault=model.run(5000)
            value=lambda addr:int.from_bytes(bytes(model.memory.get(addr+i,0) for i in range(4)),'little')
            c.require(fault.code==8 and fault.pc==symbols['halt_ecall'] and model.regs[10]==0 and
                model.regs[2]==symbols['__stack_top'] and value(symbols['signature'])==0x600d600d and
                value(symbols['initial_data'])==0xcafebabe and value(symbols['initial_data']+4)==0x13579bdf and
                value(symbols['zero_area'])==0 and value(symbols['zero_area']+4)==0,
                'Independent compiled boot '+phase+' seed='+str(seed))
            if phase=='warm-reset':c.require(model.memory[0x1e000]==0x5a,'Warm reset keeps memory outside runtime init')
            trace=directory/('iss_%d_%s.json'%(seed,phase))
            harness.atomic(trace,{'events':[e.fields() for e in events],'fault':vars(fault),'registers':model.regs})
            boot_runs.append({'seed':seed,'phase':phase,'retirements':len(events),'trace':trace.relative_to(harness.ROOT).as_posix()})
    # Execute corrupted real images in the independent model; do not count an
    # arbitrary failure as the intended negative control.
    image=dict(enumerate(raw));image.update({i:0 for i in range(4)})
    _,fault=RV32ISS(image).run(5000)
    c.require(fault.code==1 and fault.pc==0,'Corrupted entry instruction rejected as illegal')
    image=dict(enumerate(raw));image[symbols['__data_load']]^=1
    model=RV32ISS(image);_,fault=model.run(5000)
    c.require(fault.code==8 and model.regs[10]==1 and model._word(symbols['signature'])==0,'Corrupted copied data reaches explicit smoke failure')
    for region,section in [('ROM','.rodata'),('RAM','.bss')]:
        source=directory/('overflow_'+region+'.S');obj=source.with_suffix('.o')
        harness.atomic_text(source,'.section '+section+',"'+('a' if region=='ROM' else 'aw')+'",@'+('progbits' if region=='ROM' else 'nobits')+'\n.space 65536\n.section .note.GNU-stack,"",@progbits\n')
        r=command('gcc',['-march=rv32i','-mabi=ilp32','-mno-relax','-c',str(source),'-o',str(obj)])
        c.require(rtl_checks.successful(r),'Overflow stimulus assembles '+region,r)
        badlink=list(linker)
        badlink[badlink.index('-o')+1]=str(directory/('overflow_'+region+'.elf'))
        badlink[badlink.index('-Map')+1]=str(directory/('overflow_'+region+'.map'))
        r=command('ld',badlink+[str(obj)])
        text=r['stdout']+r['stderr'];diagnostic='ROM image exceeds approved region' if region=='ROM' else 'RAM/stack collision'
        c.require(r['status']=='FAIL' and r['exit_code']!=0 and diagnostic in text,'Actual linker overflow rejected '+region,r)
    # Failed overflow links target separate files to preserve the positive ELF.
    c.result['boot_runs']=boot_runs;c.result['segments']=segments;c.result['symbols']=symbols
    c.require(all(sha(file)==digest for file,digest in config['components_sha256'].items()),'Compiler components unchanged')
    artifacts={p.relative_to(harness.ROOT).as_posix():sha(p) for p in directory.iterdir() if p.is_file()}
    c.result.setdefault('artifacts',{}).update(artifacts)
    return raw,symbols


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    c=rtl_checks.Checks('firmware-build',task='T026',scope='Real RV32I firmware image and independent ISS; no RTL CPU/SoC execution')
    code=1
    try:
        sources=['sw/boot.S','sw/smoke.S','sw/linker.ld','.harness/software_toolchain.json','scripts/firmware_image.py','scripts/firmware_build.py','dv/reference/rv32_iss.py','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={f:sha(harness.inside(f)) for f in sources}
        build(c,c.base/'compiler',args.prepare)
        c.result['source_sha256']['fpga/basys3/rom_init.mem']=sha(harness.inside('fpga/basys3/rom_init.mem'))
        c.require(all(sha(harness.inside(f))==h for f,h in c.result['source_sha256'].items()),'Firmware sources unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
