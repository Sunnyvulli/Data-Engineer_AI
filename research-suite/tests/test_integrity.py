"""Tests focus on leakage, label semantics, cutoff integrity, and policy behavior."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from research_suite.common import binary_metrics, split_groups, threshold_at_fpr
from research_suite.checkpoints import features, load as load_alce, recall_threshold, triage
from research_suite.phishing import load as load_phishing, corrupt
from research_suite.transients import early_features, budget_metrics


class IntegrityTests(unittest.TestCase):
    def test_group_disjointness_and_coverage(self):
        groups = np.repeat(np.arange(60), 3)
        y = np.repeat(np.arange(60) % 2, 3)
        splits = split_groups(y, groups)
        self.assertEqual(set(np.concatenate(splits)), set(range(len(y))))
        self.assertEqual(sum(map(len, splits)), len(y))
        for a, b in [(0, 1), (0, 2), (1, 2)]:
            self.assertFalse(set(groups[splits[a]]) & set(groups[splits[b]]))

    def test_tied_threshold_meets_validation_budget(self):
        y = np.array([0, 0, 0, 1, 1])
        p = np.array([.1, .8, .8, .8, .9])
        threshold = threshold_at_fpr(y, p, 0)
        self.assertEqual(np.sum(p[y == 0] >= threshold), 0)
        self.assertGreaterEqual(threshold, .8)

    def test_all_equal_scores_can_abstain(self):
        threshold = threshold_at_fpr([0, 1], [.5, .5], 0)
        self.assertGreater(threshold, .5)

    def test_invalid_metrics_rejected(self):
        for y, p in [([0, 1], [0, np.nan]), ([0, 0], [.1, .2]), ([0, 1], [-.1, .2])]:
            with self.assertRaises(ValueError):
                binary_metrics(y, p)

    def test_positive_label_is_phishing(self):
        text = '@relation x\n@attribute a {-1,1}\n@attribute Result {-1,1}\n@data\n1,-1\n-1,1\n1,1\n'
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'data.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('Training Dataset.arff', text)
            X, y, g = load_phishing(path)
            self.assertEqual(y.tolist(), [1, 0, 0])
            self.assertEqual(g[0], g[2])  # contradictory labels still share one group
            self.assertNotIn('Result', X)

    def test_corruption_does_not_mutate_source(self):
        frame = pd.DataFrame(np.ones((10, 4)))
        before = frame.copy()
        corrupt(frame, 'random_20pct', 42)
        pd.testing.assert_frame_equal(frame, before)

    def test_citation_numbers_ignore_reference_markers(self):
        f = features({'text': 'The instrument has 12 sensors [9].', 'citations': [{'text': 'The instrument has 12 sensors.'}]})
        self.assertEqual(f[4], 0)

    def test_missing_citations_flagged(self):
        self.assertTrue(triage({'text': 'A claim.', 'citations': []})['review_required'])

    def test_annotation_fields_cannot_leak_into_features(self):
        s = {'text': 'Earth has one moon [1].', 'citations': [{'text': 'Earth has one moon.'}]}
        f = features(s)
        s.update(sentence_recall_score=0, automatic_recall_scores=[0])
        s['citations'][0]['citation_precision_score'] = 0
        np.testing.assert_array_equal(features(s), f)

    def test_alce_question_grouping_across_models(self):
        s = {'text': 'A claim', 'citations': [], 'sentence_recall_score': 0}
        x = {'asqa': {'m1': {'q1': {'sentences': [s]}}, 'm2': {'q1': {'sentences': [s]}}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'a.json';p.write_text(json.dumps(x))
            _, y, groups, _ = load_alce(p)
            self.assertEqual(groups[0], groups[1]);self.assertEqual(y.tolist(), [1, 1])

    def test_recall_threshold_uses_positive_class(self):
        y = np.array([0, 1, 1, 1])
        p = np.array([.9, .1, .5, .8])
        t = recall_threshold(y, p, 1.)
        self.assertEqual(t, .1)

    def test_artifact_loading_requires_explicit_trust(self):
        from research_suite.inference import predict
        with self.assertRaisesRegex(ValueError, 'trust'):
            predict('nonexistent.joblib', 'x.csv', 'y.csv')

    def test_lexical_overlap_does_not_establish_truth(self):
        sentence = {'text': 'The system is not safe [1].',
                    'citations': [{'text': 'The system is safe.'}]}
        result = triage(sentence)
        self.assertIn('contradictions', result['warning'])
        # This test documents a limitation, not an assertion that triage solves negation.
        self.assertGreaterEqual(result['risk'], 0.)

    def observations(self):
        return pd.DataFrame({'object_id': [1]*4, 'mjd': [9., 10., 11., 20.], 'passband': [0]*4,
                             'flux': [1., 2., 3., 9.], 'flux_err': [1.]*4, 'detected_bool': [0, 1, 1, 1]})

    def test_future_flux_cannot_change_early_features(self):
        obs = self.observations()
        before = early_features(obs, 1)
        obs.loc[obs.mjd > 11, 'flux'] = 1e10
        pd.testing.assert_frame_equal(before, early_features(obs, 1))

    def test_future_observation_count_cannot_change_features(self):
        obs = self.observations()
        pd.testing.assert_frame_equal(early_features(obs, 1), early_features(obs.iloc[:3], 1))

    def test_cutoff_inclusive_and_prealert_excluded(self):
        f = early_features(self.observations(), 1)
        self.assertEqual(f.loc[1, 'n_observations'], 2)
        self.assertEqual(f.loc[1, 'b0_min'], 2.)
        self.assertEqual(f.loc[1, 'b0_max'], 3.)

    def test_simulation_truth_columns_ignored(self):
        obs = self.observations()
        f = early_features(obs, 1)
        obs['true_peakmjd'] = 123.;obs['target'] = 64
        pd.testing.assert_frame_equal(f, early_features(obs, 1))

    def test_no_detection_not_assigned_a_fake_alert(self):
        obs = self.observations();obs['detected_bool'] = 0
        with self.assertRaises(ValueError):early_features(obs, 1)

    def test_invalid_uncertainty_rejected(self):
        obs = self.observations();obs.loc[0, 'flux_err'] = 0
        with self.assertRaises(ValueError):early_features(obs, 1)

    def test_budget_ranking_and_ties_are_deterministic(self):
        result = budget_metrics(np.array([1, 0, 1, 0]), np.array([.9, .8, .7, .1]), .5)
        self.assertEqual(result['selected'], 2)
        self.assertEqual(result['rare_found'], 1)
        self.assertEqual(result['recall_at_budget'], .5)


if __name__ == '__main__':
    unittest.main()
