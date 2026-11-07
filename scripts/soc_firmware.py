"""Build a separate actual RV32I SoC image, preserving the T026 smoke image."""
import argparse
import datetime as dt
import json
import sys
import harness,rtl_checks
from firmware_build import sha
from firmware_image import parse_elf,words


def build(c,directory,prepare=False):
    config=harness.read(harness.inside('.harness/software_toolchain.json'))
    for path,digest in config['components_sha256'].items():
        if sha(path)!=digest:raise ValueError('Installed compiler component changed')
    def command(name,args):
        tool=config['tools'][name]
        if sha(tool['command'][0])!=tool['sha256']:raise ValueError('Installed compiler executable changed')
        return c.command(tool['command']+args,directory,30)
    for name,tool in config['tools'].items():
        r=command(name,['--version']);c.require(rtl_checks.successful(r) and r['stdout'].splitlines()[0]==tool['version_line'],'Pinned software tool '+name,r)
    r=command('gcc',['-dumpmachine']);c.require(rtl_checks.successful(r) and r['stdout'].strip()==config['target'],'Actual RV32 compiler target',r)
    for source in ('boot','soc_smoke'):
        r=command('gcc',['-march=rv32i','-mabi=ilp32','-misa-spec=20191213','-mno-relax','-Wa,--fatal-warnings','-c',str(harness.inside('sw/'+source+'.S')),'-o',str(directory/(source+'.o'))])
        c.require(rtl_checks.successful(r),'Actual SoC assembly '+source,r)
    elf=directory/'soc.elf';binary=directory/'soc.bin';mapfile=directory/'soc.map'
    r=command('ld',['-m','elf32lriscv','--no-relax','--fatal-warnings','-T',str(harness.inside('sw/linker.ld')),'-Map',str(mapfile),'-o',str(elf),str(directory/'boot.o'),str(directory/'soc_smoke.o')])
    c.require(rtl_checks.successful(r),'Actual SoC approved-map link',r)
    raw,segments,symbols=parse_elf(elf.read_bytes())
    r=command('objcopy',['-O','binary','--gap-fill','0','--pad-to','0x10000',str(elf),str(binary)])
    c.require(rtl_checks.successful(r) and binary.read_bytes()==raw,'Independent SoC ELF LMA image equals objcopy64KiB',r)
    for tool,args,name in [('readelf',['-h','-lW','-sW','-A'],'readelf.txt'),('objdump',['-d','-M','no-aliases'],'disassembly.txt')]:
        r=command(tool,args+[str(elf)]);c.require(rtl_checks.successful(r),'Actual SoC '+tool,r);harness.atomic_text(directory/name,r['stdout'])
    generated=directory/'soc_boot.mem';harness.atomic_text(generated,words(raw));target=harness.inside('fpga/basys3/soc_boot.mem')
    if prepare and not target.exists():harness.atomic_text(target,words(raw))
    c.require(target.is_file() and target.read_bytes()==generated.read_bytes(),'Committed separate SoC image matches fresh actual build')
    c.result['software_toolchain']=config;c.result['symbols']=symbols;c.result['segments']=segments
    c.result.setdefault('artifacts',{}).update({p.relative_to(harness.ROOT).as_posix():sha(p) for p in directory.iterdir() if p.is_file()})
    return raw,symbols


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    c=rtl_checks.Checks('soc-firmware',task='T031',scope='Actual separate RV32I firmware preparation, no CPU/SoC/hardware claim')
    code=1
    try:
        names=['sw/boot.S','sw/soc_smoke.S','sw/linker.ld','.harness/software_toolchain.json','scripts/soc_firmware.py','scripts/firmware_image.py','docs/ARCH_CONTRACT.json']
        c.result['source_sha256']={n:sha(harness.inside(n)) for n in names};build(c,c.base/'compiler',args.prepare)
        c.result['source_sha256']['fpga/basys3/soc_boot.mem']=sha(harness.inside('fpga/basys3/soc_boot.mem'))
        c.result['status']='PASS';code=0
    except (RuntimeError,ValueError,KeyError,OSError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save();print(json.dumps({'status':c.result['status'],'receipt':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}));return code


if __name__=='__main__':sys.exit(main())
