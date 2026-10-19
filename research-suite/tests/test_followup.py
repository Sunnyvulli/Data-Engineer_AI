import gzip
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from research_suite.followup import cluster_interval, first_complete_objects, host, independent_outcome


class FollowupTests(unittest.TestCase):
    def test_paired_identical_predictions_have_zero_ap_difference(self):
        y = np.array([0, 1, 0, 1, 0, 1])
        p = np.array([.1, .8, .4, .7, .6, .9])
        result = cluster_interval(y, p, np.array([0, 0, 1, 1, 2, 2]), other_scores=p, repetitions=30)
        self.assertEqual(result['paired_ap_difference_percentile_95'], [0., 0.])
        self.assertEqual(result['clusters'], 3)
        self.assertEqual(result['valid_resamples'], 30)

    def test_bootstrap_is_deterministic_and_records_budget_uncertainty(self):
        y = np.array([0, 1]*5);p = np.linspace(0, 1, 10);groups = np.arange(10)
        a = cluster_interval(y, p, groups, repetitions=30, budget=.2)
        b = cluster_interval(y, p, groups, repetitions=30, budget=.2)
        self.assertEqual(a, b)
        self.assertIsNotNone(a['recall_at_budget_percentile_95'])

    def test_hostname_normalization_preserves_parent_distinction(self):
        self.assertEqual(host('https://WWW.Example.invalid./Path?q=X'), 'example.invalid')
        self.assertNotEqual(host('https://a.example.invalid'), host('https://b.example.invalid'))

    def test_malformed_host_is_rejected(self):
        for value in ['', 'https:///path', 'https://[bad']:
            with self.assertRaises(ValueError):host(value)

    def test_object_selection_keeps_all_rows_of_selected_object(self):
        obs = pd.DataFrame({'object_id': [1, 1, 2, 2, 2, 3], 'mjd': range(6)})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'observations.csv.gz';obs.to_csv(p,index=False,compression='gzip')
            selected, note = first_complete_objects(p, 2)
            self.assertEqual(selected.object_id.tolist(), [1,1,2,2,2])
            self.assertEqual(note['selected_complete_objects'], 2)

    def test_no_positive_sample_does_not_fabricate_ap_or_recall(self):
        result = independent_outcome(np.array([0, 0, 0]), np.array([.1, .8, .2]), np.arange(3))
        self.assertIsNone(result['metrics']['average_precision'])
        self.assertIsNone(result['budget']['recall_at_budget'])
        self.assertEqual(result['metrics']['false_positive_rate'], 1/3)

    def test_unsorted_shard_is_rejected(self):
        obs = pd.DataFrame({'object_id': [1, 3, 2], 'mjd': range(3)})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'observations.csv.gz';obs.to_csv(p,index=False,compression='gzip')
            with self.assertRaises(ValueError):first_complete_objects(p, 2)


if __name__ == '__main__':unittest.main()
