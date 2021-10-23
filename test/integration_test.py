"""Integration Test"""

import unittest
from unittest.mock import MagicMock, patch

from pathlib import Path
import argparse
import shutil
import os
import PIL.ImageChops
import PIL.Image
import h5py

from annotation import (
    merge,
    split,
    generate_pseudo_label,
    h5_extract,
    create_roi_consistency,
)
from bdda import prepare, reformat_gaze_maps
from util.files import get_files_with_suffix, read_json
from util import config

RESOURCE_PATH = Path(__file__).parent.joinpath("resources")
TEST_OUTPUT_PATH = RESOURCE_PATH.joinpath("output")
PATH_INDIVIDUAL = RESOURCE_PATH.joinpath("individual")
IMAGE_TOPICS = [
    "front_left",
    "front",
    "front_right",
    "rear_left",
    "rear",
    "rear_right",
]


def get_return_value_for_merge_patch(
    input_path=PATH_INDIVIDUAL, hdf5_return_value=False, reindex_return_value=False
):
    """
    Create common argparse return values for test patching
    :param input_path:
    :param hdf5_return_value:
    :param reindex_return_value:
    :return:
    """
    return argparse.Namespace(
        input_dir=input_path,
        suffix=".png",
        output_dir=TEST_OUTPUT_PATH,
        res="640x480",
        image_topics=IMAGE_TOPICS,
        images_per_row=3,
        hdf5=hdf5_return_value,
        reindex=reindex_return_value,
    )


class IntegrationTest(unittest.TestCase):
    """Integration Test"""

    PATH_MERGED = RESOURCE_PATH.joinpath("merged")
    PATH_HDF5 = RESOURCE_PATH.joinpath("hdf5")
    PATH_LABEL = RESOURCE_PATH.joinpath("label")
    PATH_HEATMAP = RESOURCE_PATH.joinpath("heatmap")
    PATH_REINDEX = RESOURCE_PATH.joinpath("reindex")
    PATH_REFORMAT = RESOURCE_PATH.joinpath("reformat")
    PATH_PREPARED = RESOURCE_PATH.joinpath("prepared")
    PATH_PREPARED_IMAGES = PATH_PREPARED.joinpath("camera_images")
    PATH_PREPARED_GAZEMAPS = PATH_PREPARED.joinpath("gazemap_images")
    PATH_NAMING = PATH_PREPARED.joinpath(config.MVROI_NAMING_FILE)
    PATH_CAMERA_CONFIG = RESOURCE_PATH.joinpath("camera_config")
    PATH_CONSISTENT_IN = RESOURCE_PATH.joinpath("consistent_in")
    PATH_CONSISTENT = RESOURCE_PATH.joinpath("consistent")

    def setUp(self) -> None:
        self.__message("Set Up")
        self.assertFalse(TEST_OUTPUT_PATH.exists())

    def tearDown(self) -> None:
        self.__message("Tear Down")
        if TEST_OUTPUT_PATH.exists():
            shutil.rmtree(TEST_OUTPUT_PATH)

    def __message(self, message):
        print("\n==========================================")
        print("%s: %s" % (message, self.id()))
        print("==========================================\n")

    def __check_dir_content(self, path_expected, path_actual):
        expected = os.listdir(path_expected)
        actual = os.listdir(path_actual)
        expected.sort()
        actual.sort()

        self.assertEqual(expected, actual)

    def __check_json_content(self, path_expected, path_actual):
        expected = get_files_with_suffix(path_expected, ".json")
        actual = get_files_with_suffix(path_actual, ".json")

        for exp, act in zip(expected, actual):
            json_exp = read_json(exp)
            json_act = read_json(act)
            if exp.name == act.name == config.MVROI_LAYOUT_FILE:
                self.assertEqual(json_exp, json_act)
            elif exp.name == act.name == config.MVROI_NAMING_FILE:
                self.assertEqual(json_exp, json_act)
            else:
                for shape_exp, shape_act in zip(json_exp["shapes"], json_exp["shapes"]):
                    self.assertAlmostEqual(shape_exp, shape_act)

    def __check_image_content(self, path_expected, path_actual):
        expected = get_files_with_suffix(path_expected, ".png")
        actual = get_files_with_suffix(path_actual, ".png")

        for exp, act in zip(expected, actual):
            img_exp = PIL.Image.open(exp)
            img_act = PIL.Image.open(act)
            self.assertIsNone(PIL.ImageChops.difference(img_exp, img_act).getbbox())

    def __check_hdf5_content(self, path_expected, path_actual):
        expected = get_files_with_suffix(path_expected, ".h5")
        actual = get_files_with_suffix(path_actual, ".h5")

        for exp, act in zip(expected, actual):
            self.assertAlmostEqual(exp.stat().st_size, act.stat().st_size, delta=500)
            h5_exp = h5py.File(exp, "r")
            h5_act = h5py.File(act, "r")
            self.assertEqual(h5_exp["/"].name, h5_act["/"].name)
            h5_exp.close()
            h5_act.close()

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(return_value=get_return_value_for_merge_patch()),
    )
    def test_merge__res_individual__equal_to_res_merged(self):
        merge.main()

        self.__check_dir_content(self.PATH_MERGED, TEST_OUTPUT_PATH)
        self.__check_json_content(self.PATH_MERGED, TEST_OUTPUT_PATH)
        self.__check_image_content(self.PATH_MERGED, TEST_OUTPUT_PATH)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                input_dir=PATH_MERGED,
                suffix=".png",
                output_dir=TEST_OUTPUT_PATH,
                split_images=True,
            )
        ),
    )
    def test_split__res_merged__equal_to_res_individuals(self):
        split.main()

        self.__check_dir_content(PATH_INDIVIDUAL, TEST_OUTPUT_PATH)
        self.__check_json_content(PATH_INDIVIDUAL, TEST_OUTPUT_PATH)
        self.__check_image_content(PATH_INDIVIDUAL, TEST_OUTPUT_PATH)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=get_return_value_for_merge_patch(hdf5_return_value=True)
        ),
    )
    def test_merge_hdf5__res_individual__equal_to_res_hdf5(self):
        merge.main()

        self.__check_dir_content(self.PATH_HDF5, TEST_OUTPUT_PATH)
        self.__check_hdf5_content(self.PATH_HDF5, TEST_OUTPUT_PATH)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                input_dir=PATH_HEATMAP,
                suffix=".jpg",
                output_dir=TEST_OUTPUT_PATH,
                min_diameter=0.05,
                bin_threshold=96,
                res="640x480",
            )
        ),
    )
    def test_generate_pseudo_label__res_label_image__equal_to_res_label_json(self):
        generate_pseudo_label.main()

        self.__check_dir_content(self.PATH_LABEL, TEST_OUTPUT_PATH)
        self.__check_json_content(self.PATH_LABEL, TEST_OUTPUT_PATH)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=get_return_value_for_merge_patch(
                input_path=TEST_OUTPUT_PATH, reindex_return_value=True
            )
        ),
    )
    @patch("builtins.input", MagicMock(return_value="y"))
    def test_reindex__res_reindex__equal_to_res_individual(self):
        shutil.copytree(self.PATH_REINDEX, TEST_OUTPUT_PATH)
        merge.main()

        expected = get_files_with_suffix(PATH_INDIVIDUAL, ".png")
        actual = get_files_with_suffix(TEST_OUTPUT_PATH, ".png")
        expected.sort()
        actual.sort()
        self.assertEqual([exp.name for exp in expected], [act.name for act in actual])

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                input_dirs=[PATH_INDIVIDUAL],
                image_topics=IMAGE_TOPICS,
                suffix=".png",
                naming=None,
                output_dir=TEST_OUTPUT_PATH,
            )
        ),
    )
    def test_prepare__res_individual__equal_to_res_prepare(self):
        prepare.main()

        image_out_path = TEST_OUTPUT_PATH.joinpath("camera_images")
        gazemap_out_path = TEST_OUTPUT_PATH.joinpath("gazemap_images")
        self.__check_dir_content(self.PATH_PREPARED, TEST_OUTPUT_PATH)
        self.__check_json_content(self.PATH_PREPARED, TEST_OUTPUT_PATH)
        self.__check_dir_content(self.PATH_PREPARED_IMAGES, image_out_path)
        self.__check_image_content(self.PATH_PREPARED_IMAGES, image_out_path)
        self.__check_dir_content(self.PATH_PREPARED_GAZEMAPS, gazemap_out_path)
        self.__check_image_content(self.PATH_PREPARED_GAZEMAPS, gazemap_out_path)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                input_dir=PATH_PREPARED_GAZEMAPS,
                naming=argparse.FileType("r")(PATH_NAMING),
                suffix=".jpg",
                output_dir=TEST_OUTPUT_PATH,
            )
        ),
    )
    def test_reformat_gaze_maps__res_prepare_gazemaps__equal_to_res_reformat(self):
        reformat_gaze_maps.main()

        out_path = TEST_OUTPUT_PATH.joinpath("individual")
        self.__check_dir_content(self.PATH_REFORMAT, out_path)
        self.__check_image_content(self.PATH_REFORMAT, out_path)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                h5_files=[argparse.FileType("r")(PATH_HDF5.joinpath("individual.h5"))],
                output_dir=TEST_OUTPUT_PATH,
            )
        ),
    )
    def test_h5_extract__res_hdf5__equal_to_res_individual(self):
        h5_extract.main()

        out_path = TEST_OUTPUT_PATH.joinpath("individual")
        self.__check_dir_content(PATH_INDIVIDUAL, out_path)
        self.__check_hdf5_content(PATH_INDIVIDUAL, out_path)

    @patch(
        "argparse.ArgumentParser.parse_args",
        MagicMock(
            return_value=argparse.Namespace(
                input_dir=PATH_CONSISTENT_IN,
                output_dir=TEST_OUTPUT_PATH,
                camera_config=PATH_CAMERA_CONFIG.joinpath("6_camera_setup.ini"),
                fov_degree=90,
                iou_threshold=0.7,
            )
        ),
    )
    def test_create_roi_consistency__res_consistent__equal_to_res_consistent_gt(self):
        create_roi_consistency.main()

        out_path = TEST_OUTPUT_PATH.joinpath("consistent_in")
        self.__check_dir_content(self.PATH_CONSISTENT, out_path)
        self.__check_json_content(self.PATH_CONSISTENT, out_path)


if __name__ == "__main__":
    print("Running all integration tests...")
    unittest.main()
