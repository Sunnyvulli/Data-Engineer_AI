"""No model download in CI; verify leakage and NLI probability semantics."""

import unittest
import numpy as np
from research_suite.entailment import input_pair, unsupported_risk


class EntailmentIntegrity(unittest.TestCase):
    def test_scores_cannot_change_inputs(self):
        sentence = {
            "text": "Claim [12][3].",
            "citations": [
                {"title": "Doc", "text": "Evidence", "citation_precision_score": 0}
            ],
            "sentence_recall_score": 0,
        }
        before = input_pair(sentence)
        sentence["sentence_recall_score"] = 1
        sentence["citations"][0]["citation_precision_score"] = 1
        self.assertEqual(before, input_pair(sentence))
        self.assertEqual(before, ("Doc\nEvidence", "Claim ."))

    def test_entailment_is_middle_class_and_shift_invariant(self):
        logits = np.array([[0, 12, 0], [12, 0, 0], [0, 0, 12]])
        risk = unsupported_risk(logits)
        self.assertLess(risk[0], 0.001)
        self.assertGreater(risk[1], 0.999)
        self.assertGreater(risk[2], 0.999)
        np.testing.assert_allclose(risk, unsupported_risk(logits + 1000))

    def test_reject_invalid_outputs(self):
        for bad in [[[0, float("nan"), 1]], [[1, 2]], [1, 2, 3]]:
            with self.assertRaises(ValueError):
                unsupported_risk(bad)

    def test_no_citation_is_explicitly_empty(self):
        self.assertEqual(input_pair({"text": "Claim", "citations": []}), ("", "Claim"))
