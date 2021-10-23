"""Split Images Test"""

import unittest
from unittest.mock import patch, MagicMock

import json
from pathlib import Path

from annotation import split


class SplitImagesTest(unittest.TestCase):
    """Split Images Test"""

    TEST_LAYOUT = json.loads(
        """{"layout": [
        {"camera": "front_left", "location": {"x": 0, "y": 0, "width": 640, "height": 480}},
        {"camera": "front", "location": {"x": 640, "y": 0, "width": 640, "height": 480}},
        {"camera": "front_right", "location": {"x": 1280, "y": 0, "width": 640, "height": 480}},
        {"camera": "rear_left", "location": {"x": 0, "y": 480, "width": 640, "height": 480}},
        {"camera": "rear", "location": {"x": 640, "y": 480, "width": 640, "height": 480}},
        {"camera": "rear_right", "location": {"x": 1280, "y": 480, "width": 640, "height": 480}}],
        "width": 1920, "height": 960}"""
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

    def test_split_json_data__no_files__empty(self):
        result = split.split_json_data([], {}, ".png")
        self.assertFalse(result)

    @patch("pathlib.Path.read_text", MagicMock())
    @patch("json.loads", MagicMock())
    @patch("annotation.split.crop_from_json", MagicMock())
    def test_split_json_data__two_files_and_test_layout__size_is_12(self):
        result = split.split_json_data(
            [Path("merged_000.json"), Path("merged_001.json")], self.TEST_LAYOUT, ".png"
        )
        self.assertEqual(12, len(result))

    @patch("pathlib.Path.read_text", MagicMock())
    @patch("json.loads", MagicMock())
    @patch("annotation.split.crop_from_json", MagicMock())
    def test_split_json_data__two_files_and_test_layout__correct_file_names(self):
        result = split.split_json_data(
            [Path("merged_000.json"), Path("merged_001.json")], self.TEST_LAYOUT, ".png"
        )
        self.assertIn("front", result[0][0])
        self.assertIn("000", result[0][0])
        self.assertIn("rear", result[-1][0])
        self.assertIn("001", result[-1][0])

    def test_crop_from_json__no_shapes__empty_shapes(self):
        result = split.crop_from_json({"shapes": []}, MagicMock())
        self.assertFalse(result["shapes"])

    def test_crop_from_json__no_shapes_inside__empty_shapes(self):
        layout_model = MagicMock()
        layout_model.is_inside.return_value = False
        result = split.crop_from_json(self.TEST_SHAPES, layout_model)
        self.assertFalse(result["shapes"])

    def test_crop_from_json__two_and_one_inside__size_is_1(self):
        layout_model = MagicMock()
        layout_model.is_inside.side_effect = [True, False]
        result = split.crop_from_json(self.TEST_SHAPES, layout_model)
        self.assertEqual(1, len(result["shapes"]))

    def test_crop_from_json__two_and_two_inside__size_is_2(self):
        layout_model = MagicMock()
        layout_model.is_inside.return_value = True
        result = split.crop_from_json(self.TEST_SHAPES, layout_model)
        self.assertEqual(1, len(result["shapes"]))


if __name__ == "__main__":
    unittest.main()
