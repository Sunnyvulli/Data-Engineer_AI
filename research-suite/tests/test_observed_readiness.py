"""Sky coordinates, deterministic sampling and rejection of incompatible inputs."""

import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import pandas as pd
from research_suite.observed_readiness import coordinate, select, admission, run


class ObservedReadinessIntegrity(unittest.TestCase):
    def test_empty_cone_is_not_admitted(self):
        result = admission(["oid", "mjd", "mag"], "ZTF", 0)
        self.assertTrue(
            any("no photometry rows" in reason for reason in result["reasons"])
        )

    def test_cached_wrong_query_is_retained_as_failure_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pd.DataFrame(
                {
                    "ZTFID": ["ZTFa"],
                    "RA": ["01:00:00"],
                    "Dec": ["+02:00:00"],
                    "type": ["SN Ia"],
                }
            ).to_csv(root / "bts-readiness.csv", index=False)
            (root / "bts-first-selected-dr24.csv").write_text("oid,mjd,mag\n")
            (root / "bts-first-selected-dr24-provenance.json").write_text(
                json.dumps({"query_url": "wrong", "sha256": "wrong"})
            )
            with patch(
                "urllib.request.urlopen",
                side_effect=AssertionError("Unexpected network request"),
            ) as request:
                result = run(root, root / "out")
            request.assert_not_called()
            self.assertEqual(
                result["first_object_archive_query"]["status"],
                "access or schema failure",
            )
            self.assertFalse(result["admission"]["model_scores_computed"])

    def test_sexagesimal_coordinates_and_bounds(self):
        self.assertAlmostEqual(coordinate("12:00:00", ra=True), 180)
        self.assertAlmostEqual(coordinate("-00:30:00"), -0.5)
        for bad, is_ra in [
            ("24:00:00", True),
            ("91", False),
            ("nan", False),
            ("12:65:00", True),
        ]:
            with self.assertRaises(ValueError):
                coordinate(bad, ra=is_ra)

    def test_selection_is_order_independent_and_excludes_unclassified(self):
        frame = pd.DataFrame(
            {
                "ZTFID": ["ZTFb", "ZTFa", "ZTFc"],
                "RA": ["01:00:00"] * 3,
                "Dec": ["+02:00:00"] * 3,
                "type": ["SN Ia", "SN II", "-"],
            }
        )
        first, counts = select(frame)
        second, _ = select(frame.iloc[::-1])
        self.assertEqual(first, second)
        self.assertEqual(counts["selected"], 2)
        self.assertNotIn("ZTFc", [r["ztf_id"] for r in first])

    def test_catalog_magnitudes_are_not_silently_admitted(self):
        result = admission(["oid", "mjd", "mag", "magerr", "filtercode"], "ZTF")
        self.assertFalse(result["admitted_for_scoring"])
        self.assertFalse(result["model_scores_computed"])
        self.assertIsNone(result["performance_metrics"])
        self.assertTrue(any("detected_bool" in reason for reason in result["reasons"]))
