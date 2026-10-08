import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '基础/starter'))
import student
import runner

class BasicTests(unittest.TestCase):
    def test_prompt_preserves_exact_visible_passages(self):
        for c in runner.cases():
            if c['split'] != 'dev': continue
            _, _, selected, messages = runner.prepare(c['id'], 'R0', 'baseline')
            self.assertEqual(json.loads(messages[1]['content']),
                             {'question': c['question'], 'passages': selected})

    def test_order_and_identifier_variants(self):
        for c in runner.cases():
            if c['split'] != 'dev': continue
            original = copy.deepcopy(c['passages'])
            expected = student.improve(c['question'], original)
            remapped = [dict(p, id=f'NEW-{i}', source=f'renamed/{i}')
                        for i, p in enumerate(reversed(original))]
            actual = student.improve(c['question'], remapped)
            self.assertEqual([p['text'] for p in expected], [p['text'] for p in actual])
            self.assertEqual(original, c['passages'])
            self.assertCountEqual([p['id'] for p in expected], [p['id'] for p in original])

    def test_linked_record_is_not_dropped(self):
        ps = [dict(id='a',source='x',text='测试项目R9于2026-09正式测量批次ZX73有20项。'),
              dict(id='b',source='y',text='ZX73补页：有15项通过。'),
              dict(id='c',source='z',text='测试项目R9于2026-09压力测试80项。')]
        out = student.improve('测试项目R9于2026-09正式测量通过率？', ps)
        self.assertEqual([p['id'] for p in out[:2]], ['a','b'])

    def test_rejects_passage_outside_current_condition(self):
        c, visible, _, _ = runner.prepare('D01','K','baseline')
        hidden = next(p for p in c['passages'] if p not in visible)
        with patch.object(student,'improve',return_value=[hidden]):
            with self.assertRaises(ValueError): runner.prepare('D01','K','improved')

    def test_dry_run_does_not_call_provider(self):
        conf = runner.load_config(ROOT/'基础/config.example.json')
        with tempfile.TemporaryDirectory() as d, patch.object(runner,'call_model') as call:
            r=runner.execute('D01','R0','baseline',conf,dry=True,outdir=d)
            call.assert_not_called()
            saved=json.loads(next(pathlib.Path(d).glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(saved,r)
            self.assertEqual(r['status'],'dry_run')

if __name__=='__main__': unittest.main()
