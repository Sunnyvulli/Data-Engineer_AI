"""Temporal and fitted-preprocessing controls; no TensorFlow required in CI."""

import unittest
import numpy as np
import pandas as pd
from research_suite.recurrent import prefix, fit_scales, encode


def observations():
    return pd.DataFrame(
        {
            "object_id": [1, 1, 1, 2],
            "mjd": [9.0, 10.0, 10.75, 20.0],
            "passband": [0, 0, 0, 1],
            "flux": [999.0, 0.0, 8.0, 4.0],
            "flux_err": [1.0, 1.0, 1.0, 2.0],
            "detected_bool": [0, 1, 0, 1],
        }
    )


class RecurrentIntegrity(unittest.TestCase):
    def test_future_and_prealert_rows_cannot_change_inputs(self):
        frame = observations()
        base = encode(prefix(frame), np.ones(6))
        extra = pd.DataFrame(
            {
                "object_id": [1, 1],
                "mjd": [13.01, 8.0],
                "passband": [0, 0],
                "flux": [1e9, -1e9],
                "flux_err": [1.0, 1.0],
                "detected_bool": [1, 0],
            }
        )
        changed = encode(
            prefix(pd.concat([frame, extra], ignore_index=True)), np.ones(6)
        )
        np.testing.assert_array_equal(base[0], changed[0])
        np.testing.assert_array_equal(base[1], changed[1])

    def test_grid_does_not_interpolate_from_later_observation(self):
        _, values = encode(prefix(observations()), np.ones(6))
        np.testing.assert_array_equal(values[0, :3, 0], np.zeros(3))
        self.assertGreater(values[0, 3, 0], 0)
        self.assertEqual(values[0, 0, 2], 1)  # observed zero flux
        self.assertEqual(values[0, 0, 5], 0)  # unobserved band

    def test_scaling_uses_only_training_ids_and_allowed_prefix(self):
        frame = observations()
        original = fit_scales(prefix(frame), [1])
        frame.loc[frame.object_id == 2, "flux"] = 1e12
        np.testing.assert_array_equal(original, fit_scales(prefix(frame), [1]))
        self.assertEqual(original[0], 4.0)
        self.assertEqual(original[1], 1.0)

    def test_inclusive_cutoff_and_same_time_inverse_variance(self):
        frame = pd.DataFrame(
            {
                "object_id": [1, 1, 1],
                "mjd": [10.0, 10.0, 13.0],
                "passband": [0, 0, 1],
                "flux": [2.0, 4.0, 6.0],
                "flux_err": [1.0, 1.0, 2.0],
                "detected_bool": [1, 0, 0],
            }
        )
        _, values = encode(prefix(frame), np.ones(6))
        self.assertAlmostEqual(float(values[0, 0, 0]), float(np.arcsinh(3)), places=6)
        self.assertEqual(values[0, -1, 5], 1)
        self.assertEqual(values[0, -2, 5], 0)

    def test_invalid_scale_is_rejected(self):
        with self.assertRaises(ValueError):
            encode(prefix(observations()), [0] * 6)
