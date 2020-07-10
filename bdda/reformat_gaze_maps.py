"""Reformat the predicted gaze maps into the pipeline naming convention"""

import shutil
from pathlib import Path
import sys
import argparse
from tqdm import tqdm

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

from util.args import ArgumentParserFactory
from util.files import read_json, get_files_with_suffix, FileGrouper, PathPair
from util import config


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.add_input_dir_argument("Path to the predicted gazemaps")
    factory.add_output_dir_argument(
        "Path to the output directory where the gazemaps will be put according to its scenarios",
        Path(__file__).parent,
    )
    factory.add_suffix_argument()
    parser = factory.parser
    parser.add_argument(
        "naming", type=argparse.FileType("r"), help="Path to the naming.json"
    )
    return parser.parse_args()


def get_path_pair_gazemap_groups(gazemap_groups, naming_data, output_path):
    """
    Get path pair groups from gazemap groups
    :param gazemap_groups:
    :param naming_data:
    :param output_path:
    :return:
    """
    pair_groups = {}
    for key, files in gazemap_groups.items():
        pair_groups[key] = []
        scenario_name = naming_data[key]["scenario_name"]
        view = naming_data[key]["view"]
        for file_model in files:
            target_path = (
                Path(output_path)
                .joinpath(scenario_name)
                .joinpath(file_model.get_file_name_with_view_key(view))
            )
            pair_groups[key].append(PathPair(file_model.file_path, target_path))
    return pair_groups


def reformat_gaze_map_sequence(pair_group):
    """
    Reformat gaze maps
    :param pair_group:
    :return:
    """
    for index, pair in enumerate(pair_group):
        if index == 0:
            pair.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(pair.source, pair.target)


def main():
    """main"""
    args = parse_arguments()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    print("Reading %s..." % config.MVROI_NAMING_FILE)
    naming_data = read_json(args.naming.name)

    gazemaps = get_files_with_suffix(args.input_dir, args.suffix)
    gazemap_groups = FileGrouper.group_files_by_keys(gazemaps, naming_data.keys())
    grouped_pairs = get_path_pair_gazemap_groups(
        gazemap_groups, naming_data, args.output_dir
    )
    print(
        "Found %d %s gazemaps in %d groups"
        % (len(gazemaps), config.BDDA_IMAGE_SUFFIX, len(gazemap_groups.keys()))
    )

    bar = tqdm(grouped_pairs.items())
    for key, pair_group in bar:
        bar.set_description("Reformatting sequence for index %s..." % key)
        reformat_gaze_map_sequence(pair_group)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
