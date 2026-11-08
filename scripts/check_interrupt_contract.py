"""Validate approved target binding and actual 52-port core declaration only."""
import hashlib
import json
import re
import sys
import harness


def main():
    c=harness.read(harness.inside('docs/INTERRUPT_CONTRACT.json'));_,s=harness.load()
    if s['task_states']['T044']!='completed' or 'T044' not in s['owner_reviews']:raise ValueError('Missing recorded T044 owner review')
    for name,key in [('docs/INTERRUPT_SPEC.md','approved_spec_sha256'),('docs/ARCH_CONTRACT.json','legacy_contract_sha256')]:
        if hashlib.sha256(harness.inside(name).read_bytes()).hexdigest()!=c[key]:raise ValueError('Reviewed specification drift: '+name)
    header=harness.inside('rtl/core/pipeline_cpu.sv').read_text(encoding='utf-8').split(');',1)[0]
    ports={}
    for direction,bits,names in re.findall(r'\b(input|output)\s+(?:wire\s+)?logic\s*(\[\d+:\d+\])?\s*([A-Za-z0-9_, ]+)',header):
        width=1
        if bits:
            high,low=map(int,bits.strip('[]').split(':'));width=abs(high-low)+1
        for name in names.strip().strip(',').split(','):
            name=name.strip()
            if name in ports:raise ValueError('Duplicate core port: '+name)
            ports[name]=(direction,width)
    expected={p['name']:(p['direction'],p['width']) for p in c['core_ports']}
    if ports!=expected or len(ports)!=52:raise ValueError('Core interface differs from approved target')
    config=harness.read(harness.inside('config/fpga_build.json'))
    if config['part']!=c['target']['part'] or config['clock_period_ns']!=c['target']['clock_period_ns']:raise ValueError('Target/clock drift')
    for name,value in [('rtl/core/pipeline_cpu.sv',0),('rtl/soc/edge_soc.sv',0),('fpga/basys3/top.sv',1)]:
        if not re.search(r'parameter bit ENABLE_TRAPS\s*=\s*1\x27b'+str(value),harness.inside(name).read_text(encoding='utf-8')):raise ValueError('Feature default drift: '+name)
    print(json.dumps({'status':'PASS','scope':'Reviewed document/interface/configuration binding only','ports':len(ports),'functional_verification':'Separate native interrupt gate required'}));return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,KeyError,OSError,harness.Stop) as exc:print('FAIL: '+str(exc));sys.exit(1)
