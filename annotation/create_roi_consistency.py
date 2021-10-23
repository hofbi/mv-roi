"""Create ROI consistent label json files for multiple views"""

import math
from tqdm import tqdm
import sys
from pathlib import Path
from typing import Dict
from configparser import ConfigParser
import itertools

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

from util.args import ArgumentParserFactory
from util.files import get_files_with_suffix, read_json, write_json, FileReindexer
from util.geometry import Circle
from util import config
from util.camera import RoiView, RoiViewPair
from annotation.generate_pseudo_label import get_shapes_from_roi_circles


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.add_input_dir_argument(
        "Path to the directory which contains the images and labels in json format."
    )
    factory.add_output_dir_argument(
        "Path to the directory where the roi consistent label files will be put.",
        Path(__file__).parent.joinpath("_out"),
    )
    parser = factory.parser
    parser.add_argument(
        "-c",
        "--camera-config",
        type=ArgumentParserFactory.file_path,
        default=(
            Path(__file__).parent.parent / "record" / "config" / "6_camera_setup.ini"
        ),
        help="Path to the camera config file that contains the camera positions",
    )
    parser.add_argument(
        "-f",
        "--fov-degree",
        type=float,
        default=90.0,
        help="Field of camera view in degree",
    )
    parser.add_argument(
        "-i",
        "--iou-threshold",
        type=float,
        default=0.7,
        help="IOU threshold to adjust if a new ROI circle need to be added",
    )
    return parser.parse_args()


def read_camera_config(camera_config_path: Path) -> Dict:
    """Read the camera config file"""
    config_parser = ConfigParser()
    config_parser.read(camera_config_path)
    return {
        section: dict(config_parser.items(section))
        for section in config_parser.sections()
    }


def create_circle_list_from_json(jsonfile):
    """
    Extract the ROI information from json file and store it in the dictionary
    :return:
    """
    return [Circle.from_json(shape["points"]) for shape in jsonfile["shapes"]]


def sync_rois_for_scene(json_files, camera_orientation_list, iou_threshold, fov_degree):
    """Sync the ROIs for one scene"""
    image_width = json_files[0]["imageWidth"]
    roi_view_list = [
        RoiView(
            create_circle_list_from_json(json_file),
            camera_orientation_list[json_files.index(json_file)],
            image_width,
            iou_threshold,
            math.radians(fov_degree),
        )
        for json_file in json_files
    ]
    unique_permutations = list(itertools.product(*[roi_view_list, roi_view_list]))
    for unique_permutation in unique_permutations:
        roi_view_pair = RoiViewPair(
            unique_permutation[0],
            unique_permutation[1],
        )
        roi_view_pair.sync_rois_between_views()
    return [roi_view.rois for roi_view in roi_view_list]


def main():
    """main"""
    args = parse_arguments()

    output_path = args.output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    input_dir = args.input_dir

    camera_config = read_camera_config(args.camera_config)
    camera_orientation_list = [
        math.radians(float(camera_config[camera_position]["yaw"]))
        for camera_position in camera_config.keys()
    ]

    print("Reading scenarios...")
    json_files = get_files_with_suffix(input_dir, config.LABELME_SUFFIX)

    print(f"Processing the dataset {input_dir.name}")
    consistent_output_path = output_path.joinpath(input_dir.name)
    consistent_output_path.mkdir(parents=True, exist_ok=True)
    file_groups = FileReindexer.group_files_by_index(json_files)
    for file_group in tqdm(file_groups.values()):
        file_group_content = [
            read_json(json_file.file_path) for json_file in file_group
        ]
        roi_view_list = sync_rois_for_scene(
            file_group_content,
            camera_orientation_list,
            args.iou_threshold,
            args.fov_degree,
        )
        for json_file in file_group:
            json_file_one_frame = read_json(json_file.file_path)
            json_file_one_frame["shapes"] = get_shapes_from_roi_circles(
                roi_view_list[file_group.index(json_file)], 1, 1
            )
            outfile = consistent_output_path / json_file.file_path.name
            write_json(outfile, json_file_one_frame)


if __name__ == "__main__":
    main()
