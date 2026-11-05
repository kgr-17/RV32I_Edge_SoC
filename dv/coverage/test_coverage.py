#!/usr/bin/env python3
"""Independent acceptance tests for incomplete, mislabeled and excluded bins."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from dv.coverage.coverage_report import GROUPS, FEATURES, excluded, parse_bins, summarize
from dv.random.test_random_programs import generate as random_generate, REQUIRED_BINS as RANDOM_BINS, NEGATIVE_FULL_PROGRAM
from dv.integration.test_core_smoke import i,s,j
from dv.reference.rv32_iss import RV32ISS
REQUIRED_BINS=RANDOM_BINS+['directed_jump_mem_hold']
NEGATIVE_DIAGNOSTIC='COVERAGE_MISMATCH fault'


def collision_image():
    # Priming LW fills the fetch queue; older SW then holds a ready JAL in EX.
    words=[0x000100b7,i(0x03,10,2,1,0),s(2,1,0,4),j(7,8),s(2,1,0,8),i(0x13,8,0,7,1),0x100073]
    image={4*n+k:byte for n,word in enumerate(words) for k,byte in enumerate(word.to_bytes(4,'little'))}
    image.update({0x10000+n:0xa5 for n in range(128)})
    return words,image


def generate(seed):
    prefix,old=random_generate(seed);coverage=dict(old)
    words,image=collision_image();events,fault=RV32ISS(image).run(limit=1000)
    if len(events)!=5 or fault.code!=9:raise ValueError('invalid directed jump collision')
    rows=[(0,fault.pc,fault.insn,fault.code,len(events),50,0,0,0,0,0,0,fault.tval)]
    rows += [(1,4*n,word,*([0]*10)) for n,word in enumerate(words)]
    rows += [(2,0x10000+off,0xa5a5a5a5,*([0]*10)) for off in range(0,128,4)]
    rows += [(3,*event.fields()[1:]) for event in events]
    rows.append((4,*([0]*12)))
    coverage.update(scenarios=51,expected_retirements=old['expected_retirements']+len(events),directed_jump_mem_hold=1)
    return prefix+''.join(' '.join('%08x'%v for v in row)+'\n' for row in rows),coverage


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.bins={(g,f):int(excluded(GROUPS[g],FEATURES[f]) is None) for g in range(8) for f in range(8)}
        self.text='\n'.join('COVERAGE_BIN seed=7 group=%d feature=%d hits=%d'%(g,f,h) for (g,f),h in self.bins.items())

    def test_exact_matrix_and_justified_exclusions(self):
        result=summarize(parse_bins(self.text,7),{'op:ADD':1},['op:ADD'])
        self.assertEqual(result['counts'],dict(matrix=64,reachable=49,hit=49,uncovered=0,excluded=15))
        self.assertTrue(all(row['exclusion'] for row in result['excluded_crosses']))

    def test_reachable_uncovered_is_reported_not_erased(self):
        self.bins[1,1]=0
        result=summarize(self.bins,{'op:ADD':1},['op:ADD'])
        self.assertEqual([(r['group'],r['feature']) for r in result['uncovered_crosses']],[('load','ex_forward')])
        self.assertEqual(result['counts']['reachable'],49)

    def test_missing_required_opcode_feature_or_redirect_cross_rejected(self):
        for changed,isa in ((dict(self.bins),{}),({k:(0 if k[1]==1 else h) for k,h in self.bins.items()},{'op:ADD':1}),
                            ({**self.bins,(3,7):0},{'op:ADD':1}),({**self.bins,(7,0):0},{'op:ADD':1})):
            with self.assertRaises(ValueError):summarize(changed,isa,['op:ADD'])

    def test_hits_cannot_be_hidden_under_exclusion(self):
        with self.assertRaises(ValueError):summarize({**self.bins,(5,1):1},{'op:ADD':1},['op:ADD'])

    def test_missing_duplicate_wrong_seed_invalid_and_empty_telemetry_rejected(self):
        for text,seed in ((self.text,1),(self.text+'\n'+self.text,7),('\n'.join(self.text.splitlines()[1:]),7),
                          (self.text.replace('hits=1','hits=x'),7),('',7)):
            with self.assertRaises(ValueError):parse_bins(text,seed)

    def test_instrumented_bench_preserves_assertion_and_existing_guards(self):
        root=Path(__file__).resolve().parents[2]
        old=(root/'dv/assertions/tb_assertions.sv').read_text().replace('ASSERTIONS_','COVERAGE_')
        new=(root/'dv/coverage/tb_coverage.sv').read_text()
        for line in old.splitlines():
            if 'fail(' in line or '$fatal(' in line:self.assertIn(line.strip(),new)
        self.assertIn('core_properties monitor',new)

    def test_all_fifty_original_cases_remain_byte_identical(self):
        for seed in (1,7,101,20261102,314159,271828):
            self.assertTrue(generate(seed)[0].startswith(random_generate(seed)[0]))

    def test_new_collision_has_literal_link_and_wrongpath_memory_anchors(self):
        _,image=collision_image();iss=RV32ISS(image);events,fault=iss.run()
        self.assertEqual([r.pc for r in events],[0,4,8,12,20])
        self.assertEqual((iss.regs[7],iss.regs[8],iss.regs[10]),(16,17,0xa5a5a5a5))
        self.assertEqual((iss._word(0x10004),iss._word(0x10008)),(0,0xa5a5a5a5))
        self.assertEqual((fault.pc,fault.code),(24,9))


if __name__=='__main__':unittest.main(verbosity=2)
