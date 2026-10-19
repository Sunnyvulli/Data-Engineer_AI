import unittest
from research_suite.observed_alerts import clean, prefix


class AlertIntegrity(unittest.TestCase):
    def row(self, t=10, c=1):
        return dict(oid="obj", mjd=t, magpsf=20, sigmapsf=0.1, fid=1, candid=c)

    def test_inclusive_boundary_sort_future(self):
        rows = [self.row(14, 3), self.row(10, 1), self.row(13, 2)]
        clean_rows, _, _ = clean(rows, "obj")
        self.assertEqual(prefix(clean_rows, 3)["detections"], 2)
        self.assertEqual(
            prefix(clean_rows, 3), prefix(clean_rows + [self.row(1000, 4)], 3)
        )

    def test_conflicting_candid_rejected(self):
        with self.assertRaises(ValueError):
            clean([self.row(), self.row(11)], "obj")

    def test_invalid_or_wrong_identity(self):
        a = self.row()
        a["oid"] = "other"
        b = self.row()
        b["sigmapsf"] = float("nan")
        rows, counts, _ = clean([a, b], "obj")
        self.assertEqual(rows, [])
        self.assertEqual(sum(counts.values()), 2)
