"""Merge images and json labels"""

import copy
import sys
from pathlib import Path

from tqdm import tqdm

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

import PIL.Image

from util import config
from util.args import ArgumentParserFactory, parse_resolution, user_confirmation
from util.files import (
    FileGrouper,
    FileReindexer,
    ImageLayoutModel,
    get_files_with_suffix,
    read_json,
    write_json,
)
from util.geometry import shift_label_points
from util.h5 import HDF5Writer


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """

    factory = ArgumentParserFactory(__doc__)
    factory.add_common_arguments()
    factory.add_resolution_argument()
    factory.add_image_topics_argument(
        "All image topics that should be should be merged together. "
        "The order defines the layout of merging.",
    )
    parser = factory.parser
    parser.add_argument(
        "--images_per_row",
        type=int,
        default=3,
        help="Number of images that are aligned next to each other",
    )
    parser.add_argument(
        "--hdf5",
        action="store_true",
        help="Merge files into hdf5 file",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Reindex image and label files to a sequential continuous numbering",
    )

    return parser.parse_args()


def create_layout_data(image_topics, images_per_row, width, height):
    """
    Create layout data to calculate ROI position for individual frames
    :param image_topics:
    :param images_per_row:
    :param width:
    :param height:
    :return:
    """
    data = {"layout": []}
    x_count = 0
    y_count = 0
    for topic in image_topics:
        if x_count == images_per_row:
            y_count += 1
            x_count = 0

        data["layout"].append(
            ImageLayoutModel.create(
                topic, x=x_count * width, y=y_count * height, width=width, height=height
            ).image_layout
        )
        x_count += 1

    data["width"] = images_per_row * width
    data["height"] = height + height * y_count

    return data


def merge_frames(image_merge_groups, output_dir, image_suffix):
    """
    merge individual frames of different camera views into a single frame and write to file
    :param image_merge_groups:
    :param output_dir:
    :param image_suffix:
    :return:
    """
    for index, merge_group in enumerate(
        tqdm(image_merge_groups, desc="Merging images...")
    ):
        result = PIL.Image.new(
            config.IMAGE_FORMAT, (merge_group.width, merge_group.height)
        )
        for layout in merge_group.image_layouts:
            file_path = merge_group.get_file_path_by_key(layout.key)
            # TODO resize to given resolution
            result.paste(
                PIL.Image.open(file_path),
                layout.top_left,
            )

        result.save(Path(output_dir) / f"merged_{index:06d}{image_suffix}")


def merge_json_data(json_merge_groups, image_suffix):
    """
    Merge individual frames json data into single frame json data
    :param json_merge_groups:
    :param image_suffix:
    :return:
    """
    merged_json_data = []
    for index, json_merge_group in enumerate(
        tqdm(json_merge_groups, desc="Merging json...")
    ):
        merged_json = copy.deepcopy(
            json_merge_group.image_layouts[0].image_layout
        )  # Use any layout as template
        merged_json["imageData"] = None
        merged_json["imageHeight"] = json_merge_group.height
        merged_json["imageWidth"] = json_merge_group.width
        merged_json["shapes"] = []
        merged_json["imagePath"] = f"merged_{index:06d}{image_suffix}"
        for layout in json_merge_group.image_layouts:
            file_path = json_merge_group.get_file_path_by_key(layout.key)
            json_data = read_json(file_path)
            json_data = shift_label_points(json_data, layout.x, layout.y)
            merged_json["shapes"].extend(json_data["shapes"])

        merged_json_data.append(merged_json)

    return merged_json_data


def file_merge(output_dir: Path, image_grouper, json_grouper, image_suffix):
    """
    Merge individual image and json files into files
    :param output_dir:
    :param image_grouper:
    :param json_grouper:
    :param image_suffix:
    :return:
    """
    merge_frames(image_grouper.merge_groups, output_dir, image_suffix)
    merged_json_data = merge_json_data(json_grouper.merge_groups, image_suffix)
    for index, merged_data in enumerate(
        tqdm(merged_json_data, desc="Writing merged json files...")
    ):
        write_json(output_dir.joinpath(f"merged_{index:06d}.json"), merged_data)


def hdf5_merge(args, image_grouper, json_grouper):
    """
    Merge individual image and json files into a hdf5 file
    :param args:
    :param image_grouper:
    :param json_grouper:
    :return:
    """
    h5_name = args.output_dir.joinpath(Path(args.input_dir).with_suffix(".h5").name)
    print(f"Creating HDF5 file {h5_name}")
    writer = HDF5Writer(h5_name)
    for index, merge_group in enumerate(
        tqdm(
            image_grouper.merge_groups,
            desc="Adding images to hdf5 file...",
        )
    ):
        writer.add_image_group(index, merge_group)
    for index, merge_group in enumerate(
        tqdm(json_grouper.merge_groups, desc="Adding json labels to hdf5 file...")
    ):
        writer.add_roi_group(index, merge_group)


def reindex_files(image_files, image_topics):
    """
    Reindex files to follow required structure
    :param image_files:
    :param image_topics:
    :return:
    """
    image_reindexer = FileReindexer(image_files, image_topics)
    if user_confirmation(
        f"{len(image_reindexer.files_to_remove)}/{len(image_files)} samples will be removed"
    ):
        image_reindexer.clean_up()
    if user_confirmation(
        f"{len(image_reindexer.files_to_remove)}/{len(image_files)} samples with "
        f"{len(image_topics)} topics will be reindexed"
    ):
        image_reindexer.reindex()


def main():
    """main"""
    args = parse_arguments()
    width, height = parse_resolution(args.res)

    input_dir = args.input_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    layout_data = create_layout_data(
        args.image_topics, args.images_per_row, width, height
    )
    if not (args.hdf5 or args.reindex):
        print(f"Write {config.MVROI_LAYOUT_FILE}")
        write_json(output_dir.joinpath(config.MVROI_LAYOUT_FILE), layout_data)

    image_files = get_files_with_suffix(input_dir, args.suffix)
    json_files = get_files_with_suffix(
        input_dir, ".json", ignore=config.MVROI_LAYOUT_FILE
    )
    print(
        f"Found {len(image_files)} {args.suffix} images and {len(json_files)} "
        f"label files in {input_dir}\n"
    )

    if args.reindex:
        print("Reindexing files...")
        reindex_files(image_files, args.image_topics)
        return

    print("Grouping files for merging...")
    image_grouper = FileGrouper(layout_data, image_files, args.image_topics)
    json_grouper = FileGrouper(layout_data, json_files, args.image_topics)
    if not (image_grouper.is_valid and json_grouper.is_valid):
        print(
            "Image or json files not aligned or of same length for topics "
            f"{args.image_topics}.\nRun with --reindex to align your files",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Found {len(image_grouper.merge_groups)} image and "
        f"{len(json_grouper.merge_groups)} json groups to merge\n"
    )

    if args.hdf5:
        hdf5_merge(args, image_grouper, json_grouper)
    else:
        file_merge(args.output_dir, image_grouper, json_grouper, args.suffix)


if __name__ == "__main__":
    main()
