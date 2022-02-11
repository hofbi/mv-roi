"""Shapes Test"""

import copy
import unittest

from util import geometry
from util.files import ImageLayoutModel
from util.geometry import Circle


class GeometryTest(unittest.TestCase):
    """Geometry Test"""

    TEST_SHAPES = {
        "shapes": [
            {
                "label": "veh_r",
                "shape_type": "circle",
                "points": [[20, 30], [30, 45.67]],
            }
        ]
    }

    def test_shift_shapes__no_shift__same_as_input(self):
        result = geometry.shift_label_points(copy.deepcopy(self.TEST_SHAPES), 0, 0)
        self.assertEqual(self.TEST_SHAPES, result)

    def test_shift_shapes__shift_by_10_and_20__correct(self):
        result = geometry.shift_label_points(copy.deepcopy(self.TEST_SHAPES), 10, 20)
        self.assertEqual([[30, 50], [40, 65.67]], result["shapes"][0]["points"])

    def test_is_shape_inside__all_inside__true(self):
        result = geometry.is_shape_inside(
            self.TEST_SHAPES["shapes"][0], ImageLayoutModel.create("", 0, 0, 100, 100)
        )
        self.assertTrue(result)

    def test_is_shape_inside__center_inside__true(self):
        result = geometry.is_shape_inside(
            self.TEST_SHAPES["shapes"][0], ImageLayoutModel.create("", 0, 0, 25, 35)
        )
        self.assertTrue(result)

    def test_is_shape_inside__circle_point_inside__false(self):
        result = geometry.is_shape_inside(
            self.TEST_SHAPES["shapes"][0], ImageLayoutModel.create("", 25, 35, 100, 100)
        )
        self.assertFalse(result)

    def test_is_shape_inside__nothing_inside__false(self):
        result = geometry.is_shape_inside(
            self.TEST_SHAPES["shapes"][0], ImageLayoutModel.create("", 0, 0, 5, 5)
        )
        self.assertFalse(result)


class CircleTest(unittest.TestCase):
    """Circle Test"""

    TEST_POINTS = [[20, 30], [30, 45.67]]

    def test_from_json__test_points__correct(self):
        unit = Circle.from_json(self.TEST_POINTS)

        self.assertEqual(20, unit.centroid.x)
        self.assertEqual(30, unit.centroid.y)

    def test_to_json__test_points_coordinates__equal_to_test_points(self):
        unit = Circle((20, 30), (30, 45.67))

        self.assertEqual(self.TEST_POINTS, unit.to_json())

    def test_translate__positive_translation__correct(self):
        unit = Circle((0, 0), (0, 1))
        unit.translate(2, 3)

        self.assertEqual(2, unit.centroid.x)
        self.assertEqual(3, unit.centroid.y)

    def test_scale__upscale__correct(self):
        unit = Circle((2, 3), (3, 3))
        unit.scale(2, 2)

        self.assertEqual(4, unit.centroid.x)
        self.assertEqual(6, unit.centroid.y)

    def test_scale__crash_geometry_must_be_a_point_or_line_string__correct(self):
        unit = Circle((2, 3), (2, 3))
        unit.scale(2, 2)

        self.assertEqual(4, unit.centroid.x)
        self.assertEqual(6, unit.centroid.y)

    def test_scale__downscale__correct(self):
        unit = Circle((2, 3), (3, 3))
        unit.scale(0.5, 0.25)

        self.assertEqual(1, unit.centroid.x)
        self.assertEqual(0.75, unit.centroid.y)

    def test_bounding_box__origin_with_radius_one__correct(self):
        unit = Circle((0, 0), (1, 0))

        self.assertEqual([-1, -1, 1, 1], unit.bounding_box)

    def test_bounding_box__not_origin_with_radius_one__correct(self):
        unit = Circle((1, 1), (2, 1))

        self.assertEqual([0, 0, 2, 2], unit.bounding_box)

    def test_radius__left_radius_point(self):
        unit = Circle((1, 1), (2, 1))

        self.assertEqual(1, unit.radius)

    def test_iou__one_case(self):
        unit = Circle((1, 1), (2, 1))

        self.assertEqual(1, unit.iou(Circle((1, 1), (2, 1))))

    def test_iou__zero_case(self):
        unit = Circle((1, 1), (2, 1))

        self.assertEqual(0, unit.iou(Circle((10, 1), (12, 1))))


if __name__ == "__main__":
    unittest.main()
