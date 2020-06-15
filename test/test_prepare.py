"""Prepare Data Test"""

import unittest
from unittest.mock import patch, mock_open, MagicMock

import PIL.Image

from bdda import prepare
from util.files import ScenarioGrouper
from util import config


class PrepareTest(unittest.TestCase):
    """Prepare Data Test"""

    TEST_NAMING = {
        "10": {"scenario_index": 1},
        "11": {"scenario_index": 1},
        "20": {"scenario_index": 2},
        "21": {"scenario_index": 2},
    }
    TEST_GROUP_IMAGES = ScenarioGrouper(
        1, "test", ["front", "rear"], ["front_000000.png", "rear_000000.png"]
    )

    def test_append_naming_data__empty_scenario_groups__empty_naming_list(self):
        result = prepare.append_naming_data([], {})
        self.assertFalse(result)

    def test_append_naming_data__one_2_topics__2_elements(self):
        result = prepare.append_naming_data(
            [ScenarioGrouper(1, "test", ["front", "rear"], [])], {}
        )

        self.assertEqual(2, len(result))
        self.assertEqual({"10", "11"}, result.keys())

    def test_append_naming_data__one_2_topics_and_existing_naming__6_elements(self,):
        result = prepare.append_naming_data(
            [ScenarioGrouper(3, "test", ["front", "rear"], [])], self.TEST_NAMING.copy()
        )

        self.assertEqual(6, len(result))
        self.assertIn("31", result.keys())

    def test_init_naming_data__no_naming__empty_dict(self):
        result = prepare.init_naming_data(None)
        self.assertFalse(result)

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock())
    def test_init_naming_data__with_naming__read_json_called(self, mock_method):
        prepare.init_naming_data("naming.json")
        mock_method.assert_called_once()

    @patch("PIL.Image.open")
    def test_prepare_scenario_group_images__2_topics_and_2_files__open_called_twice(
        self, mock_method
    ):
        prepare.prepare_scenario_group_images(
            self.TEST_GROUP_IMAGES, "output",
        )

        self.assertEqual(2, mock_method.call_count)

    @patch("PIL.Image.open")
    def test_prepare_scenario_group_images__2_topics_and_no_files__never_called(
        self, mock_method
    ):
        prepare.prepare_scenario_group_images(
            ScenarioGrouper(1, "test", ["front", "rear"], []), "output"
        )

        mock_method.assert_not_called()

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock())
    def test_prepare_scenario_group_gazemaps__2_topics_and_image_files_only__open_never_called(
        self, open_mock_method
    ):
        prepare.prepare_scenario_group_gazemaps(
            self.TEST_GROUP_IMAGES, (10, 20), "output_g",
        )

        open_mock_method.assert_not_called()

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.loads", MagicMock())
    @patch.object(PIL.Image.Image, "save")
    def test_prepare_scenario_group_gazemaps__2_topics_and_label_files__open_called_twice(
        self, save_mock_method, open_mock_method
    ):
        prepare.prepare_scenario_group_gazemaps(
            ScenarioGrouper(
                1,
                "test",
                ["front", "rear"],
                [],
                ["front_000000.json", "rear_000000.json"],
            ),
            (10, 20),
            "output_g",
        )

        self.assertEqual(2, open_mock_method.call_count)
        self.assertEqual(2, save_mock_method.call_count)

    def test_prepare_scenario_group_gazemaps__size_is_none__raise_error(self):

        with self.assertRaises(ValueError):
            prepare.prepare_scenario_group_gazemaps(
                ScenarioGrouper(
                    1,
                    "test",
                    ["front", "rear"],
                    [],
                    ["front_000000.json", "rear_000000.json"],
                ),
                None,
                "output_g",
            )

    def test_get_scenario_start_index__empty_naming__start_index_1(self):
        result = prepare.get_scenario_start_index({})
        self.assertEqual(1, result)

    def test_get_scenario_start_index__2_scenarios_in_naming__start_index_3(self):
        result = prepare.get_scenario_start_index(self.TEST_NAMING)
        self.assertEqual(3, result)

    def test_create_gazemap_from_shapes__empty_shapes__all_back_and_correct_size(self):
        result = prepare.create_gazemap_from_shapes([], (10, 20))

        self.assertEqual((10, 20), result.size)
        self.assertEqual(config.GAZEMAP_FORMAT, result.mode)
        self.assertIsNone(result.getbbox())

    def test_create_gazemap_from_shapes__one_shape__not_all_back(self):
        result = prepare.create_gazemap_from_shapes(
            [{"points": [[20, 30], [30, 45.67]]}], (100, 100)
        )

        self.assertIsNotNone(result.getbbox())

    def test_create_gazemap_from_shapes__two_shape__white_pixel_within_objects(self):
        result = prepare.create_gazemap_from_shapes(
            [{"points": [[25, 25], [27, 25]]}, {"points": [[50, 50], [50, 51]]}],
            (60, 60),
        )

        self.assertEqual(255, result.getpixel((26, 26)))
        self.assertEqual(255, result.getpixel((49, 49)))


if __name__ == "__main__":
    unittest.main()
