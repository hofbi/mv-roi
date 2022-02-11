"""Camera module test"""

import math
import unittest

from shapely.geometry import Point

from util.camera import RegionOverlap, RoiView, RoiViewPair
from util.geometry import Circle


class RegionOverlapTest(unittest.TestCase):
    """Create Region Overlap Test"""

    FIRST_ROI_LIST_EMPTY = {
        "num_label": 0,
        "center_list": [],
    }
    SECOND_ROI_LIST_EMPTY = {
        "num_label": 0,
        "center_list": [],
    }

    def test_is_valid__true_case(self):
        unit = RegionOverlap(
            math.pi / 6,
            math.pi / 3,
            0.5 * math.pi,
        )
        self.assertTrue(unit.is_valid)

    def test_is_valid__false_case(self):
        unit = RegionOverlap(
            math.pi / 6,
            math.pi,
            0.5 * math.pi,
        )
        self.assertFalse(unit.is_valid)

    def test_is_valid__threshold_case(self):
        unit = RegionOverlap(
            math.pi / 6,
            2 * math.pi / 3,
            0.5 * math.pi,
        )
        self.assertFalse(unit.is_valid)

    def test_diff_twoview__positive_case(self):
        unit = RegionOverlap(
            0.2,
            0.1,
            0.5 * math.pi,
        )
        self.assertEqual(0.1, unit.angle_diff_between_both_views)

    def test_diff_twoview__negative_case(self):
        unit = RegionOverlap(
            0.1,
            0.2,
            0.5 * math.pi,
        )
        self.assertEqual(-0.1, unit.angle_diff_between_both_views)


class RoiViewTest(unittest.TestCase):
    """Create Single ROI View Test"""

    def test_is_inside__true_case(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        self.assertTrue(unit.is_inside(Circle([100, 300], [110, 300])))

    def test_is_inside__false_case(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        self.assertFalse(unit.is_inside(Circle([800, 300], [810, 300])))

    def test_exsits__true_case(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        self.assertTrue(unit.exists(Circle([100, 300], [110, 300])))

    def test_exsits__false_case(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        self.assertFalse(unit.exists(Circle([400, 300], [410, 300])))

    def test_translate_rois__empty_case__no_roi(self):
        unit = RoiView([], 30.0, 640, 0.3, 90)
        self.assertEqual([], unit.translate_rois(math.pi / 6))

    def test_translate_rois__single_case__one_roi(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        self.assertAlmostEqual(
            255.5180223, unit.translate_rois(math.pi / 6)[0].centroid.x
        )
        self.assertEqual(300, unit.translate_rois(math.pi / 6)[0].centroid.y)

    def test_translate_rois__multi_case__three_roi(self):
        unit = RoiView(
            [
                Circle([100, 300], [110, 300]),
                Circle([200, 300], [210, 300]),
                Circle([300, 300], [310, 300]),
            ],
            30.0,
            640,
            0.3,
            90,
        )
        self.assertAlmostEqual(
            255.5180223, unit.translate_rois(math.pi / 6)[0].centroid.x
        )
        self.assertEqual(300, unit.translate_rois(math.pi / 6)[0].centroid.y)
        self.assertAlmostEqual(
            315.60249429, unit.translate_rois(math.pi / 6)[1].centroid.x
        )
        self.assertEqual(300, unit.translate_rois(math.pi / 6)[0].centroid.y)
        self.assertAlmostEqual(
            408.86621955, unit.translate_rois(math.pi / 6)[2].centroid.x
        )
        self.assertEqual(300, unit.translate_rois(math.pi / 6)[0].centroid.y)

    def test_insert__fail_case__is_not_inside(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        unit.insert(Circle([800, 300], [810, 300]))
        self.assertEqual(1, len(unit.rois))

    def test_insert__fail_case__exists(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        unit.insert(Circle([100, 300], [110, 300]))
        self.assertEqual(1, len(unit.rois))

    def test_insert__success_case(self):
        unit = RoiView([Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90)
        unit.insert(Circle([200, 300], [210, 300]))
        self.assertEqual(2, len(unit.rois))


class RoiViewPairTest(unittest.TestCase):
    """Create a Pair of ROI View Test"""

    def test_sync_rois_between_views__empty_case__no_roi(self):
        unit_single_left = RoiView([], 30.0, 640, 0.3, 90)
        unit_single_right = RoiView([], 30.0, 640, 0.3, 90)
        unit = RoiViewPair(unit_single_left, unit_single_right)
        unit.sync_rois_between_views()
        self.assertEqual([], unit_single_left.rois)
        self.assertEqual([], unit_single_right.rois)

    def test_sync_rois_between_views__single_case__one_roi(self):
        unit_single_left = RoiView([Circle([500, 300], [510, 300])], 30.0, 640, 0.3, 90)
        unit_single_right = RoiView(
            [Circle([100, 300], [110, 300])], 30.0, 640, 0.3, 90
        )
        unit = RoiViewPair(unit_single_left, unit_single_right)
        unit.sync_rois_between_views()
        self.assertEqual(Point(500, 300), unit_single_left.rois[0].centroid)
        self.assertAlmostEqual(100, unit_single_left.rois[1].centroid.x)
        self.assertEqual(300, unit_single_left.rois[1].centroid.y)
        self.assertEqual(Point(100, 300), unit_single_right.rois[0].centroid)
        self.assertAlmostEqual(499.99999999, unit_single_right.rois[1].centroid.x)
        self.assertEqual(300, unit_single_right.rois[1].centroid.y)


if __name__ == "__main__":
    unittest.main()
