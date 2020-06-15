"""Test merge module"""

import unittest
from unittest.mock import mock_open, patch, MagicMock

import json
import copy

from annotation import merge
from util.files import MergeGroup, FileModel


class MergeImagesTest(unittest.TestCase):
    """Merge frames test"""

    TEST_SUFFIX = ".png"
    TEST_KEYS = [
        "front_left",
        "front",
        "front_right",
        "rear_left",
        "rear",
        "rear_right",
    ]
    TEST_LAYOUT_SINGLE = json.loads(
        """{"width": 10, "height": 5, "layout": [{"camera": "front", "location": {"y": 0, "x": 0}}]}"""
    )
    TEST_LAYOUT = json.loads(
        """{"width": 10, "height": 5, "layout": [{"camera": "front_left", "location": {"y": 0, "x": 0}},
        {"camera": "front", "location": {"y": 0, "x": 640}}, {"camera": "front_right", "location": {"y": 0, "x": 1280}},
        {"camera": "rear_left", "location": {"y": 480, "x": 0}}, {"camera": "rear", "location": {"y": 480, "x": 640}},
        {"camera": "rear_right", "location": {"y": 480, "x": 1280}}]}"""
    )
    TEST_MERGE_GROUP = MergeGroup(
        TEST_LAYOUT, {topic: FileModel("key_000.json") for topic in TEST_KEYS}
    )
    TEST_SHAPES = {
        "shapes": [
            {
                "label": "veh_r",
                "shape_type": "circle",
                "points": [[20, 30], [30, 45.67]],
            }
        ]
    }

    def test_create_layout_data__six_images_two_rows__correct_dimensions(self):
        result = merge.create_layout_data(self.TEST_KEYS, 3, 640, 480)
        self.assertEqual(3 * 640, result["width"])
        self.assertEqual(2 * 480, result["height"])
        self.assertEqual(6, len(result["layout"]))

    def test_create_layout_data__single_image__correct_dimensions(self):
        result = merge.create_layout_data(["front"], 1, 640, 480)
        self.assertEqual(640, result["width"])
        self.assertEqual(480, result["height"])
        self.assertEqual(1, len(result["layout"]))

    def test_create_layout_data__six_images_two_rows__correct_layout(self):
        result = merge.create_layout_data(self.TEST_KEYS, 3, 640, 480)
        for idx, key in enumerate(self.TEST_KEYS):
            self.assertEqual(key, result["layout"][idx]["camera"])

    def test_merge_json__empty_list__empty(self):
        result = merge.merge_json_data([], self.TEST_SUFFIX)
        self.assertFalse(result)

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock())
    def test_merge_json__two_elements__size_2(self, _):
        result = merge.merge_json_data(
            [self.TEST_MERGE_GROUP, self.TEST_MERGE_GROUP], self.TEST_SUFFIX
        )
        self.assertEqual(2, len(result))

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock())
    def test_merge_json__one_element__correct_header(self, _):
        result = merge.merge_json_data([self.TEST_MERGE_GROUP], self.TEST_SUFFIX)[0]

        self.assertEqual(10, int(result["imageWidth"]))
        self.assertEqual(5, int(result["imageHeight"]))
        self.assertEqual("merged_000000.png", result["imagePath"])

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock(return_value=copy.deepcopy(TEST_SHAPES)))
    def test_merge_json__one_element__correct_shape_num(self, _):
        result = merge.merge_json_data([self.TEST_MERGE_GROUP], self.TEST_SUFFIX)[0]
        self.assertEqual(6, len(result["shapes"]))


if __name__ == "__main__":
    unittest.main()
