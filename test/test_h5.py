"""Test h5 module"""

import unittest
from unittest.mock import MagicMock, patch

import PIL.Image

from util import config
from util.h5 import HDF5Extractor, HDF5Wrapper


class HDF5WrapperTest(unittest.TestCase):
    """HDF5 Wrapper Test"""

    def test_get_or_create_group__not_existing__create_group_called(self):
        mock = MagicMock()
        mock.create_group.return_value = True

        result = HDF5Wrapper.get_or_create_group(mock, "key")

        mock.create_group.assert_called_once_with("key")
        self.assertTrue(result)

    def test_get_or_create_group__existing__create_group_not_called(self):
        mock = MagicMock()

        result = HDF5Wrapper.get_or_create_group({"key": True}, "key")

        mock.create_group.assert_not_called()
        self.assertTrue(result)

    def test_sample_key__index_2__correct_sample_key(self):
        result = HDF5Wrapper.sample_key(2)
        self.assertEqual("sample000002", result)

    def test_index__sample_key_000002__index_2(self):
        result = HDF5Wrapper.index("sample000002")
        self.assertEqual(2, result)


class HDF5extractorTest(unittest.TestCase):
    """HDF5 Extractor Test"""

    def test_get_image_data__empty_sample__image_data_empty(self):
        result = HDF5Extractor.get_image_data({})
        self.assertFalse(result)

    @patch(
        "PIL.Image.fromarray",
        MagicMock(return_value=PIL.Image.new(config.IMAGE_FORMAT, (10, 5))),
    )
    def test_get_image_data__two_keys_in_sample__image_data_size_correct(self):
        result = HDF5Extractor.get_image_data(
            {"front": MagicMock(), "rear": MagicMock()},
        )

        self.assertEqual(2, len(result))
        self.assertEqual((10, 5), result[0].size)

    def test_get_json_data__empty_sample__json_data_empty(self):
        result = HDF5Extractor.get_roi_data({}, 0)
        self.assertFalse(result)

    @patch("json.loads", MagicMock(return_value={"a": 0}))
    def test_get_json_data__two_keys_in_sample__json_data_size_correct(self):
        result = HDF5Extractor.get_roi_data(
            {"front": MagicMock(), "rear": MagicMock()}, 0
        )

        self.assertEqual(2, len(result))
        self.assertEqual(0, result[0][0]["a"])


if __name__ == "__main__":
    unittest.main()
