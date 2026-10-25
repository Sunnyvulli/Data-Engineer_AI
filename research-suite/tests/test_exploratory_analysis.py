"""Independent metric oracle and leakage checks for the exposed-target analysis."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

SPEC = importlib.util.spec_from_file_location("exploratory", Path(__file__).resolve().parents[1]/"docs/paper/exploratory_analysis.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ExploratoryChecks(unittest.TestCase):
    def test_tied_metrics_against_independent_library(self):
        rng = np.random.default_rng(17)
        for n in [8, 37, 100]:
            for _ in range(30):
                y = rng.integers(0, 2, n)
                y[:2] = [0, 1]
                score = rng.integers(0, 6, n).astype(float)
                np.testing.assert_allclose(mod.metrics(y, score),
                    [average_precision_score(y, score), roc_auc_score(y, score)], atol=1e-14)
        np.testing.assert_allclose(mod.metrics([0,1,0,1], np.ones(4)), [.5,.5])
        self.assertTrue(np.isnan(mod.metrics([0,0], [1,2])).all())

    def test_invalid_macro_draws_not_replaced(self):
        observed = {"x": np.array([0.,0.])}
        samples = {"x": [[None,None]]*5000}
        result = mod.summarize(observed, samples)["x"]
        self.assertEqual(result["invalid_draws"],5000)
        self.assertIsNone(result["ap_ci95"])

    def test_group_fold_and_heldout_label_invariance(self):
        groups = np.repeat(np.array([str(i) for i in range(30)]), 2)
        gen = np.tile(["a", "b"],30)
        length = np.arange(60)+1
        nli = np.linspace(0,1,60)
        y = np.tile([0,1,1,0],15)
        folds = mod.folds_for(groups)
        for g in set(groups): self.assertEqual(len(set(folds[groups==g])),1)
        scores, _ = mod.crossfit(length,nli,gen,y,groups,folds)
        self.assertTrue(all(np.isfinite(v).all() for v in scores.values()))

    def test_resampled_ties_count_duplicate_rows(self):
        value = np.array([1.,1.,3.,10.,20.,20.])
        gen = np.array(["a"]*3+["b"]*3)
        np.testing.assert_allclose(mod.ranks(value,gen), [.5,.5,1.,1/3,5/6,5/6])
        ix=np.array([0,0,2,3,3,5])
        np.testing.assert_allclose(mod.ranks(value[ix],gen[ix]), [.5,.5,1.,.5,.5,1.])


if __name__ == "__main__": unittest.main()
