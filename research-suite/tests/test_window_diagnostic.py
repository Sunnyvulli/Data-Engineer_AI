import unittest
import numpy as np
from research_suite.window_diagnostic import aggregate

class WindowTests(unittest.TestCase):
    def test_axes_and_aggregation_have_known_results(self):
        scores=aggregate([[.9,.2],[.1,.8]])
        self.assertAlmostEqual(scores['e_first_c_first'],.1)
        self.assertAlmostEqual(scores['e_first_c_all_max'],.9)
        self.assertAlmostEqual(scores['e_first_c_all_mean'],.5)
        self.assertAlmostEqual(scores['e_all_c_all_max'],.2)
        self.assertAlmostEqual(scores['e_all_c_all_mean'],.15)
    def test_single_windows_coincide(self):
        self.assertTrue(all(np.isclose(v,.3) for v in aggregate([[.7]]).values()))
    def test_invalid_matrix_rejected(self):
        for x in [[],[.4,.2],[[float('nan')]],[[1.2]],[[-.1]]]:
            with self.assertRaises(ValueError):aggregate(x)
