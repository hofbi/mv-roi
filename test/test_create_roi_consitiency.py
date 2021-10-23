"""Create ROI Constitency Test"""

from pyfakefs.fake_filesystem_unittest import TestCase
import unittest
from pathlib import Path
import math
from annotation import create_roi_consistency
from shapely.geometry import Point


class CreateROIConsistencyTest(TestCase):
    """Create ROI Consistency Test"""

    SINGLE_CAM_CONFIG = "[main]\nx=1.6\ny=0\nz=1.7\nyaw=0\n"
    MULTI_CAM_CONFIG = "[front]\nx=1.6\n[left]\nx=1.6\n[right]\nx=1.6\n"
    EMPTY_DICT = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [],
        "imagePath": "front_000093.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }
    SINGLE_DICT = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[100, 150], [110, 150]],
            }
        ],
        "imagePath": "front_000093.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }
    MULTI_DICT = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[100, 150], [110, 150]],
            },
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[150, 150], [170, 150]],
            },
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[300, 150], [340, 150]],
            },
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[100, 300], [110, 300]],
            },
        ],
        "imagePath": "front_000093.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }

    FRONT_VIEW = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [
            {
                "label": "undefined",
                "line_color": 0,
                "fill_color": 0,
                "shape_type": "circle",
                "flags": {},
                "points": [[300, 150], [310, 150]],
            }
        ],
        "imagePath": "front_000000.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }

    FRONT_LEFT_VIEW = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [],
        "imagePath": "front_left_000000.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }

    FRONT_RIGHT_VIEW = {
        "version": "4.2.9",
        "flags": {},
        "shapes": [],
        "imagePath": "front_right_000000.png",
        "imageData": None,
        "imageHeight": 480,
        "imageWidth": 640,
    }

    def setUp(self) -> None:
        self.setUpPyfakefs()

    def test_read_camera_config__empty_case__no_camera(self):
        file_name = Path("empty.ini")
        self.fs.create_file(file_name)

        cam_config = create_roi_consistency.read_camera_config(file_name)

        self.assertEqual(0, len(cam_config))

    def test_read_camera_config__simple_case__one_camera(self):
        file_name = Path("single.ini")
        self.fs.create_file(file_name, contents=self.SINGLE_CAM_CONFIG)

        cam_config = create_roi_consistency.read_camera_config(file_name)

        self.assertEqual(1, len(cam_config))
        self.assertDictEqual(
            {"main": {"x": "1.6", "y": "0", "z": "1.7", "yaw": "0"}}, cam_config
        )

    def test_read_camera_config__multi_case__three_cameras(self):
        file_name = Path("multi.ini")
        self.fs.create_file(file_name, contents=self.MULTI_CAM_CONFIG)

        cam_config = create_roi_consistency.read_camera_config(file_name)

        self.assertEqual(3, len(cam_config))
        self.assertEqual({"front", "left", "right"}, cam_config.keys())

    def test_create_circle_list_from_json__empty_case__no_roi(self):
        circle_list = create_roi_consistency.create_circle_list_from_json(
            self.EMPTY_DICT
        )
        self.assertEqual([], circle_list)

    def test_create_circle_list_from_json__simple_case__one_roi(self):
        circle_list = create_roi_consistency.create_circle_list_from_json(
            self.SINGLE_DICT
        )
        self.assertEqual(Point(100, 150), circle_list[0].centroid)

    def test_create_circle_list_from_json__multi_case__four_roi(self):
        circle_list = create_roi_consistency.create_circle_list_from_json(
            self.MULTI_DICT
        )
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

    def test_sync_rois_for_scene__two_camera__one_roi(self):
        json_files = [self.FRONT_VIEW, self.FRONT_LEFT_VIEW]
        camera_orientation_list = [math.radians(0), math.radians(30)]
        roi_view_list = create_roi_consistency.sync_rois_for_scene(
            json_files, camera_orientation_list, 0.7, 90.0
        )
        self.assertEqual(Point(300, 150), roi_view_list[0][0].centroid)
        self.assertAlmostEqual(124.0855101, roi_view_list[1][0].centroid.x)

    def test_sync_rois_for_scene__three_camera__one_roi(self):
        json_files = [self.FRONT_VIEW, self.FRONT_LEFT_VIEW, self.FRONT_RIGHT_VIEW]
        camera_orientation_list = [math.radians(0), math.radians(30), math.radians(-30)]
        roi_view_list = create_roi_consistency.sync_rois_for_scene(
            json_files, camera_orientation_list, 0.7, 90.0
        )
        self.assertEqual(Point(300, 150), roi_view_list[0][0].centroid)
        self.assertAlmostEqual(124.0855101, roi_view_list[1][0].centroid.x)
        self.assertAlmostEqual(464.64468965, roi_view_list[2][0].centroid.x)


if __name__ == "__main__":
    unittest.main()
