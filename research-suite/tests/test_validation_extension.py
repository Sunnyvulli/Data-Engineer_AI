import importlib.util
from pathlib import Path
import unittest
import numpy as np
from research_suite.checkpoints import recall_threshold

spec=importlib.util.spec_from_file_location('extension',Path(__file__).resolve().parents[1]/'docs/paper/validation_extension.py')
ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)

class ExtensionTests(unittest.TestCase):
    def test_fast_threshold_matches_empirical_oracle_with_ties(self):
        rng=np.random.default_rng(42)
        for n in [2,9,10,11,19,20,101]:
            for _ in range(10):
                y=rng.integers(0,2,n);y[0]=1
                scores=rng.choice([0.,.1,.8,1.],n)
                self.assertEqual(ext.threshold_fast(y,scores),recall_threshold(y,scores))
        with self.assertRaises(ValueError):ext.threshold_fast([0,0],[.2,.3])
    def test_complete_paired_samples_keep_identical_rankings_equal(self):
        y=np.array([0,1,1,0,0,1]);scores=np.array([.1,.3,.8,.5,.6,.6])
        result=ext.paired_bootstrap(y,{'a':scores,'b':scores},['a','a','b','b','c','c'],{'same':('a','b')},100)
        self.assertEqual(result['valid'],100)
        self.assertEqual(result['paired_ap_difference_95']['same'],[0.,0.])
