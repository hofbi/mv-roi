"""Prepare the input data according to the bdda naming concentions"""

import sys
from pathlib import Path
from tqdm import tqdm

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

import PIL.Image
import PIL.ImageDraw

from util.args import ArgumentParserFactory
from util.files import (
    ScenarioGrouper,
    get_files_with_suffix,
    read_json,
    FileGrouper,
    write_json,
)
from util.geometry import Circle
from util import config


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """

    factory = ArgumentParserFactory(__doc__)
    factory.parser.add_argument(
        "input_dirs",
        type=ArgumentParserFactory.is_dir_path,
        nargs="+",
        help="Path to the directories with driving scenarios.",
    )
    factory.add_output_dir_argument(
        "Path to the directory where the prepared files will be put.",
        Path(__file__).parent.joinpath("data"),
    )
    factory.add_suffix_argument()
    factory.add_image_topics_argument(
        "All image topics that should be should be prepared"
    )
    parser = factory.parser
    parser.add_argument(
        "-n",
        "--naming",
        type=str,
        help="Naming file required for converting back from the bdda naming convention. "
        "This file is generated by this tool. If this file provided the naming data will "
        "be appended to this file.",
    )

    return parser.parse_args()


def append_naming_data(scenario_groups, naming_data):
    """
    Append naming data to match bdda naming conventions
    :param scenario_groups:
    :param naming_data:
    :return:
    """
    for scenario_group in scenario_groups:
        for topic in scenario_group.image_topics:
            naming_data[
                scenario_group.get_sequence_index_for_topic(topic)
            ] = scenario_group.get_naming_data_for_topic(topic)
    return naming_data


def init_naming_data(naming_file_arg):
    """
    Init naming data from optional naming file
    :param naming_file_arg:
    :return:
    """
    if naming_file_arg is None:
        return {}
    else:
        return read_json(naming_file_arg)


def get_scenario_start_index(naming_data):
    """
    Get scenario start index from naming data
    :param naming_data:
    :return:
    """
    if naming_data:
        scenario_indices = [val["scenario_index"] for val in naming_data.values()]
        return max(scenario_indices) + 1
    return 1


def create_gazemap_from_shapes(shapes, image_size):
    """
    Create gazemap from ROI shapes
    :param shapes:
    :param image_size:
    :return:
    """
    image = PIL.Image.new(config.GAZEMAP_FORMAT, image_size)
    draw = PIL.ImageDraw.Draw(image)
    for shape in shapes:
        roi = Circle.from_json(shape["points"])
        draw.ellipse(roi.bounding_box, fill=255, outline=255)
    return image


def prepare_scenario_group_images(scenario_group, output_image_dir):
    """
    Copy image files with correct name
    :param scenario_group:
    :param output_image_dir:
    :return:
    """
    size = None
    for path_pair in scenario_group.get_prepared_path_pairs(
        scenario_group.image_groups, output_image_dir, config.BDDA_IMAGE_SUFFIX
    ):
        image = PIL.Image.open(path_pair.source)
        size = image.size
        image = image.convert(config.IMAGE_FORMAT)
        image.save(path_pair.target)
    return size


def prepare_scenario_group_gazemaps(scenario_group, image_size, output_gaze_path):
    """
    Create gaze maps from labels
    :param scenario_group:
    :param image_size:
    :param output_gaze_path:
    :return:
    """
    if image_size is None:
        raise ValueError("Cannot convert labels without corresponding images.")
    for path_pair in scenario_group.get_prepared_path_pairs(
        scenario_group.json_groups, output_gaze_path, config.BDDA_IMAGE_SUFFIX
    ):
        json_data = read_json(path_pair.source)
        gazemap = create_gazemap_from_shapes(json_data["shapes"], image_size)
        gazemap.save(path_pair.target)


def main():
    """main"""
    args = parse_arguments()

    output_image_path = Path(args.output_dir).joinpath("camera_images")
    output_gaze_path = Path(args.output_dir).joinpath("gazemap_images")
    output_image_path.mkdir(parents=True, exist_ok=True)
    output_gaze_path.mkdir(parents=True, exist_ok=True)
    input_dirs = [Path(input_dir) for input_dir in args.input_dirs]

    naming_data = init_naming_data(args.naming)

    print("Reading scenarios...")
    scenario_index = get_scenario_start_index(naming_data)
    num_previous_scenarios = scenario_index - 1
    scenario_groups = []
    for input_dir in input_dirs:
        image_files = get_files_with_suffix(input_dir, args.suffix)
        json_files = get_files_with_suffix(input_dir, config.LABELME_SUFFIX)
        scenario_grouper = ScenarioGrouper(
            scenario_index,
            input_dir.name,
            args.image_topics,
            image_files,
            json_files,
        )
        if not image_files:
            print(
                "Could not find any image files in scenario %s with %s extension. "
                "Make sure you set the corrent suffix with --suffix."
                % (scenario_grouper.scenario_name, args.suffix),
                file=sys.stderr,
            )
            sys.exit(1)
        if not scenario_grouper.is_valid:
            print(
                "Images of scenario %s are not aligned or of same length for topics %s.\n"
                "Run merge.py with --reindex to align your files"
                % (scenario_grouper.scenario_name, args.image_topics),
                file=sys.stderr,
            )
            sys.exit(1)
        if FileGrouper.is_empty(scenario_grouper.image_groups):
            print(
                "None of the image files for scenario %s is matching a topic in %s"
                % (scenario_grouper.scenario_name, args.image_topics),
                file=sys.stderr,
            )
            sys.exit(1)
        scenario_groups.append(scenario_grouper)
        scenario_index += 1

    print("Write %s" % config.MVROI_NAMING_FILE)
    naming_data = append_naming_data(scenario_groups, naming_data)
    write_json(Path(args.output_dir).joinpath(config.MVROI_NAMING_FILE), naming_data)

    for scenario_group in tqdm(scenario_groups, desc="Preparing scenarios..."):
        size = prepare_scenario_group_images(scenario_group, output_image_path)
        prepare_scenario_group_gazemaps(scenario_group, size, output_gaze_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
