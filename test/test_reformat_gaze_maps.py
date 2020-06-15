"""Reformat Gaze Maps Test"""

import unittest
from unittest.mock import patch

from pathlib import Path

from bdda.reformat_gaze_maps import (
    get_path_pair_gazemap_groups,
    reformat_gaze_map_sequence,
)
from util.files import FileModel, PathPair


class ReformatTest(unittest.TestCase):
    """Reformat Test"""

    TEST_NAMING = {
        "10": {"view": "front_left", "scenario_name": "test", "scenario_index": 1},
        "11": {"view": "front", "scenario_name": "test", "scenario_index": 1},
        "20": {"view": "front_left", "scenario_name": "blub", "scenario_index": 2},
        "21": {"view": "front", "scenario_name": "blub", "scenario_index": 1},
    }

    def test_get_path_pair_gazemap_groups__empty_groups__empty(self):
        result = get_path_pair_gazemap_groups({}, {}, "")
        self.assertFalse(result)

    def test_get_path_pair_gazemap_groups__single_group_one_file__correct_path_pair(
        self,
    ):
        result = get_path_pair_gazemap_groups(
            {"10": [FileModel("10_00000.jpg")]}, self.TEST_NAMING, ""
        )

        self.assertEqual(1, len(result))
        self.assertEqual(1, len(result["10"]))
        path_pair = result["10"][0]
        self.assertEqual(Path("10_00000.jpg"), path_pair.source)
        self.assertEqual(Path("test/front_left_000000.jpg"), path_pair.target)

    def test_get_path_pair_gazemap_groups__four_groups__correct_groups(self,):
        result = get_path_pair_gazemap_groups(
            {"10": [], "11": [], "20": [], "21": []}, self.TEST_NAMING, ""
        )
        self.assertEqual(4, len(result))

    @patch("shutil.copy")
    @patch.object(Path, "mkdir")
    def test_reformat_gazemap_group__no_pairs__copy_never_called(
        self, mkdir_mock, copy_mock
    ):
        reformat_gaze_map_sequence([])

        copy_mock.assert_not_called()
        mkdir_mock.assert_not_called()

    @patch("shutil.copy")
    @patch.object(Path, "mkdir")
    def test_reformat_gazemap_group__2_pairs__copy_called_twice(
        self, mkdir_mock, copy_mock
    ):
        reformat_gaze_map_sequence([PathPair("", Path()), PathPair("", Path())])

        self.assertEqual(2, copy_mock.call_count)
        mkdir_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
