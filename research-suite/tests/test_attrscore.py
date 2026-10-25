import unittest
from research_suite.attrscore import parse_label,bounded_input

class Tokenizer:
    eos_token_id=1
    def encode(self,text,add_special_tokens=False):return list(range(2,len(text.split())+2))

class AttrScoreTests(unittest.TestCase):
    def test_all_labels_and_failure(self):
        self.assertEqual(parse_label(' Attributable\n'),0)
        self.assertEqual(parse_label('CONTRADICTORY'),1)
        self.assertEqual(parse_label('Extrapolatory'),1)
        self.assertIsNone(parse_label('Attributable or contradictory'))
        self.assertIsNone(parse_label(''))
    def test_claim_preserved_before_evidence_budget(self):
        ids,a=bounded_input(Tokenizer(),'e '*2000,'c '*300)
        self.assertEqual(len(ids),512)
        self.assertTrue(a['claim_truncated']);self.assertTrue(a['evidence_truncated'])
        self.assertEqual(ids[-1],1)
        ids,a=bounded_input(Tokenizer(),'e','c')
        self.assertFalse(a['claim_truncated']);self.assertFalse(a['evidence_truncated'])

if __name__=='__main__':unittest.main()
