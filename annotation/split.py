"""Split images and json labels"""

import copy
import sys
from pathlib import Path
from tqdm import tqdm

try:
    sys.path.append(Path(__file__).parent.parent)
except IndexError:
    pass

import PIL.Image

from util.args import ArgumentParserFactory
from util.files import (
    get_files_with_suffix,
    ImageLayoutModel,
    FileModel,
    read_json,
    write_json,
)
from util.geometry import is_shape_inside, shift_label_points
from util import config


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.add_common_arguments()
    parser = factory.parser
    parser.add_argument(
        "--split_images",
        action="store_true",
        help="Split merged images into individual ones. This is disabled by default "
        "safe memory and speed up the runtime as usually the individual images "
        "before merging are still available.",
    )
    return parser.parse_args()


def split_images(images_files, layout, output_dir):
    """
    Split images into individuals according to the provided layout
    :param images_files:
    :param layout:
    :param output_dir:
    :return:
    """
    for image_file in tqdm(images_files, desc="Splitting images..."):
        image_file_model = FileModel(image_file)
        image = PIL.Image.open(image_file)
        for image_segment in layout["layout"]:
            layout_model = ImageLayoutModel(image_segment)
            segment = image.crop(layout_model.box)
            segment.save(
                Path(output_dir).joinpath(
                    image_file_model.get_file_name_with_view_key(layout_model.key)
                )
            )


def split_json_data(json_files, layout, image_suffix):
    """
    Split json data into individuals according to the provided layout
    :param json_files:
    :param layout:
    :param image_suffix:
    :return:
    """
    files_to_save = []
    for json_file in tqdm(json_files, desc="Splitting json..."):
        json_file_model = FileModel(json_file)
        json_data = read_json(json_file)
        for image_segment in layout["layout"]:
            layout_model = ImageLayoutModel(image_segment)
            segment_data = crop_from_json(json_data, layout_model)
            file_name = json_file_model.get_file_name_with_view_key(layout_model.key)
            segment_data["imagePath"] = Path(file_name).stem + image_suffix
            files_to_save.append((file_name, segment_data))

    return files_to_save


def crop_from_json(json_data, layout_model):
    """
    Crop label coordinates from json according to layout model
    :param json_data:
    :param layout_model:
    :return:
    """
    segment_data = copy.deepcopy(json_data)
    segment_data["imageWidth"] = layout_model.width
    segment_data["imageHeight"] = layout_model.height
    segment_data["shapes"] = [
        shape
        for shape in segment_data["shapes"]
        if is_shape_inside(shape, layout_model)
    ]
    return shift_label_points(segment_data, -layout_model.x, -layout_model.y)


def main():
    """Main"""
    args = parse_arguments()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    image_files = get_files_with_suffix(args.input_dir, args.suffix)
    json_files = get_files_with_suffix(args.input_dir, config.LABELME_SUFFIX)
    layout_json = [
        json_files.pop(json_files.index(file))
        for file in json_files
        if config.MVROI_LAYOUT_FILE == file.name
    ]
    if not layout_json:
        print(
            "Input folder does not contain a %s file." % config.MVROI_LAYOUT_FILE,
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "Found %d %s images and %d label files in %s\n"
        % (len(image_files), args.suffix, len(json_files), args.input_dir)
    )

    layout_data = read_json(layout_json[0])

    if args.split_images:
        split_images(image_files, layout_data, args.output_dir)
    individual_json_files = split_json_data(json_files, layout_data, args.suffix)
    for path, data in tqdm(individual_json_files, desc="Writing json files..."):
        write_json(Path(args.output_dir).joinpath(path), data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
