import os
import sys,unittest,json,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from roster import FIELD_POS,defense_plan,fielding_rearrangement

class FieldingPlanTests(unittest.TestCase):
    def test_last_bench_catcher_is_not_counted_after_projected_replacement(self):
        with patch('roster.can_play', side_effect=lambda name, pos, cutoff: name.startswith('catcher')), \
             patch('roster.display_name', side_effect=lambda name, cutoff: name):
            status, note, action = defense_plan('C', 'hitter', ['catcher1'], '2026-09-20')
            self.assertEqual((status, action), ('warn', 'replacement'))
            self.assertIn('板凳已無備用捕手', note)
            self.assertNotIn('板凳已無備用捕手',
                             defense_plan('C', 'hitter', ['catcher1', 'catcher2'], '2026-09-20')[1])
            self.assertEqual(defense_plan('C', 'catcher1', ['hitter'], '2026-09-20')[2], 'direct')

    def setUp(self):
        self.positions={p:p for p in FIELD_POS+['DH']}
        self.allowed={(p,p) for p in FIELD_POS}|{('1B','3B'),('New','1B')}
    def test_requires_a_complete_evidence_based_assignment_and_preserves_dh(self):
        with patch('roster.can_play',side_effect=lambda n,p,d:(n,p) in self.allowed) as check:
            plan=fielding_rearrangement(self.positions,'3B','New','2025-09-20')
            self.assertEqual(plan['incoming_position'],'1B');self.assertEqual(plan['retained_dh'],'DH')
            self.assertEqual(plan['moves'],[dict(player='1B',from_position='1B',to_position='3B')])
            self.assertTrue(plan['requires_confirmation'])
            self.assertTrue(all(c.args[2]=='2025-09-20' for c in check.call_args_list))
    def test_no_plan_when_any_slot_unverified_or_dh_would_need_to_field(self):
        for allowed in [self.allowed-{('C','C')},{('DH','3B'),('New','DH')}]:
            with patch('roster.can_play',side_effect=lambda n,p,d:(n,p) in allowed):
                self.assertIsNone(fielding_rearrangement(self.positions,'3B','New','2025-09-20'))
    def test_rejects_incomplete_duplicate_positions_existing_player_and_missing_cutoff(self):
        self.assertIsNone(fielding_rearrangement({'A':'CF'},'A','New','2025-09-20'))
        self.assertIsNone(fielding_rearrangement(self.positions,'3B','1B','2025-09-20'))
        self.assertIsNone(fielding_rearrangement(self.positions,'DH','New','2025-09-20'))
        self.assertIsNone(fielding_rearrangement(self.positions,'3B','New',None))
    def test_published_plans_are_consistent_with_their_replay_files(self):
        """不需原始資料：每個已發布日期的守位計畫都綁定該日索引，且只針對『守備待確認』的候選。"""
        root=Path(__file__).resolve().parents[1]
        base=Path(os.environ.get('BASEBALL_STATIC_OUT',root/'docs/data'))/'replay'
        days=sorted(base.glob('day-*/fielding-plans.json'))
        self.assertTrue(days,'沒有任何已發布的守位計畫檔')
        for plans_file in days:
            day=plans_file.parent
            data=json.loads(plans_file.read_text(encoding='utf8'));index=json.loads((day/'index.json').read_text(encoding='utf8'))
            self.assertEqual(hashlib.sha256((day/'index.json').read_bytes()).hexdigest(),data['replay_index_sha256'],day.name)
            self.assertEqual(data['date'],index['date'],day.name)
            self.assertEqual(len(data['plans']),data['counts']['pas_with_plan'],day.name)
            for pid,choices in data['plans'].items():
                self.assertIn(pid,index['files'],f'{day.name}：{pid} 不在回放索引')
                candidates=json.loads((day/index['files'][pid]).read_text(encoding='utf8'))['ph']['candidates']
                for name in choices:
                    match=[x for x in candidates if x['球員']==name]
                    self.assertEqual(len(match),1,f'{day.name} {pid}：候選 {name}')
                    self.assertEqual(match[0]['守備'],'unknown',f'{day.name} {pid}：{name} 已有明確守備結論，不該有重排計畫')

    def test_exported_plans_reproduce_from_prior_evidence_without_changing_eligibility(self):
        root=Path(__file__).resolve().parents[1]
        from engine import situation
        from runtime_config import settings
        date=settings().history_date
        day=Path(os.environ.get('BASEBALL_STATIC_OUT',root/'docs/data'))/f'replay/day-{date}'
        if not (day/'fielding-plans.json').exists():self.skipTest(f'目前測試設定的 {date} 未提供回放守位匯出檔')
        data=json.loads((day/'fielding-plans.json').read_text(encoding='utf8'));index=json.loads((day/'index.json').read_text(encoding='utf8'))
        self.assertEqual(hashlib.sha256((day/'index.json').read_bytes()).hexdigest(),data['replay_index_sha256'])
        self.assertEqual(len(data['plans']),data['counts']['pas_with_plan']);self.assertGreater(len(data['plans']),0)
        for pid,choices in data['plans'].items():
            s=situation(pid);r=json.loads((day/index['files'][pid]).read_text(encoding='utf8'))['ph']
            for name,p in choices.items():
                self.assertEqual(p,fielding_rearrangement(s['positions'],s['due'],name,date))
                self.assertEqual(next(x for x in r['candidates'] if x['球員']==name)['守備'],'unknown')

if __name__=='__main__':unittest.main()
