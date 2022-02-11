"""Create ROI Constitency Test"""

import math
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

from pyfakefs.fake_filesystem_unittest import TestCase
from shapely.geometry import Point

from annotation import create_roi_consistency


class CreateROIConsistencyTest(TestCase):
    """Create ROI Consistency Test"""

    SINGLE_CAM_CONFIG = "[main]\nx=1.6\ny=0\nz=1.7\nyaw=0\n"
    MULTI_CAM_CONFIG = "[front]\nx=1.6\n[left]\nx=1.6\n[right]\nx=1.6\n"

    @staticmethod
    def create_dict_with_shapes(
        shapes: List, img_path: str = "front_000093.png"
    ) -> Dict:
        return {
            "version": "4.2.9",
            "flags": {},
            "shapes": shapes,
            "imagePath": img_path,
            "imageData": None,
            "imageHeight": 480,
            "imageWidth": 640,
        }

    @staticmethod
    def create_shape(one: Tuple[int, int], two: Tuple[int, int]) -> Dict:
        return {
            "label": "undefined",
            "line_color": 0,
            "fill_color": 0,
            "shape_type": "circle",
            "flags": {},
            "points": [one, two],
        }

    def setUp(self) -> None:
        self.setUpPyfakefs()

    def test_read_camera_config__empty_case__no_camera(self):
        file_name = "empty.ini"
        self.fs.create_file(file_name)

        cam_config = create_roi_consistency.read_camera_config(Path(file_name))

        self.assertEqual(0, len(cam_config))

    def test_read_camera_config__simple_case__one_camera(self):
        file_name = "single.ini"
        self.fs.create_file(file_name, contents=self.SINGLE_CAM_CONFIG)

        cam_config = create_roi_consistency.read_camera_config(Path(file_name))

        self.assertEqual(1, len(cam_config))
        self.assertDictEqual(
            {"main": {"x": "1.6", "y": "0", "z": "1.7", "yaw": "0"}}, cam_config
        )

    def test_read_camera_config__multi_case__three_cameras(self):
        file_name = "multi.ini"
        self.fs.create_file(file_name, contents=self.MULTI_CAM_CONFIG)

        cam_config = create_roi_consistency.read_camera_config(Path(file_name))

        self.assertEqual(3, len(cam_config))
        self.assertEqual({"front", "left", "right"}, cam_config.keys())

    def test_create_circle_list_from_json__empty_case__no_roi(self):
        circle_list = create_roi_consistency.create_circle_list_from_json(
            self.create_dict_with_shapes([])
        )
        self.assertEqual([], circle_list)

    def test_create_circle_list_from_json__simple_case__one_roi(self):
        circle_list = create_roi_consistency.create_circle_list_from_json(
            self.create_dict_with_shapes([self.create_shape((100, 150), (110, 150))])
        )
        self.assertEqual(Point(100, 150), circle_list[0].centroid)

    def test_create_circle_list_from_json__multi_case__four_roi(self):
        multi_dict = self.create_dict_with_shapes(
            [
                self.create_shape((100, 150), (110, 150)),
                self.create_shape((150, 150), (170, 150)),
                self.create_shape((300, 150), (340, 150)),
                self.create_shape((100, 300), (110, 300)),
            ]
        )
        circle_list = create_roi_consistency.create_circle_list_from_json(multi_dict)
        self.assertEqual(Point(100, 150), circle_list[0].centroid)
        self.assertEqual(Point(150, 150), circle_list[1].centroid)
        self.assertEqual(
            Point(300, 150),
            circle_list[2].centroid,
        )
        self.assertEqual(
            Point(100, 300),
            circle_list[3].centroid,
        )

    def test_sync_rois_for_scene__three_camera__one_roi(self):
        front = self.create_dict_with_shapes(
            [self.create_shape((300, 150), (310, 150))]
        )
        left = self.create_dict_with_shapes([], "front_left_000093.png")
        right = self.create_dict_with_shapes([], "front_right_000093.png")
        json_files = [front, left, right]
        camera_orientation_list = [math.radians(0), math.radians(30), math.radians(-30)]
        roi_view_list = create_roi_consistency.sync_rois_for_scene(
            json_files, camera_orientation_list, 0.7, 90.0
        )
        self.assertEqual(Point(300, 150), roi_view_list[0][0].centroid)
        self.assertAlmostEqual(124.0855101, roi_view_list[1][0].centroid.x)
        self.assertAlmostEqual(464.64468965, roi_view_list[2][0].centroid.x)


if __name__ == "__main__":
    unittest.main()
