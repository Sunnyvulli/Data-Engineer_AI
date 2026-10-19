"""Selection and uncertainty checks without fetching any feed or visiting sites."""

import unittest
from research_suite.feed_probe import select_urls, agreement_interval


class FeedProbeIntegrity(unittest.TestCase):
    def test_overlap_duplicates_and_invalid_schemes(self):
        selected, audit = select_urls(
            [
                "https://www.old.example/a",
                "https://new.example/a",
                " https://new.example/a ",
                "ftp://other.example/a",
                "not-a-url",
                "http://[invalid",
            ],
            {"old.example"},
        )
        self.assertEqual(selected, [("https://new.example/a", "new.example")])
        self.assertEqual(audit["unique_urls"], 5)
        self.assertEqual(audit["source_host_overlap_excluded"], 1)
        self.assertEqual(audit["invalid_excluded"], 3)

    def test_whole_host_bootstrap_is_reproducible(self):
        first = agreement_interval([True, True, False], ["a", "a", "b"])
        self.assertEqual(
            first, agreement_interval([True, True, False], ["a", "a", "b"])
        )
        self.assertEqual(first["clusters"], 2)
        self.assertEqual(first["percentile_95"], [0.0, 1.0])
        self.assertIsNone(agreement_interval([], []))
