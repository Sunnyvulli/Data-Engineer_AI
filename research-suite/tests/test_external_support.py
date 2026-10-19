import unittest
import numpy as np
from research_suite.external_support import window_ranges, target_record, uncertainty


class ExternalSupportIntegrity(unittest.TestCase):
    def test_windows_cover_every_token_and_include_ends(self):
        for length in [0, 1, 120, 121, 384, 385, 1001]:
            spans = window_ranges(length, 120, 100)
            covered = {i for a, b in spans for i in range(a, b)}
            self.assertEqual(covered, set(range(length)))
            self.assertEqual(spans[0][0], 0)
            self.assertEqual(spans[-1][1], length)

    def test_invalid_windows_are_rejected(self):
        for args in [(-1, 120, 100), (10, 0, 1), (10, 120, 121)]:
            with self.assertRaises(ValueError):
                window_ranges(*args)

    def test_human_labels_quality_generator_and_prompt_do_not_enter_inputs(self):
        source = {
            "task_type": "QA",
            "source_info": {"passages": "Evidence", "question": "Question"},
            "prompt": "Secret prompt",
        }
        response = {
            "response": "Complete answer",
            "labels": [],
            "quality": "good",
            "model": "one",
        }
        before = target_record(source, response)
        response.update(
            {
                "labels": [{"text": "unsupported"}],
                "quality": "truncated",
                "model": "two",
            }
        )
        source["prompt"] = "Changed"
        source["source_info"]["question"] = "Changed question"
        self.assertEqual(before, target_record(source, response))
        self.assertEqual(
            before,
            {
                "text": "Complete answer",
                "citations": [{"title": "", "text": "Evidence"}],
            },
        )

    def test_nonqa_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            target_record(
                {"task_type": "Summary", "source_info": "text"}, {"response": "answer"}
            )

    def test_paired_cluster_interval_keeps_same_predictions_paired(self):
        y = np.array([0, 1] * 6)
        p = np.array([0.1, 0.9] * 6)
        g = np.array(["a"] * 6 + ["b"] * 6)
        result = uncertainty(y, p, g, 0.5, other=p, unit="complete test component")
        self.assertEqual(result["unit"], "complete test component")
        self.assertEqual(result["clusters"], 2)
        self.assertEqual(result["valid"], 300)
        self.assertEqual(result["percentile_95"]["paired_ap_difference"], [0.0, 0.0])
