"""Generate Pseudo Label Test"""
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from annotation import generate_pseudo_label
from util.geometry import Circle


class GeneratePseudoLabelTest(unittest.TestCase):
    """Generate Pseudo Label Test"""

    def test_create_pseudo_labels__no_files__empty(self):
        result = generate_pseudo_label.create_pseudo_labels([], 0, 0, 0, 0, ".png")
        self.assertFalse(result)

    @patch("PIL.Image.open", MagicMock())
    @patch("annotation.generate_pseudo_label.binarize_image")
    @patch("annotation.generate_pseudo_label.get_roi_circles_from_bin_image")
    @patch("annotation.generate_pseudo_label.get_shapes_from_roi_circles")
    def test_create_pseudo_labels__one_file__correct_image_dimensions_and_label_path(
        self, mock_bin, mock_roi, mock_shapes
    ):
        result = generate_pseudo_label.create_pseudo_labels(
            [Path("test.png")], 640, 480, 96, 0.05, ".png"
        )
        path, data = result[0]

        self.assertEqual(1, len(result))
        self.assertEqual(640, data["imageWidth"])
        self.assertEqual(480, data["imageHeight"])
        self.assertEqual("test.json", path)

        mock_bin.assert_called_once()
        mock_roi.assert_called_once()
        mock_shapes.assert_called_once()

    @patch("PIL.Image.open", MagicMock())
    @patch(
        "annotation.generate_pseudo_label.get_roi_circles_from_bin_image",
        MagicMock(
            return_value=[Circle([10.10, 20], [30, 40]), Circle([50, 60], [70, 88.88])]
        ),
    )
    def test_create_pseudo_labels__one_file_with_two_shapes__correct_shapes(self):
        result = generate_pseudo_label.create_pseudo_labels(
            [Path("test.png")], 640, 480, 96, 0.05, ".png"
        )[0][1]

        self.assertEqual(2, len(result["shapes"]))


if __name__ == "__main__":
    unittest.main()
