#!/usr/bin/env python3
"""Replayable stress corpus; reset programs are architecturally idempotent."""
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from dv.coverage.test_coverage import generate as coverage_generate, REQUIRED_BINS as COVERAGE_BINS
from dv.integration.test_core_smoke import i,s
from dv.reference.rv32_iss import RV32ISS

REQUIRED_BINS=COVERAGE_BINS+['reset_windows','load_address_dependencies','illegal_memory_hold']
NEGATIVE_FULL_PROGRAM=True
NEGATIVE_DIAGNOSTIC='STRESS_MISMATCH fault'
SEEDS=(1,314159,20261104,424242)


def program(ident):
    if 51<=ident<=57:
        words=[0x000100b7,i(0x13,2,0,0,5),s(2,1,2,0),i(0x03,3,2,1,0),i(0x13,4,0,3,1),0x100073]
    elif ident==58:
        words=[0x000100b7,i(0x03,10,2,1,4),i(0x13,5,0,1,0),i(0x03,6,2,5,0),
               i(0x03,7,2,1,12),i(0x03,8,2,7,0),0x100073]
    elif ident==59:
        words=[0x000100b7,i(0x03,10,2,1,0),s(2,1,0,4),0xffffffff]
    else:raise ValueError('unknown stress scenario')
    initial=bytearray([0xa5]*128)
    if ident==58:initial[12:16]=(0x10000).to_bytes(4,'little')
    image={4*n+k:byte for n,word in enumerate(words) for k,byte in enumerate(word.to_bytes(4,'little'))}
    image.update({0x10000+n:byte for n,byte in enumerate(initial)})
    return words,initial,image


def generate(seed):
    prefix,old=coverage_generate(seed);coverage=dict(old);rows=[];count=0
    for ident in range(51,60):
        words,initial,image=program(ident);events,fault=RV32ISS(image).run(limit=1000);count+=len(events)
        rows.append((0,fault.pc,fault.insn,fault.code,len(events),ident,0,0,0,0,0,0,fault.tval))
        rows += [(1,4*n,word,*([0]*10)) for n,word in enumerate(words)]
        rows += [(2,0x10000+off,int.from_bytes(initial[off:off+4],'little'),*([0]*10)) for off in range(0,128,4)]
        rows += [(3,*event.fields()[1:]) for event in events]
        rows.append((4,*([0]*12)))
    coverage.update(scenarios=60,expected_retirements=old['expected_retirements']+count,
                    reset_windows=7,load_address_dependencies=1,illegal_memory_hold=1)
    return prefix+''.join(' '.join('%08x'%value for value in row)+'\n' for row in rows),coverage


def reset_witnesses(text,seed):
    pattern=r'^STRESS_RESET seed=(\d+) scenario=(\d+) mode=(\d+) pre_retired=(\d+) i_pending=(\d+) d_pending=(\d+) committed_store=(\d+) fault_seen=(\d+)$'
    rows=[dict(zip(('seed','scenario','mode','pre_retired','i_pending','d_pending','committed_store','fault_seen'),map(int,m)))
          for m in re.findall(pattern,text,re.M)]
    if [r['scenario'] for r in rows]!=list(range(51,58)) or any(r['seed']!=seed or r['mode']!=r['scenario']-50 for r in rows):
        raise ValueError('missing/duplicate/wrong actual reset windows')
    for r in rows:
        mode=r['mode']
        if not 0<=r['pre_retired']<=5:raise ValueError('invalid pre-reset retirement count')
        if mode==2 and r['i_pending']!=1:raise ValueError('vacuous accepted I reset')
        if mode in (4,5) and r['d_pending']!=1:raise ValueError('vacuous accepted D reset')
        if r['committed_store']!=int(mode>=6) or r['fault_seen']!=int(mode==7):
            raise ValueError('wrong retained-store/fault reset boundary')
        if mode==6 and r['pre_retired']!=2:raise ValueError('store already retired before reset')
        if mode==7 and r['pre_retired']!=5:raise ValueError('fault reset before final retirements')
    return rows


def accept_reset_leak(record):
    text=record['stdout']+'\n'+record['stderr']
    return (record['status'] in ('PASS','FAIL') and record['exit_code'] in (0,1)
            and text.count('STRESS_MISMATCH reset memory retention')==1
            and 'STRESS_SIM_PASS' not in text and not re.search(r'(?im)^\s*(ERROR:|WARNING:)',text))


class StressTests(unittest.TestCase):
    def test_prefix_replay_and_seed_variation(self):
        for seed in SEEDS:self.assertTrue(generate(seed)[0].startswith(coverage_generate(seed)[0]))
        self.assertEqual(generate(7),generate(7));self.assertNotEqual(generate(7)[0],generate(20261104)[0])

    def test_reset_program_retained_committed_store_does_not_change_post_reset_trace(self):
        from dv.reference.retire import expected_trace
        for ident in range(51,58):
            _,_,image=program(ident);retained=dict(image)
            retained.update({0x10000+n:byte for n,byte in enumerate((5).to_bytes(4,'little'))})
            self.assertEqual(expected_trace([{'id':ident,'image':image}]),expected_trace([{'id':ident,'image':retained}]))

    def test_literal_reset_and_dependency_program_anchors(self):
        for ident in range(51,58):
            iss=RV32ISS(program(ident)[2]);events,fault=iss.run()
            self.assertEqual((len(events),fault.pc,fault.code),(5,20,9))
            self.assertEqual((iss.regs[2],iss.regs[3],iss.regs[4],iss._word(0x10000)),(5,5,6,5))
        iss=RV32ISS(program(58)[2]);events,fault=iss.run()
        self.assertEqual((len(events),iss.regs[5],iss.regs[7],iss.regs[8]),(6,0x10000,0x10000,0xa5a5a5a5))
        iss=RV32ISS(program(59)[2]);events,fault=iss.run()
        self.assertEqual((len(events),fault.pc,fault.code,iss._word(0x10004)),(3,12,1,0))

    def test_unique_bounded_scenarios_and_positive_generator_bins(self):
        from dv.reference.retire import stimulus_images
        for seed in SEEDS:
            text,bins=generate(seed);cases=stimulus_images(text)
            self.assertEqual([c['id'] for c in cases],list(range(60)))
            self.assertTrue(all(bins[k]>0 for k in REQUIRED_BINS))
            self.assertEqual(sum(len(RV32ISS(c['image']).run()[0]) for c in cases),bins['expected_retirements'])

    def test_reset_witnesses_reject_missing_wrong_seed_and_wrong_commit_boundary(self):
        text='\n'.join('STRESS_RESET seed=7 scenario=%d mode=%d pre_retired=%d i_pending=%d d_pending=%d committed_store=%d fault_seen=%d'%
            (50+m,m,5 if m==7 else 2 if m>=3 else 0,int(m==2),int(m in (4,5)),int(m>=6),int(m==7)) for m in range(1,8))
        self.assertEqual(len(reset_witnesses(text,7)),7)
        for changed,seed in ((text,1),(text+'\n'+text,7),('',7),(text.replace('committed_store=1','committed_store=0'),7)):
            with self.assertRaises(ValueError):reset_witnesses(changed,seed)

    def test_reset_leak_requires_exact_diagnostic_and_real_bounded_execution(self):
        good=dict(stdout='Fatal: STRESS_MISMATCH reset memory retention',stderr='',status='PASS',exit_code=0)
        self.assertTrue(accept_reset_leak(good))
        for row in ({**good,'exit_code':4294967295,'status':'FAIL'}, {**good,'status':'TIMEOUT'},
                    {**good,'stdout':'Fatal: other failure'}, {**good,'stdout':good['stdout']+'\nSTRESS_SIM_PASS'}):
            self.assertFalse(accept_reset_leak(row))

    def test_old_guard_and_monitor_preservation(self):
        root=Path(__file__).resolve().parents[2]
        old=(root/'dv/coverage/tb_coverage.sv').read_text().replace('COVERAGE_','STRESS_')
        new=(root/'dv/random/tb_stress.sv').read_text()
        for line in old.splitlines():
            if 'fail(' in line or '$fatal(' in line:self.assertIn(line.strip(),new)
        self.assertIn('core_properties monitor',new)


if __name__=='__main__':unittest.main(verbosity=2)
