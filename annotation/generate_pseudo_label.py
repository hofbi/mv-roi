"""Generate pseudo labels from predicted heatmaps"""

import copy
import sys
from pathlib import Path
from tqdm import tqdm

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

import PIL.Image
import numpy as np
import skimage.measure

from util.args import (
    ArgumentParserFactory,
    parse_resolution,
)
from util.files import get_files_with_suffix, write_json
from util.geometry import Circle
from util import config


JSON_FILE_TEMPLATE = {
    "version": config.LABELME_VERSION,
    "flags": {},
    "lineColor": [0, 255, 0, 128],
    "fillColor": [255, 0, 0, 128],
    "imageData": None,
    "shapes": [],
}

SHAPE_TEMPLATE = {
    "label": "undefined",
    "line_color": None,
    "fill_color": None,
    "shape_type": "circle",
    "flags": {},
    "points": [],
}


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.add_input_dir_argument("Path to the predicted heatmaps")
    factory.add_output_dir_argument(
        "Path to the RGB images where the generated labels belong to and should be stored",
        Path(__file__).parent,
    )
    factory.add_suffix_argument()
    factory.add_resolution_argument()
    parser = factory.parser
    parser.add_argument(
        "-bt",
        "--bin_threshold",
        default=96,
        type=int,
        help="Values over this threshold will be binarized to 1",
    )
    parser.add_argument(
        "-md",
        "--min_diameter",
        default=0.05,
        type=float,
        help="Minimum diameter for an ROI in percent to the image width",
    )
    return parser.parse_args()


def binarize_image(heatmap_image, bin_threshold):
    """
    Convert image to binary black and white image according to threshold
    :param heatmap_image:
    :param bin_threshold:
    :return:
    """
    gray = heatmap_image.convert(config.GAZEMAP_FORMAT)
    return gray.point(lambda x: 0 if x < bin_threshold else 255, "1")


def get_roi_circles_from_bin_image(bin_image, min_diameter):
    """
    Get ROI circles from binary image if larger than minimum area
    :param bin_image:
    :param min_diameter:
    :return:
    """
    labels = skimage.measure.label(np.array(bin_image))
    return [
        Circle.from_region_props(region)
        for region in skimage.measure.regionprops(labels)
        if region.equivalent_diameter > min_diameter * bin_image.width
    ]


def get_shapes_from_roi_circles(roi_circles, x_scale, y_scale):
    """
    Get shapes from roi circles
    :param roi_circles:
    :param x_scale:
    :param y_scale:
    :return:
    """
    shapes = []
    for roi_circle in roi_circles:
        roi_circle.scale(x_scale, y_scale)
        shape_to_write = copy.deepcopy(SHAPE_TEMPLATE)
        shape_to_write["points"] = roi_circle.to_json()
        shapes.append(shape_to_write)
    return shapes


def create_pseudo_labels(
    heatmap_files, width, height, bin_threshold, min_diameter, target_image_suffix
):
    """
    Create json files with labels from predicted heatmap
    :param heatmap_files:
    :param width:
    :param height:
    :param bin_threshold:
    :param min_diameter:
    :param target_image_suffix:
    :return:
    """
    label_json_files = []
    for heatmap_file in tqdm(heatmap_files, desc="Creating Pseudo Labels..."):
        json_data = copy.deepcopy(JSON_FILE_TEMPLATE)
        json_data["imageWidth"] = width
        json_data["imageHeight"] = height
        json_data["imagePath"] = heatmap_file.stem + target_image_suffix

        heatmap_image = PIL.Image.open(heatmap_file)
        bin_image = binarize_image(heatmap_image, bin_threshold)
        roi_circles = get_roi_circles_from_bin_image(bin_image, min_diameter)
        json_data["shapes"] = get_shapes_from_roi_circles(
            roi_circles, width / heatmap_image.width, height / heatmap_image.height
        )

        label_json_files.append((heatmap_file.stem + config.LABELME_SUFFIX, json_data))

    return label_json_files


def main():
    """Main"""
    args = parse_arguments()
    width, height = parse_resolution(args.res)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    heatmap_files = get_files_with_suffix(args.input_dir, config.BDDA_IMAGE_SUFFIX)
    print(
        f"Found {len(heatmap_files)} {config.BDDA_IMAGE_SUFFIX} heatmap files in {args.input_dir}\n"
    )

    print("Creating pseudo labels from heatmaps...")
    label_json_files = create_pseudo_labels(
        heatmap_files, width, height, args.bin_threshold, args.min_diameter, args.suffix
    )

    for path, data in tqdm(label_json_files, desc="Writing label json files..."):
        write_json(output_dir / path, data)


if __name__ == "__main__":
    main()
