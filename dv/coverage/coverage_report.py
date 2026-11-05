"""Finite functional bins from matched execution and actual EX-stage telemetry."""
import re

GROUPS=('alu_upper','load','store','branch','jump','fence','system','illegal_fetch_fault')
FEATURES=('ex_sample','ex_forward','wb_forward','load_blocked','mem_hold',
          'i_offer_stall','d_offer_stall','deferred_redirect')


def excluded(group,feature):
    if feature in ('ex_forward','wb_forward','load_blocked') and group in GROUPS[5:]:
        return 'FENCE/SYSTEM/illegal tokens have no enabled register operands in the reviewed decoder.'
    if feature=='deferred_redirect' and group not in ('branch','jump'):
        return 'Only branch/JAL/JALR generate a legal redirect.'
    return None


def parse_bins(text,seed):
    result={}
    for line in text.splitlines():
        if not line.startswith('COVERAGE_BIN '):continue
        m=re.fullmatch(r'COVERAGE_BIN seed=(\d+) group=(\d+) feature=(\d+) hits=(\d+)',line)
        if not m:raise ValueError('malformed actual coverage bin')
        actual,g,f,h=map(int,m.groups())
        if actual!=seed or not 0<=g<len(GROUPS) or not 0<=f<len(FEATURES) or (g,f) in result:
            raise ValueError('wrong seed/index or duplicate actual coverage bin')
        result[g,f]=h
    if len(result)!=len(GROUPS)*len(FEATURES):raise ValueError('missing actual coverage bins')
    return result


def summarize(bins,isa,required_isa):
    if set(bins)!={(g,f) for g in range(8) for f in range(8)}:
        raise ValueError('incomplete coverage matrix')
    if any(type(h) is not int or h<0 for h in bins.values()):raise ValueError('invalid coverage hit count')
    uncovered_isa=[key for key in required_isa if isa.get(key,0)<=0]
    rows=[]
    for (g,f),hits in sorted(bins.items()):
        group,feature=GROUPS[g],FEATURES[f]; reason=excluded(group,feature)
        if reason and hits:raise ValueError('hit a structurally excluded bin: '+group+'/'+feature)
        rows.append(dict(group=group,feature=feature,hits=hits,reachable=reason is None,exclusion=reason))
    missing=[]
    for g in range(8):
        if bins[g,0]<=0:missing.append(GROUPS[g]+'/ex_sample')
    for f in range(1,8):
        if sum(bins[g,f] for g in range(8))<=0:missing.append('any/'+FEATURES[f])
    for g in (3,4):
        if bins[g,7]<=0:missing.append(GROUPS[g]+'/deferred_redirect')
    if uncovered_isa or missing:raise ValueError('required coverage absent: '+repr(uncovered_isa+missing))
    reachable=[row for row in rows if row['reachable']]
    return {'isa_hits':{key:isa.get(key,0) for key in required_isa},'matrix':rows,
            'uncovered_isa':uncovered_isa,'uncovered_crosses':[row for row in reachable if not row['hits']],
            'excluded_crosses':[row for row in rows if not row['reachable']],
            'counts':{'matrix':len(rows),'reachable':len(reachable),'hit':sum(row['hits']>0 for row in reachable),
                      'uncovered':sum(row['hits']==0 for row in reachable),'excluded':len(rows)-len(reachable)}}
