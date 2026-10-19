import unittest
import numpy as np
from PIL import Image
from research_suite.visual_phishing import components, filename_key, image_features


class VisualIntegrity(unittest.TestCase):
    def test_near_duplicates_merge_transitively(self):
        g = components(
            ["a", "b", "c", "d"], ["a", "b", "c", "d"], [0, 3, 15, 2**32 - 1]
        )
        self.assertEqual(g[0], g[2])
        self.assertNotEqual(g[0], g[3])

    def test_host_and_pixel_merges(self):
        g = components(["a", "a", "b"], ["x", "y", "y"], [0, 2**32 - 1, 2**64 - 1])
        self.assertEqual(len(set(g)), 1)

    def test_descriptor_has_no_file_or_label_inputs(self):
        f, dh, h = image_features(Image.new("RGB", (80, 40), (100, 200, 30)))
        self.assertEqual(f.shape, (179,))
        self.assertTrue(np.isfinite(f).all())
        self.assertEqual(len(h), 64)

    def test_mapping(self):
        self.assertEqual(filename_key("https://a.example/b?c=d"), "a.example_b_c=d")
