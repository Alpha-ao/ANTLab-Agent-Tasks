import json
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'基础/starter'))
from score_exploration import matches
from student_v2 import prepare_messages

class ExplorationTests(unittest.TestCase):
    def test_scoring_does_not_accept_wrong_number_substrings(self):
        self.assertFalse(matches('180%','80%'))
        self.assertFalse(matches('流程丙','流程乙'))
        self.assertFalse(matches('2.6秒但也可能是4秒','2.6'))
        self.assertTrue(matches('3.80秒','3.8'))
        self.assertTrue(matches('-1.3','-1.3'))
        self.assertTrue(matches('乙方案','乙'))
        self.assertFalse(matches('甲方案','乙'))

    def test_labels_cannot_enter_dynamic_message(self):
        ps=[{'id':'unknown','source':'new document','text':'只有17项成功，未记录分母。'}]
        msg=prepare_messages('通过率是多少？',ps)
        data=json.loads(msg[1]['content'])
        self.assertEqual(set(data),{'question','passages'})
        self.assertEqual(data['passages'],ps)
        self.assertNotIn('expected',msg[1]['content'])

if __name__=='__main__':unittest.main()
