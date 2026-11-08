# Initial package creation helper; final job.tsv is retained byte-for-byte in native-job.zip.
# See audit.json for the subsequent whitespace-check failure and packaging correction.
import datetime as dt,hashlib,json,pathlib,re,sys
sys.path.insert(0,'scripts')
import harness,report

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
folder=harness.inside('build/T043/preauthorization-2026-11-07-92e3363')
r=harness.read(folder/'result.json');c=r['command']
assert r['mode']=='plan' and r['stage']=='all' and r['inputs_unchanged']
assert c['status']=='PASS' and c['exit_code']==0
assert 'FPGA_BUILD_PLAN_PASS' in c['stdout'] and len(re.findall(r'^FPGA_PLANNED_COMMAND=',c['stdout'],re.M))==20
assert not re.search(r'(?im)^\s*(?:WARNING:|ERROR:|FATAL:)',c['stdout']+c['stderr'])
assert not harness.inside(r['output']).exists()
assert all(sha(harness.inside(n))==h for n,h in r['source_sha256'].items())
_,s=harness.load();assert s['active'] is None and s['task_states']['T043']=='pending' and 'T043' not in s['start_approvals']
assert all(s['task_states'][n]=='completed' for n in ['T031','T044','T045'])
collateral=harness.read(harness.inside('config/vivado_vendor_collateral.json'))['checkpoints'];fixtures={}
for p in folder.rglob('*'):
 if p.is_file() and p.suffix.lower() in ('.dcp','.bit'):
  n=p.relative_to(folder).as_posix();assert n in collateral and sha(p)==collateral[n]['sha256'],n
  fixtures[n]=sha(p)
assert fixtures=={n:v['sha256'] for n,v in collateral.items()}
dest=harness.inside('evidence/prepare/T043-preauthorization-2026-11-07');dest.mkdir(exist_ok=False)
for n in ('job.tsv','inputs.json','result.json'):(dest/n).write_bytes((folder/n).read_bytes())
binding={'status':'PASS','scope':'Plan-only input/tool/command validation; no target synthesis or implementation',
 'implementation_commit':'92e3363','checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'files':{n:sha(dest/n) for n in ('job.tsv','inputs.json','result.json')},'source_sha256':r['source_sha256'],
 'target_artifact_directory_absent':True,'vendor_example_checkpoints':fixtures,'planned_commands':20,
 'owner_start_authorization':'PENDING','task_state':'pending','next_required_checks_unregistered':['vivado-synth','vivado-impl','fpga-reports'],
 'no_physical_programming':True,'formal':'T023 owner-skipped / NOT RUN'}
harness.atomic(dest/'audit.json',binding)
tech='''## Shutdown/resume point: T045 committed; T043 plan ready for owner authorization

Local commit 92e3363 contains the approved v0.3 implementation, 213 inspected
files (35,915,282 bytes including retained raw evidence/archives), both reports,
and all current acceptance receipts. All 170 audited source hashes matched the
Git index exactly; git diff --cached --check passed. No unstaged edit remained
at commit. The final audit binds 42 tool receipts, 170 sources, 2063 artifacts,
and 1220 unchanged baseline files. Its helper preparation corrected two metadata
assumptions: the unchanged T026 compiler discovery reference is historical config
provenance, and lint includes register_fixture as well as negative_latch. The
helper before correction is archived; no native check or acceptance changed.

After the clean commit, ran plan-only command (exit0):
python -B scripts/fpga_build.py plan --output build/T043/preauthorization-2026-11-07-92e3363
Actual Vivado returned FPGA_BUILD_PLAN_PASS for20 commands/33 input hashes;
all inputs stayed unchanged, target artifacts directory absent. Five DCPs are
exact previously pinned SDK examples, not synthesized target outputs. Job,
raw result and a separate audit are preserved in
evidence/prepare/T043-preauthorization-2026-11-07/. Review package:
docs/FPGA_EXECUTION_REVIEW.md. No target source/synth/place/route/report/bitstream
command in the plan was executed. No hardware connection/programming occurred.

harness next/status exit0: active null, next null/planning_only true, completed34,
pending10 (including4 optional), skipped1, no failed/blocked/review task. T043 is
the next engineering milestone but start authorization is absent. Its three
required verify entries vivado-synth/vivado-impl/fpga-reports are unregistered;
implement them under active T043 after owner authorization, preserving report
completeness, source bindings and failures. Do not claim this plan passed those
checks. Installed board-catalog warning failures and GPIO CDC-6 history remain.
Keep native120/aggregate600 caps and no diagnostic waivers. Formal remains NOT RUN.

Owner must explicitly authorize T043 execution and the exact command
python -B scripts/harness.py authorize T043 --confirm-owner-review
before the agent may record it. No owner command was called for T043. Once an
explicit response arrives, save its exact evidence, record authorization, run
daily --supervised, inspect clean Git and begin T043. Proceed attended; capture
actual synthesis/implementation/timing/CDC/power/DRC/bitstream evidence and finish
with at most3 attempts. Final T043 human approval is separate. T032 physical
programming is separately gated. Do not rerun T045 or reset its two attempts.
Both Nov7 reports append this handoff; no other dated report was created.
'''
zh='''## 可安全关机的交接点：T045已提交，T043执行方案已准备

中断实现与证据已保存在本地提交92e3363，213个文件经过检查，170个已验证源码哈希
与Git暂存内容逐一吻合。五项最终门禁全部通过；首次失败证据也保留。两份今日日报
已追加结果。最终审计核对42份工具回执、2063个产物及1220个未改动基线文件。

随后运行当前SoC的Vivado仅计划命令，退出0，确认20条计划命令和33个输入哈希。
没有执行综合、布局布线或生成目标bitstream；缓存里的5个DCP是已核验的SDK例子，
不能算本项目的综合结果。完整方案在docs/FPGA_EXECUTION_REVIEW.md，原始结果和
输入清单保存在evidence/prepare/T043-preauthorization-2026-11-07/。

现在没有活动或失败任务，34项完成、1项按您要求跳过。下一项T043需要您的明确执行
授权；其综合、实现和报告验证入口仍需在任务开始后实现。请审阅方案，包括安装板卡
库警告、GPIO CDC-6、形式证明缺失、功耗估计假设及现有超时上限。不会自行放宽检查。
授权后才开始完整SoC的综合、布局布线和报告验收；最终人工评审仍单独保留。

实板烧写属于另一个T032审批。本次没有连接或烧写FPGA，也未下载、改全局设置或安排
无人值守执行。重启后先阅读最新技术交接和工程契约，恢复当前状态即可，不必重做T045。
'''
entry={'technical':tech,'zh-CN':zh};harness.atomic(harness.inside('evidence/report_entries/t043-2026-11-07-plan.json'),entry)
print(report.generate(entry));print(json.dumps(binding))
