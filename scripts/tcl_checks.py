#!/usr/bin/env python3
"""Actual Vivado Tcl plan/guard tests; full-target build stages remain NOT RUN."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import fpga_build
import harness
import rtl_checks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    c=rtl_checks.Checks('tcl',task='T030',scope='Actual Vivado nonproject Tcl plan/input/output/owner-ack guards only; target synth/place/route/bitstream NOT RUN')
    c.result['excluded']=['full-target synthesis','placement/routing','timing/power closure','bitstream generation','FPGA programming','SoC/ASIC signoff']
    code=1
    try:
        manifest=rtl_checks.load_manifest();c.versions(manifest)
        sources=['config/fpga_build.json','config/vivado_vendor_collateral.json','fpga/basys3/build.tcl','scripts/fpga_build.py','scripts/test_fpga_build.py','scripts/tcl_checks.py',
            'scripts/harness.py','scripts/tool_runner.py','scripts/tool_child.py','scripts/rtl_checks.py','.harness/checks.json',
            'docs/ARCH_CONTRACT.json','fpga/basys3/top.sv','fpga/basys3/basys3.xdc']
        c.result['source_sha256']={n:sha(harness.inside(n)) for n in sources};artifacts={}
        folder=c.base/'positive';r=c.command([sys.executable,'-B',str(harness.inside('scripts/fpga_build.py')),'plan','--output',str(folder)],c.base/'launcher',30)
        c.require(rtl_checks.successful(r) and json.loads(r['stdout'])['status']=='PASS','Actual CLI plan launch',r)
        result=harness.read(folder/'result.json');native=result['command'];output=native['stdout']+native['stderr']
        planned=[line.split('=',1)[1] for line in output.splitlines() if line.startswith('FPGA_PLANNED_COMMAND=')]
        expected=['read_verilog','synth_design','read_xdc','report_utilization','report_timing_summary','write_checkpoint',
            'opt_design','place_design','phys_opt_design','route_design','report_utilization','report_timing_summary','report_clocks','report_clock_interaction',
            'report_cdc','check_timing','report_drc','report_power','write_checkpoint','write_bitstream']
        c.require([line.split()[0] for line in planned]==expected and rtl_checks.successful(native,'FPGA_BUILD_PLAN_PASS stage=all top=basys3_top part=xc7a35tcpg236-1 period_ns=10.000 commands=20'),'Actual Tcl validates20 planned commands, executesnone')
        collateral=harness.read(harness.inside('config/vivado_vendor_collateral.json'))
        found={p.relative_to(folder).as_posix():p for p in folder.rglob('*.dcp')}
        sdk=Path(harness.read(harness.inside('.harness/toolchain.json'))['tools']['vivado']).parent.parent/'data'
        def vendor_match(name,record):
            parts=Path(name).parts
            if parts[:3]!=('tool','2025.2','XilinxTclStore') or not name.endswith('.dcp'):return False
            expected=(sdk/Path(*parts[2:])).resolve()
            return Path(record['installed_source']).resolve()==expected and sha(found[name])==record['sha256']==sha(expected)
        c.require(collateral['schema_version']==1 and len(found)==5 and set(found)==set(collateral['checkpoints']) and all(vendor_match(n,record) for n,record in collateral['checkpoints'].items()),'Only five exact installed SDK example checkpoints copied by startup')
        c.result['vendor_collateral']={n:dict(record,observed_sha256=sha(found[n])) for n,record in collateral['checkpoints'].items()}
        c.require(result['inputs_unchanged'] and not (folder/'artifacts').exists() and not list(folder.rglob('*.bit')),'Plan creates no target build artifacts')
        c.result['planned_commands']=planned;c.result['plan_result']=(folder/'result.json').relative_to(harness.ROOT).as_posix()
        original=(folder/'job.tsv').read_text();original_output=(folder/'artifacts').as_posix()
        cases=[('wrong-part','part\txc7a35tcpg236-1','part\txc7a100tcsg324-1','FPGA_TARGET_CONTRACT'),
            ('wrong-clock','period\t10.000','period\t11.000','FPGA_TARGET_CONTRACT'),
            ('missing-source','source\t'+harness.inside('fpga/basys3/top.sv').as_posix(),'source\t'+(c.base/'absent.sv').as_posix(),'FPGA_INPUT_REJECTED'),
            ('outside-source','source\t'+harness.inside('fpga/basys3/top.sv').as_posix(),'source\t'+harness.ROOT.as_posix()+'_escape/never.sv','FPGA_INPUT_REJECTED'),
            ('unknown-mode','mode\tplan','mode\tinvalid','FPGA_MODE_STAGE'),
            ('unauthorized-execution','mode\tplan','mode\texecute','FPGA_OWNER_AUTH_REQUIRED')]
        for label,before,after,diagnostic in cases:
            work=c.base/label;work.mkdir();text=original.replace(original_output,(work/'artifacts').as_posix())
            c.require(text.count(before)==1,'Unique job mutation '+label);text=text.replace(before,after)
            job=work/'job.tsv';harness.atomic_text(job,text)
            r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('fpga/basys3/build.tcl')),'-tclargs',str(job)],work/'tool',15)
            observed=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and 'FPGA_BUILD_FAIL: '+diagnostic in observed and 'FPGA_BUILD_PLAN_PASS' not in observed and 'FPGA_BUILD_EXECUTION_PASS' not in observed,'Actual Tcl rejects '+label,r)
            c.require(not (work/'artifacts').exists(),'No build output from rejected '+label)
        for label,output_path,exists in [('outside-output',harness.inside('docs/T030-rejected-output'),False),('existing-output',c.base/'existing-output'/'artifacts',True)]:
            work=c.base/label;work.mkdir(exist_ok=True)
            if exists:output_path.mkdir();sentinel=output_path/'owner.txt';sentinel.write_bytes(b'keep exactly\n')
            job=work/'job.tsv';harness.atomic_text(job,original.replace(original_output,output_path.as_posix()))
            r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('fpga/basys3/build.tcl')),'-tclargs',str(job)],work/'tool',15)
            observed=r['stdout']+r['stderr']
            c.require(r['status'] in ('PASS','FAIL') and 'FPGA_BUILD_FAIL: FPGA_OUTPUT_REJECTED' in observed and 'FPGA_BUILD_PLAN_PASS' not in observed,'Actual Tcl rejects '+label,r)
            c.require(sentinel.read_bytes()==b'keep exactly\n' if exists else not output_path.exists(),'Rejected output preserves existing work '+label)
        for pattern in ('*.tsv','*.json','*.txt'):
            for p in c.base.rglob(pattern):artifacts[p.relative_to(harness.ROOT).as_posix()]=sha(p)
        c.result['artifacts']=artifacts
        c.require(all(sha(harness.inside(n))==digest for n,digest in c.result['source_sha256'].items()),'Tcl/config/source bindings unchanged')
        c.result['status']='PASS';code=0
    except (rtl_checks.NotRun,FileNotFoundError) as exc:c.result.update(status='NOT RUN',error=str(exc));code=125
    except (RuntimeError,ValueError,KeyError,OSError,AssertionError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'evidence':c.path.relative_to(harness.ROOT).as_posix(),'error':c.result.get('error')}))
    return code


if __name__=='__main__':sys.exit(main())
