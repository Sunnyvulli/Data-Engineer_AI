import inspect
import unittest
import numpy as np
from research_suite.data_selection import select_groups


class SelectionIntegrity(unittest.TestCase):
    def test_selector_accepts_no_label_or_target(self):
        self.assertEqual(
            list(inspect.signature(select_groups).parameters),
            ["X", "groups", "count", "seed", "method"],
        )

    def test_deterministic_distinct_complete_question_selection(self):
        X = np.arange(60).reshape(20, 3)
        groups = np.repeat(np.arange(10).astype(str), 2)
        for method in ["random", "diversity"]:
            a = select_groups(X, groups, 4, 42, method)
            np.testing.assert_array_equal(a, select_groups(X, groups, 4, 42, method))
            self.assertEqual(len(set(a)), 4)
            self.assertEqual(np.isin(groups, a).sum(), 8)

    def test_full_selection_contains_all_groups(self):
        X = np.arange(30).reshape(10, 3)
        g = np.arange(10).astype(str)
        for method in ["random", "diversity"]:
            self.assertEqual(set(select_groups(X, g, 10, 17, method)), set(g))
