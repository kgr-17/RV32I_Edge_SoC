"""Recoverable source-only Vivado integration; no synthesis or programming."""
import argparse
import datetime as dt
import hashlib
import json
import sys
import harness,rtl_checks,fpga_build
from board_checks import validate_xpr


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');parser.add_argument('--task',choices=('T031','T045'),default='T031');args=parser.parse_args()
    config=fpga_build.load_config();xpr=harness.inside('RV32I_Edge_SoC.xpr')
    if not args.apply:
        validate_xpr(xpr.read_text(),config);print('SOC_PROJECT_MANIFEST_PASS');return 0
    c=rtl_checks.Checks('soc-project-integration',task=args.task,scope='Existing project source integration only, no full FPGA build')
    c.result['source_sha256']={n:hashlib.sha256(harness.inside(n).read_bytes()).hexdigest() for n in ['config/fpga_build.json','scripts/project_integration.py','fpga/basys3/integrate.tcl']+config['rtl_sources']+config['memory_files']+config['constraints']}
    before=c.base/'project-before.xpr';before.write_bytes(xpr.read_bytes())
    job=c.base/'sources.tsv';harness.atomic_text(job,''.join(kind+'\t'+name+'\n' for kind,key in [('rtl','rtl_sources'),('mem','memory_files'),('xdc','constraints')] for name in config[key]))
    code=1
    try:
        r=c.vendor('vivado',['-mode','batch','-nolog','-nojournal','-notrace','-source',str(harness.inside('fpga/basys3/integrate.tcl')),'-tclargs',str(job)],c.base/'tool',120)
        (c.base/'project-after-native.xpr').write_bytes(xpr.read_bytes())
        validate_xpr(xpr.read_text(),config);c.result['project_manifest_matches']=True
        # Preserve strict diagnostics, including installed board-catalog warnings.
        c.require(rtl_checks.successful(r,'BOARD_INTEGRATION_PASS'),'Warning-free native source integration',r)
        c.result['status']='PASS';code=0
    except (RuntimeError,ValueError,KeyError,OSError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['artifacts']={p.relative_to(harness.ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in c.base.rglob('*') if p.is_file()}
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save();print(json.dumps(dict(status=c.result['status'],evidence=c.path.relative_to(harness.ROOT).as_posix(),manifest_matches=c.result.get('project_manifest_matches'),error=c.result.get('error'))));return code


if __name__=='__main__':sys.exit(main())
