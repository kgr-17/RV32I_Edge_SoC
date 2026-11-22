"""Bounded, owner-authorized Basys 3 SRAM programming and physical UART evidence.

Workflow acknowledgments are not authentication or a security sandbox.
No simulator output is accepted as physical evidence. No flash commands exist.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import harness
import rtl_checks
import tool_runner

AUTH = 'evidence/owner_reviews/T032-2026-11-15-authorization.json'
IMAGE_SHA = '13f3639d2b01feded384a1316207a0ddb02fb5d4036bc399901fc87fd2aacbd9'
SOURCES = ['scripts/hardware.py','scripts/hardware.tcl','scripts/hardware_serial.py']
SUCCESS = b'IRQ PASS\r\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(harness.ROOT.resolve()).as_posix()


def context():
    _, state = harness.load()
    if state['active'] != 'T032' or state['task_states']['T032'] not in ('in_progress','failed'):
        raise ValueError('HARDWARE_ACTIVE_T032_REQUIRED')
    if 'T032' not in state['start_approvals'] or state['task_states']['T043'] != 'completed':
        raise ValueError('HARDWARE_START_AUTHORITY_REQUIRED')
    owner = harness.read(harness.inside(AUTH))
    if (owner.get('answer') != 'Authorize T032 and that command' or
            owner.get('physical_programming_authorized') is not True or
            owner.get('spi_flash_programming_authorized') is not False or owner.get('bitstream_sha256') != IMAGE_SHA):
        raise ValueError('HARDWARE_OWNER_SCOPE')
    package = harness.read(harness.inside('evidence/fpga/review-package-2026-11-15.json'))
    manifest_path = harness.inside('evidence/fpga/manifest.json')
    if sha(manifest_path) != package['manifest_sha256']:
        raise ValueError('HARDWARE_ACCEPTED_MANIFEST_DRIFT')
    manifest = harness.read(manifest_path)
    config = harness.read(harness.inside('config/fpga_build.json'))
    if (manifest['status'] != 'PASS' or config['part'] != 'xc7a35tcpg236-1' or
            config['top'] != 'basys3_top' or config['design_scope'] != 'integrated_soc_v03_interrupts' or
            config['clock_period_ns'] != 10.0):
        raise ValueError('HARDWARE_TARGET_CONTRACT')
    # The accepted immutable manifest binds the implemented hardware. New T032
    # workflow files/registry are separately bound, not misrepresented as T043 code.
    names = ['config/fpga_build.json','docs/ARCH_CONTRACT.json','docs/INTERRUPT_CONTRACT.json'] + config['rtl_sources'] + config['constraints'] + config['memory_files']
    for name in names:
        if sha(harness.inside(name)) != manifest['source_sha256'][name]:
            raise ValueError('HARDWARE_IMPLEMENTED_SOURCE_DRIFT ' + name)
    image = harness.inside(package['bitstream'])
    if package['bitstream_sha256'] != IMAGE_SHA or sha(image) != IMAGE_SHA:
        raise ValueError('HARDWARE_APPROVED_IMAGE_DRIFT')
    return image, {n:sha(harness.inside(n)) for n in names + SOURCES + [AUTH,'evidence/fpga/manifest.json']}


def native_ok(record, marker):
    return rtl_checks.successful(record, marker) and not re.search(r'(?im)^\s*CRITICAL WARNING:', record['stdout']+'\n'+record['stderr'])


def artifacts(folder):
    return {rel(p):sha(p) for p in folder.iterdir() if p.is_file()}


def parse_inventory(text):
    targets, devices = [], []
    for line in text.splitlines():
        row = line.split('\t')
        if len(row) == 2 and row[0] == 'target':
            targets.append(row[1])
        elif len(row) == 5 and row[0] == 'device':
            devices.append(dict(zip(('target','name','part','idcode'), row[1:])))
        else:
            raise ValueError('HARDWARE_INVENTORY_SCHEMA')
    if len(set(targets)) != len(targets):
        raise ValueError('HARDWARE_DUPLICATE_TARGET')
    return targets, devices


def select_device(inventory, target, device, com):
    if inventory['status'] != 'PASS' or inventory['targets'] != [target] or len(inventory['devices']) != 1:
        raise ValueError('HARDWARE_AMBIGUOUS_TARGET')
    entry = inventory['devices'][0]
    if entry['target'] != target or entry['name'] != device or entry['part'] != 'xc7a35t':
        raise ValueError('HARDWARE_WRONG_DEVICE')
    if not re.fullmatch(r'COM[1-9][0-9]*', com) or not target.startswith('localhost:3121/'):
        raise ValueError('HARDWARE_LOCAL_TARGET_OR_PORT')
    cable = target.rsplit('/',1)[-1]
    if not re.fullmatch(r'[A-Za-z0-9_-]{6,64}', cable):
        raise ValueError('HARDWARE_CABLE_ID')
    # FT2232 interface A is JTAG, B is UART. Match their observed common USB
    # parent, not an arbitrary truncated serial number or the first COM port.
    parents=[p['InstanceId'].rsplit('\\',1)[-1] for p in inventory['ports']['usb_devices']
             if re.fullmatch(r'USB\\VID_0403&PID_6010\\[A-Za-z0-9_-]+',p['InstanceId'],re.I)]
    parents=[p for p in parents if cable in (p,p+'A')]
    ports = [p for p in inventory['ports']['serial_ports'] if p['DeviceID'] == com]
    if (len(parents)!=1 or len(ports)!=1 or com not in inventory['ports']['port_names'] or
            not re.fullmatch(r'FTDIBUS\\VID_0403\+PID_6010\+' + re.escape(parents[0]) + r'B\\0000', ports[0]['PNPDeviceID'],re.I)):
        raise ValueError('HARDWARE_UART_CABLE_MISMATCH')
    return entry


def bound_receipt(name, mode):
    path = harness.inside(name)
    if path.parent != harness.inside('evidence/hardware'):
        raise ValueError('HARDWARE_RECEIPT_LOCATION')
    record = harness.read(path)
    if record['mode'] != mode or record['status'] != 'PASS':
        raise ValueError('HARDWARE_PRIOR_NOT_PASS')
    for field in ('source_sha256','artifacts'):
        for n,d in record[field].items():
            if sha(harness.inside(n)) != d:
                raise ValueError('HARDWARE_RECEIPT_DRIFT ' + n)
    return record


def guard(job=None, capture_job=None):
    image, current = context()
    path = harness.inside(rel(Path(job or capture_job)))
    folder = path.parent
    if not folder.is_relative_to(harness.inside('build/T032')):
        raise ValueError('HARDWARE_JOB_LOCATION')
    binding = harness.read(folder/'binding.json')
    if binding['source_sha256'] != current or sha(path) != binding['job_sha256']:
        raise ValueError('HARDWARE_JOB_BINDING')
    if capture_job:
        data = harness.read(path)
        program = bound_receipt(data['program'],'program')
        select_device(bound_receipt(program['inventory'],'inventory'),program['target'],program['device'],data['com'])
        if (data['python'] != sys.executable or data['output'] != str(folder) or
                type(data['seconds']) is not int or not 5 <= data['seconds'] <= 60 or data['epoch'] not in (1,2)):
            raise ValueError('HARDWARE_CAPTURE_JOB')
    else:
        rows = [line.split('\t') for line in path.read_text(encoding='utf-8').splitlines()]
        if any(len(r)!=2 for r in rows) or len(dict(rows))!=len(rows):
            raise ValueError('HARDWARE_JOB_SCHEMA')
        data = dict(rows)
        if set(data) != {'mode','output','python','target','device'} or data['output'] != str(folder) or data['python'] != sys.executable:
            raise ValueError('HARDWARE_JOB_FIELDS')
        if data['mode'] == 'program':
            inv = bound_receipt(binding['inventory'],'inventory')
            select_device(inv,data['target'],data['device'],binding['com'])
            if sha(folder/'approved.bit') != IMAGE_SHA:
                raise ValueError('HARDWARE_PROGRAM_COPY_DRIFT')
        elif data['mode'] != 'inventory' or data['target'] or data['device']:
            raise ValueError('HARDWARE_JOB_MODE')
    return image,current


def execute(args):
    image, sources = context()
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = harness.inside('build/T032/'+args.action+'-'+stamp)
    folder.mkdir(parents=True,exist_ok=False)
    receipt = harness.inside('evidence/hardware/'+args.action+'-'+stamp+'.json')
    result = {'mode':args.action,'status':'RUNNING','started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_sha256':sources,'commands':[],'output':rel(folder),'bitstream_sha256':IMAGE_SHA,
        'scope':'Authorized physical device operation; no formal/ASIC claim'}
    harness.atomic(receipt,result)
    try:
        binding = {'source_sha256':sources}
        if args.action == 'capture':
            program=bound_receipt(args.program,'program')
            result.update(program=args.program,epoch=args.epoch,com=program['com'])
            data={'python':sys.executable,'output':str(folder),'com':program['com'],
                'seconds':args.seconds,'program':args.program,'epoch':args.epoch}
            job=folder/'capture.json';harness.atomic(job,data)
            binding['job_sha256']=sha(job);harness.atomic(folder/'binding.json',binding)
            guard(capture_job=str(job))
            command=tool_runner.run([sys.executable,'-B',str(harness.inside('scripts/hardware.py')),'capture-child','--capture-job',str(job)],folder, min(args.seconds+15,120))
            result['commands'].append(command)
            if not native_ok(command,'HARDWARE_UART_CAPTURE_COMPLETE'):
                raise ValueError('HARDWARE_NATIVE_CAPTURE_FAILED')
            raw=(folder/'uart.bin').read_bytes()
            result['raw_uart']=rel(folder/'uart.bin')
            result['status']='PASS' if raw==SUCCESS else 'NOT RUN' if not raw else 'FAIL'
            result['reason']='Exact single physical IRQ PASS boot' if raw==SUCCESS else 'Missing or unexpected physical bytes; retained'
        else:
            target=device=''
            if args.action=='program':
                inv=bound_receipt(args.inventory,'inventory')
                select_device(inv,args.target,args.device,args.com)
                binding.update(inventory=args.inventory,com=args.com)
                result.update(inventory=args.inventory,target=args.target,device=args.device,com=args.com)
                target,device=args.target,args.device
                shutil.copyfile(image,folder/'approved.bit')
            job=folder/'job.tsv'
            fields={'mode':args.action,'output':str(folder),'python':sys.executable,'target':target,'device':device}
            if any('\t' in v or '\n' in v or '\r' in v for v in fields.values()):
                raise ValueError('HARDWARE_JOB_CHARACTER')
            harness.atomic_text(job,''.join(k+'\t'+v+'\n' for k,v in fields.items()))
            binding['job_sha256']=sha(job);harness.atomic(folder/'binding.json',binding)
            guard(job=str(job))
            command=tool_runner.run(tool_runner.vendor_argv('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('scripts/hardware.tcl')),'-tclargs',str(job)]),folder,120)
            result['commands'].append(command)
            if args.action=='inventory':
                # Native read-only cmdlets, no script loading or execution-policy changes.
                query="$ErrorActionPreference='Stop'; $d=@(Get-PnpDevice -PresentOnly | Where-Object {$_.InstanceId.StartsWith('USB\\VID_0403') -or $_.InstanceId.StartsWith('FTDIBUS\\')}); $p=@($d | Where-Object {$_.Status -eq 'OK' -and $_.Class -eq 'Ports' -and $_.FriendlyName -match '\\(COM[1-9][0-9]*\\)'} | ForEach-Object {@{DeviceID=([regex]::Match($_.FriendlyName,'COM[1-9][0-9]*')).Value; Name=$_.FriendlyName; PNPDeviceID=$_.InstanceId}}); @{serial_ports=$p;usb_devices=@($d | Select-Object Status,Class,FriendlyName,InstanceId);port_names=@([System.IO.Ports.SerialPort]::GetPortNames())} | ConvertTo-Json -Depth 5 -Compress"
                ports=tool_runner.run(['powershell.exe','-NoProfile','-Command',query],folder,30)
                result['commands'].append(ports)
                if not native_ok(ports,None):
                    raise ValueError('HARDWARE_PORT_INVENTORY_FAILED')
                result['ports']=json.loads(ports['stdout'])
            if not native_ok(command,'HARDWARE_INVENTORY_COMPLETE') or 'SW Build 6299465' not in command['stdout']:
                raise ValueError('HARDWARE_NATIVE_INVENTORY_FAILED')
            result['targets'],result['devices']=parse_inventory((folder/'inventory.tsv').read_text(encoding='utf-8'))
            if args.action=='program' and not native_ok(command,'HARDWARE_PROGRAM_PASS'):
                raise ValueError('HARDWARE_NATIVE_PROGRAM_FAILED')
            result['status']='PASS' if args.action=='program' or len(result['targets'])==1 and len(result['devices'])==1 else 'NOT RUN'
        if context()[1] != sources:
            raise ValueError('HARDWARE_INPUT_CHANGED_DURING_COMMAND')
    except (ValueError,OSError,KeyError,harness.Stop) as exc:
        result.update(status='FAIL',error=str(exc))
    finally:
        result['artifacts']=artifacts(folder)
        result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
        harness.atomic(receipt,result)
    print(json.dumps({'status':result['status'],'receipt':rel(receipt),'error':result.get('error'),
        'targets':result.get('targets'),'devices':result.get('devices'),'ports':result.get('ports')}))
    return 0 if result['status']=='PASS' else 125 if result['status']=='NOT RUN' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('inventory')
    p=sub.add_parser('program');p.add_argument('--inventory',required=True);p.add_argument('--target',required=True);p.add_argument('--device',required=True);p.add_argument('--com',required=True)
    p=sub.add_parser('capture');p.add_argument('--program',required=True);p.add_argument('--epoch',type=int,choices=(1,2),required=True);p.add_argument('--seconds',type=int,default=45)
    p=sub.add_parser('guard');g=p.add_mutually_exclusive_group(required=True);g.add_argument('--job');g.add_argument('--capture-job')
    p=sub.add_parser('capture-child');p.add_argument('--capture-job',required=True)
    args=parser.parse_args()
    if args.action=='guard':
        guard(args.job,args.capture_job);print('HARDWARE_GUARD_PASS');return 0
    if args.action=='capture-child':
        guard(capture_job=args.capture_job)
        import hardware_serial
        data=harness.read(Path(args.capture_job))
        hardware_serial.capture(data['com'],data['seconds'],Path(data['output']));return 0
    return execute(args)


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,harness.Stop) as exc:
        print('FAIL: '+str(exc),file=sys.stderr);sys.exit(1)
