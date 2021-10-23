"""Test files module"""

from pyfakefs.fake_filesystem_unittest import TestCase
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from typing import List

from util.files import (
    MergeGroup,
    FileGrouper,
    FileModel,
    ImageLayoutModel,
    get_files_with_suffix,
    FileReindexer,
    ScenarioGrouper,
)

TEST_LAYOUT_SINGLE = json.loads(
    """{"layout": [{"camera": "front", "location": {"y": 0, "x": 0, "width": 10, "height": 15}}]}"""
)

ORDERED_FILE_LIST_WITH_ONE_LEADING_ZERO = sorted(
    [
        "a_00",
        "a_01",
        "a_02",
        "a_03",
        "a_04",
        "a_05",
        "a_06",
        "a_07",
        "a_08",
        "a_09",
        "a_010",
    ]
)


class FilesTest(TestCase):
    """Files test"""

    TEST_DIR_CONTENT = [
        "front_right_000047.json",
        "rear_000028.json",
        "rear_right_000012.png",
    ]
    MULTI_NAME_TEST_CONTENT = [
        "front_right_000047.json",
        "rear_000028.json",
        "front_right_000048.json",
        "front_right_000049.json",
        "rear_000029.json",
        "layout.json",
    ]

    def setUp(self) -> None:
        self.setUpPyfakefs()

    def __create_test_files(self, root: Path, files: List[str]):
        self.fs.create_dir(root)
        for file in files:
            self.fs.create_file(root / file)

    def test_get_files_with_suffix__empty_dir__no_files(self):
        result = get_files_with_suffix(Path(""), ".png")
        self.assertFalse(result)

    def test_get_files_with_suffix__not_existing_suffix__no_files(self):
        self.__create_test_files(Path("test"), self.TEST_DIR_CONTENT)
        result = get_files_with_suffix(Path("test"), ".jpg")
        self.assertFalse(result)

    def test_get_files_with_suffix__json_suffix__two_files(self):
        self.__create_test_files(Path("test"), self.TEST_DIR_CONTENT)
        result = get_files_with_suffix(Path("test"), ".json")
        self.assertEqual(2, len(result))
        self.assertEqual(Path("test"), Path(result[0]).parent)

    def test_get_files_with_suffix__input_path__ascending_order(self):
        self.__create_test_files(Path("test"), self.MULTI_NAME_TEST_CONTENT)
        result = get_files_with_suffix(Path("test"), ".json")
        expected = [
            Path("test") / element for element in sorted(self.MULTI_NAME_TEST_CONTENT)
        ]
        self.assertListEqual(expected, result)

    def test_get_files_with_suffix__only_layout_json__one_file(self):
        self.__create_test_files(Path("test"), ["layout.json"])
        result = get_files_with_suffix(Path("test"), ".json")
        self.assertEqual(1, len(result))

    def test_get_files_with_suffix__only_layout_json_but_ignored__no_files(self):
        self.__create_test_files(Path("test"), ["layout.json"])
        result = get_files_with_suffix(Path("test"), ".json", ignore="test/layout.json")
        self.assertFalse(result)


class FileModelTest(unittest.TestCase):
    """Merge Test"""

    def test_file_model__valid_file_path__correct_name(self):
        unit = FileModel("/test/rear_123.json")
        self.assertEqual("rear", unit.topic_name)
        self.assertEqual(123, unit.file_index)
        self.assertEqual(Path("/test/rear_123.json"), unit.file_path)

    def test_file_model__different_separator__correct_name(self):
        unit = FileModel("/test/rear_left-123.json")
        self.assertEqual("rear_left", unit.topic_name)
        self.assertEqual(123, unit.file_index)
        self.assertEqual(Path("/test/rear_left-123.json"), unit.file_path)

    def test_file_model__invalid_name_pattern__exception_raised(self):
        with self.assertRaises(ValueError):
            FileModel("test.json")

    def test_get_file_name_with_sequence_index__index_11__correct_name(self):
        unit = FileModel("/test/rear_123.json")
        self.assertEqual("11_00123.json", unit.get_file_name_with_sequence_index("11"))

    def test_get_file_name_with_sequence_index__target_suffix_different__suffix_changed(
        self,
    ):
        unit = FileModel("/test/rear_123.json")
        self.assertEqual(
            "11_00123.png", unit.get_file_name_with_sequence_index("11", ".png")
        )

    def test_get_file_name_with_view_key__own_view_key__correct_index(self):
        unit = FileModel("/test/rear_123.json")
        self.assertEqual("rear_000123.json", unit.get_file_name_with_view_key())

    def test_get_file_name_with_view_key__different_view_key__key_changed(self):
        unit = FileModel("/test/rear_123.json")
        self.assertEqual("front_000123.json", unit.get_file_name_with_view_key("front"))

    def test_lt__two_file_models__one_less_than_two(self):
        one = FileModel("a_000.png")
        two = FileModel("a_001.png")
        self.assertLess(one, two)


class ImageLayoutModelTest(unittest.TestCase):
    """Image Layout Test"""

    def test_properties__test_layout__correct_coordinates(self):
        unit = ImageLayoutModel(TEST_LAYOUT_SINGLE["layout"][0])

        self.assertEqual((0, 0, 10, 15), unit.box)
        self.assertEqual("front", unit.key)
        self.assertEqual((0, 0), unit.top_left)

    def test_create__equal_to_test_layout(self):
        expected = TEST_LAYOUT_SINGLE["layout"][0]
        unit = ImageLayoutModel.create("front", 0, 0, 10, 15)

        self.assertEqual(expected, unit.image_layout)

    def test_is_inside__inside__true(self):
        unit = ImageLayoutModel(TEST_LAYOUT_SINGLE["layout"][0])
        self.assertTrue(unit.is_inside(5, 5))

    def test_is_inside__not_inside__false(self):
        unit = ImageLayoutModel(TEST_LAYOUT_SINGLE["layout"][0])

        self.assertFalse(unit.is_inside(15, 5))  # y outside
        self.assertFalse(unit.is_inside(5, 25))  # x outside
        self.assertFalse(unit.is_inside(15, 25))  # both outside


class MergeGroupTest(unittest.TestCase):
    """Merge Group Test"""

    def test_constructor__invalid_input__raise(self):
        files_dict = {"front": None, "rear": None}
        with self.assertRaises(AssertionError):
            MergeGroup(TEST_LAYOUT_SINGLE, files_dict)

    def test_constructor__valid_input__no_raise(self):
        files_dict = {"front": None}
        MergeGroup(TEST_LAYOUT_SINGLE, files_dict)
        self.assertTrue(True)

    def test_get_file_by_key__existing_key__correct_file_path(self):
        files_dict = {"front": FileModel("front_00.png")}
        unit = MergeGroup(TEST_LAYOUT_SINGLE, files_dict)
        self.assertEqual("front_00.png", unit.get_file_path_by_key("front").name)


class FileReindexerTest(unittest.TestCase):
    """File Reindexer Test"""

    TEST_KEYS = [
        "front",
        "rear",
    ]
    TEST_FILES_FOR_REINDEXING = [
        "front-00026751.png",
        "front-00026752.png",
        "front-00026753.png",
        "front-00026755.png",
        "rear-00026752.png",
        "rear-00026753.png",
        "rear-00026754.png",
        "rear-00026755.png",
    ]

    def test_group_files_by_index__no_files__empty(self):
        result = FileReindexer.group_files_by_index([])
        self.assertFalse(result)

    def test_group_files_by_index__singe_file_per_index__length_and_values_correct(
        self,
    ):
        result = FileReindexer.group_files_by_index(["front_123.png", "rear_123.png"])
        self.assertEqual(1, len(result.keys()))
        self.assertIn(result[123][0].file_path.name, ["front_123.png", "rear_123.png"])

    def test_group_files_by_index__test_files_for_reindexing__correct(self):
        result = FileReindexer.group_files_by_index(self.TEST_FILES_FOR_REINDEXING)
        self.assertEqual(5, len(result.keys()))
        self.assertEqual(1, len(result[26751]))
        self.assertEqual(2, len(result[26752]))
        self.assertEqual(2, len(result[26753]))
        self.assertEqual(1, len(result[26754]))
        self.assertEqual(2, len(result[26755]))

    def test_group_files_by_index__file_order_with_one_leading_zeros__ordered_by_file_index(
        self,
    ):
        result = list(
            FileReindexer.group_files_by_index(ORDERED_FILE_LIST_WITH_ONE_LEADING_ZERO)
        )
        self.assertTrue(all(result[i] <= result[i + 1] for i in range(len(result) - 1)))

    def test_filter_files_for_reindexing__no_files__empty(self):
        reindex, remove = FileReindexer.filter_files_for_reindexing({}, self.TEST_KEYS)
        self.assertFalse(reindex)
        self.assertFalse(remove)

    def test_filter_files_for_reindexing__single_group_for_reindexing__correct(self):
        test_group = {123: [FileModel("front_123.png"), FileModel("rear_123.png")]}
        reindex, remove = FileReindexer.filter_files_for_reindexing(
            test_group, self.TEST_KEYS
        )

        self.assertEqual(test_group[123], reindex[0])
        self.assertFalse(remove)

    def test_filter_files_for_reindexing__two_groups_for_removing__correct(self):
        test_group = {
            123: [FileModel("front_123.png")],
            124: [FileModel("rear_124.png")],
        }
        reindex, remove = FileReindexer.filter_files_for_reindexing(
            test_group, self.TEST_KEYS
        )

        self.assertFalse(reindex)
        self.assertEqual(test_group[123], remove[0])
        self.assertEqual(test_group[124], remove[1])

    def test_filter_files_for_reindexing__test_files_for_reindexing__3_to_keep_2_to_remove(
        self,
    ):
        test_group = FileReindexer.group_files_by_index(self.TEST_FILES_FOR_REINDEXING)
        reindex, remove = FileReindexer.filter_files_for_reindexing(
            test_group, self.TEST_KEYS
        )

        self.assertEqual(test_group[26751], remove[0])
        self.assertEqual(test_group[26752], reindex[0])
        self.assertEqual(test_group[26753], reindex[1])
        self.assertEqual(test_group[26754], remove[1])
        self.assertEqual(test_group[26755], reindex[2])

    @patch("pathlib.Path.unlink")
    def test_clean_up__no_files_to_remove__no_clean_up(self, mock_method):
        unit = FileReindexer([], self.TEST_KEYS)
        unit.clean_up()
        mock_method.assert_not_called()

    @patch("pathlib.Path.unlink")
    def test_clean_up__test_files_for_reindexing__unlink_called_twice(
        self, mock_method
    ):
        unit = FileReindexer(self.TEST_FILES_FOR_REINDEXING, self.TEST_KEYS)
        unit.clean_up()
        self.assertEqual(2, mock_method.call_count)

    @patch("pathlib.Path.rename")
    def test_clean_up__no_files_to_reindex__no_reindexing(self, mock_method):
        unit = FileReindexer([], self.TEST_KEYS)
        unit.reindex()
        mock_method.assert_not_called()

    @patch("pathlib.Path.rename")
    def test_clean_up__test_files_for_reindexing__rename_called_six_times(
        self, mock_method
    ):
        unit = FileReindexer(self.TEST_FILES_FOR_REINDEXING, self.TEST_KEYS)
        unit.reindex()
        self.assertEqual(6, mock_method.call_count)


class FileGrouperTest(unittest.TestCase):
    """File Grouper Test"""

    TEST_LAYOUT = json.loads(
        """{"layout": [{"camera": "front_left", "location": {"y": 0, "x": 0}}, {"camera": "front",
        "location": {"y": 0, "x": 640}}, {"camera": "front_right", "location": {"y": 0, "x": 1280}}, {"camera":
        "rear_left", "location": {"y": 480, "x": 0}}, {"camera": "rear", "location": {"y": 480, "x": 640}}, {"camera":
        "rear_right", "location": {"y": 480, "x": 1280}}]}"""
    )
    TEST_KEYS = [
        "front_left",
        "front",
        "front_right",
        "rear_left",
        "rear",
        "rear_right",
    ]
    TEST_SINGLE_FILE_PER_KEY = [
        "front_000000.png",
        "front_right_000000.png",
        "rear_left_000000.png",
        "front_left_000000.png",
        "rear_000000.png",
        "rear_right_000000.png",
    ]

    def test_group_files_for_merging__no_files__empty(self):
        unit = FileGrouper(self.TEST_LAYOUT, [], self.TEST_KEYS)
        result = unit.merge_groups
        self.assertFalse(result)

    def test_group_files_for_merging__one_file_per_key__one_merge_item(self):
        unit = FileGrouper(
            self.TEST_LAYOUT, self.TEST_SINGLE_FILE_PER_KEY, self.TEST_KEYS
        )
        result = unit.merge_groups
        self.assertEqual(1, len(result))

    def test_group_files_by_keys__no_keys__empty_dict(self):
        result = FileGrouper.group_files_by_keys([], [])
        self.assertFalse(result)

    def test_group_files_by_keys__test_keys__six_keys_dict(self):
        result = FileGrouper.group_files_by_keys([], self.TEST_KEYS)
        self.assertEqual(set(self.TEST_KEYS), result.keys())
        for val in result.values():
            self.assertFalse(val)

    def test_group_files_by_keys__file_order_with_one_leading_zeros__ordered_by_file_index(
        self,
    ):
        result = FileGrouper.group_files_by_keys(
            ORDERED_FILE_LIST_WITH_ONE_LEADING_ZERO, ["a"]
        )
        self.assertTrue(FileGrouper.is_consecutive(result))

    def test_group_files_by_keys__keys_and_files_not_matching__empty_six_keys_dict(
        self,
    ):
        result = FileGrouper.group_files_by_keys(
            ["test_0.png", "test_1.png"], self.TEST_KEYS
        )
        self.assertEqual(set(self.TEST_KEYS), result.keys())
        for val in result.values():
            self.assertFalse(val)

    def test_group_files_by_keys__test_single_file_per_key__correct(self):
        result = FileGrouper.group_files_by_keys(
            self.TEST_SINGLE_FILE_PER_KEY, self.TEST_KEYS
        )
        for key, val in result.items():
            self.assertEqual(1, len(val))
            self.assertIn(val[0].file_path.name, self.TEST_SINGLE_FILE_PER_KEY)

    def test_group_files_by_keys__gazemap_keys__two_keys_dict(self):
        result = FileGrouper.group_files_by_keys(
            ["10_00000.jpg", "11_00000.jpg"], ["10", "11"]
        )
        self.assertEqual({"10", "11"}, result.keys())
        for key, val in result.items():
            self.assertEqual(1, len(val))

    def test_is_valid__no_files__true(self):
        unit = FileGrouper(self.TEST_LAYOUT, [], self.TEST_KEYS)
        self.assertTrue(unit.is_valid)

    def test_is_valid__same_length__true(self):
        unit = FileGrouper(
            self.TEST_LAYOUT, self.TEST_SINGLE_FILE_PER_KEY, self.TEST_KEYS
        )
        self.assertTrue(unit.is_valid)

    def test_is_valid__different_length__false(self):
        test_files = copy.deepcopy(self.TEST_SINGLE_FILE_PER_KEY)
        test_files.append("front_000001.png")
        unit = FileGrouper(self.TEST_LAYOUT, test_files, self.TEST_KEYS)
        self.assertFalse(unit.is_valid)

    def test_is_valid__consecutive__true(self):
        test_files = ["front_000000.png", "front_000001.png", "front_000002.png"]
        unit = FileGrouper(TEST_LAYOUT_SINGLE, test_files, ["front"])
        self.assertTrue(unit.is_valid)

    def test_is_valid__not_consecutive__false(self):
        test_files = ["front_000000.png", "front_000001.png", "front_000004.png"]
        unit = FileGrouper(TEST_LAYOUT_SINGLE, test_files, ["front"])
        self.assertFalse(unit.is_valid)

    def test_has_same_lengths__all_empty__true(self):
        test_group = FileGrouper.group_files_by_keys([], ["test"])
        self.assertTrue(FileGrouper.has_same_lengths(test_group))

    def test_is_consecutive__all_empty__true(self):
        test_group = FileGrouper.group_files_by_keys([], ["test"])
        self.assertTrue(FileGrouper.is_consecutive(test_group))

    def test_is_consecutive__correct_order__true(self):
        test_group = FileGrouper.group_files_by_keys(
            ["test_00.jpg", "test_01.jpg"], ["test"]
        )
        self.assertTrue(FileGrouper.is_consecutive(test_group))

    def test_is_empty__all_empty__true(self):
        test_group = FileGrouper.group_files_by_keys([], ["test"])
        self.assertTrue(FileGrouper.is_empty(test_group))


class ScenarioGroupTest(unittest.TestCase):
    """Scenario Group Test"""

    def test_constructor__simple__correct_properties(self):
        unit = ScenarioGrouper(1, "test", [], [])

        self.assertEqual(1, unit.scenario_index)
        self.assertEqual("test", unit.scenario_name)

    def test_get_sequence_index_for_topic__existing_topic__correct_index(self):
        unit = ScenarioGrouper(1, "test", ["front", "rear"], [])

        self.assertEqual("10", unit.get_sequence_index_for_topic("front"))
        self.assertEqual("11", unit.get_sequence_index_for_topic("rear"))

    def test_get_sequence_index_for_topic__not_existing_topic__raise_error(self):
        unit = ScenarioGrouper(1, "test", ["front", "rear"], [])

        with self.assertRaises(ValueError):
            unit.get_sequence_index_for_topic("test")

    def test_get_naming_data_for_topic__existing_topic__correct_values(self):
        unit = ScenarioGrouper(1, "test", ["front"], [])

        self.assertEqual(
            {"view": "front", "scenario_name": "test", "scenario_index": 1},
            unit.get_naming_data_for_topic("front"),
        )

    def test_get_naming_data_for_topic__not_existing_topic__raise_error(self):
        unit = ScenarioGrouper(1, "test", ["front"], [])

        with self.assertRaises(ValueError):
            unit.get_naming_data_for_topic("test")

    def test_get_prepared_path_pairs__2_topics_and_2_files__2_correct_path_pairs(self):
        unit = ScenarioGrouper(
            1, "test", ["front", "rear"], ["front_000000.png", "rear_000000.png"]
        )
        result = unit.get_prepared_path_pairs(unit.image_groups, Path("output"))

        self.assertEqual(2, len(result))
        self.assertEqual(Path("front_000000.png"), result[0].source)
        self.assertEqual(Path("output/10_00000.png"), result[0].target)

    def test_get_prepared_path_pairs__2_topics_and_no_files__2_correct_path_pairs(self):
        unit = ScenarioGrouper(1, "test", ["front", "rear"], [])
        result = unit.get_prepared_path_pairs(unit.image_groups, Path("output"))

        self.assertFalse(result)

    def test_get_prepared_path_pairs__output_suffix_jpg__2_correct_path_pairs(self):
        unit = ScenarioGrouper(
            1, "test", ["front", "rear"], ["front_000000.png", "rear_000000.png"]
        )
        result = unit.get_prepared_path_pairs(unit.image_groups, Path("output"), ".jpg")

        self.assertEqual(2, len(result))
        self.assertEqual(".jpg", result[0].target.suffix)
        self.assertEqual(".jpg", result[1].target.suffix)


if __name__ == "__main__":
    unittest.main()
