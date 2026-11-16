import collections,datetime as dt,hashlib,json,subprocess,sys
sys.path.insert(0,'scripts')
import harness,closure_checks,fpga_build,fpga_checks,fpga_reports
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def path(n):return fpga_build.project_path(n)
def rel(p):return p.relative_to(harness.ROOT).as_posix()
plan,state=harness.load();task=next(t for t in plan['tasks'] if t['id']=='T043')
assert state['active'] is None and state['task_states']['T043']=='awaiting_review' and state['attempts']['T043']==1
jname=state['receipts']['T043'];journal=harness.read(path(jname));manifest=harness.read(path('evidence/fpga/manifest.json'))
assert journal['stage']=='finished' and len(journal['commands'])==8
closure_checks.passed_prefix(journal['commands'][:6],task['verification_commands'])
assert [c['argv'] for c in journal['commands'][6:]]==[['git','diff','--check'],['git','diff','--cached','--check']]
assert all(c['status']=='PASS' and c['exit_code']==0 for c in journal['commands'])
assert manifest['status']=='PASS' and manifest['attempt']==1 and manifest['attempt_journal']==jname
assert manifest['base_commit']==journal['git_commit']
prefix=hashlib.sha256(json.dumps(journal['commands'][:5],sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert prefix==manifest['verified_prefix_sha256']
registry=harness.read(path('.harness/checks.json'))
rows=closure_checks.metadata_objects(journal['commands'][2]['stdout'])
assert sorted(r['registered_command_index'] for r in rows)==list(range(28))
rows=sorted(rows,key=lambda r:r['registered_command_index'])
closure_checks.passed_prefix(rows,registry['regress']['commands']);assert len(rows)==28
sources={};artifacts={};receipts={};base_sources={};data_reports={}
def check(n,d,target):
    p=path(n)
    if rel(p) in target:
        assert target[rel(p)]==d,'CONFLICTING_HASH '+n
        return
    assert p.is_file() and sha(p)==d,'HASH_DRIFT '+n
    target[rel(p)]=d
def source(n,d):
    if rel(path(n)) in sources:
        assert sources[rel(path(n))]==d,'SOURCE_RECEIPT_CONFLICT '+n
        return
    check(n,d,sources)
    if not rel(path(n)).startswith('build/'):
        raw=subprocess.check_output(['git','show',journal['git_commit']+':'+rel(path(n))],cwd=str(harness.ROOT))
        assert hashlib.sha256(raw).hexdigest()==d,'BASE_SOURCE_DRIFT '+n
        base_sources[rel(path(n))]=d
def visit(obj):
    if isinstance(obj,list):
        for v in obj:visit(v)
    elif isinstance(obj,dict):
        for n,d in obj.get('source_sha256',{}).items():source(n,d)
        for n,d in obj.get('artifacts',{}).items():check(n,d,artifacts)
        if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):check(obj['path'],obj['sha256'],artifacts)
        for key in ('vector','waveform'):
            if key+'_sha256' in obj:check(obj.get(key+'_path',obj.get(key)),obj[key+'_sha256'],artifacts)
        if isinstance(obj.get('stdout'),str):visit(closure_checks.metadata_objects(obj['stdout']))
        for k,v in obj.items():
            if k!='stdout' and isinstance(v,(dict,list)):visit(v)
            elif isinstance(v,str) and v.replace('\\','/').startswith(('evidence/toolchain_runs/','evidence/coverage/','evidence/isa/')) and v.endswith('.json'):receipt(v)
def receipt(n):
    n=rel(path(n))
    if n in receipts:return
    r=harness.read(path(n));receipts[n]=r
    if n.startswith(('evidence/coverage/','evidence/isa/')) and 'status' not in r:
        assert n in artifacts and artifacts[n]==sha(path(n)),'UNBOUND_DATA_REPORT '+n
        data_reports[n]=artifacts[n]
    else:assert r.get('status')=='PASS','RECEIPT_NOT_PASS '+n
    if 'checks' in r:assert r['checks'] and all(x['status']=='PASS' for x in r['checks']),n
    if 'base_commit' in r:assert r['base_commit']==journal['git_commit'],n
    if 'started_utc' in r:assert r['started_utc']>='20261108T210906188089Z',n
    visit(r)
visit(journal['commands']);visit(manifest)
for owner in manifest['parent_receipts']:check(owner['path'],owner['sha256'],artifacts)
synth=harness.read(path(manifest['parent_receipts'][0]['path']))
impl=harness.read(path(manifest['parent_receipts'][1]['path']))
checkpoint=fpga_checks.validate_chain(synth,['synth'])
fpga_checks.validate_chain(impl,[s for s,_ in fpga_checks.PHYSICAL_STEPS]+['reports'],checkpoint)
output=path(impl['output']);assert fpga_reports.validate_complete(output)==manifest['summary']
base_evidence=subprocess.check_output(['git','show',journal['git_commit']+':evidence/daily/T043.md'])
assert hashlib.sha256(base_evidence).hexdigest()==journal['evidence_sha256']
baseline=harness.read(path('evidence/prepare/T043-baseline-2026-11-07.json'))
protected={n:d for n,d in baseline['source_sha256'].items() if n.startswith(('riscv_edge_soc_codex_kit/','sw/')) or n in ['RV32I_Edge_SoC.xpr','fpga/basys3/basys3.xdc','fpga/basys3/soc_boot.mem','fpga/basys3/irq_boot.mem','docs/ARCH_CONTRACT.json','docs/INTERRUPT_CONTRACT.json','docs/INTERRUPT_SPEC.md']}
for n,d in protected.items():check(n,d,{})
assert state['task_states']['T023']=='skipped' and 'T043' not in state['owner_reviews']
assert manifest['physical_programming']=='NOT RUN' and manifest['asic']=='NOT RUN'
summary={'audit_date_la':harness.today(),'verification_date_la':'2026-11-08','status':'PASS',
 'scope':'Read-only recovery/integrity audit of finished T043 attempt; no rerun or new approval. Task awaiting owner review.',
 'attempt_journal':jname,'attempt_journal_sha256':sha(path(jname)),'base_commit':journal['git_commit'],
 'manifest_sha256':sha(path('evidence/fpga/manifest.json')),'verified_prefix_sha256':prefix,
 'gate_records':8,'regression_commands':len(rows),'linked_evidence_files':len(receipts),
 'tool_receipts':len(receipts)-len(data_reports),'bound_data_reports':len(data_reports),
 'profile_counts':dict(collections.Counter(r.get('profile','report') for r in receipts.values())),
 'source_files_checked':len(sources),'git_base_sources_checked':len(base_sources),'artifacts_checked':len(artifacts),
 'protected_baseline_files':len(protected),'output':rel(output),'bitstream_sha256':sha(output/'design.bit'),
 'summary':manifest['summary'],'receipts_sha256':{n:sha(path(n)) for n in receipts},
 'source_sha256':sources,'artifacts':artifacts,'formal':'T023 skipped / NOT RUN','physical_programming':'NOT RUN','asic':'NOT RUN'}
harness.atomic(path('evidence/fpga/final-audit-2026-11-15.json'),summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ('summary','receipts_sha256','source_sha256','artifacts','profile_counts')},indent=2))
