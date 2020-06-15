"""Generate fake gazemaps required for prediction for a directory of images"""

import sys
from pathlib import Path
from tqdm import tqdm

import PIL.Image

try:
    sys.path.append(Path(__file__).parent.parent)
except IndexError:
    pass

from util.args import ArgumentParserFactory
from util.files import get_files_with_suffix
from util import config
from bdda.prepare import create_gazemap_from_shapes


def generate_fake_gazemaps(image_file, output_dir):
    """
    Generate fake gazemap for image file
    :param image_file:
    :param output_dir:
    :return:
    """
    size = PIL.Image.open(image_file).size
    fake_gazemap = create_gazemap_from_shapes([], size)
    gazemap_path = Path(output_dir).joinpath(image_file.name)
    fake_gazemap.save(gazemap_path)


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.add_input_dir_argument("Path to the image files.")
    factory.add_output_dir_argument(
        "Path where the fake gazemaps will be put.", Path(__file__).parent
    )
    return factory.parser.parse_args()


def main():
    """main"""
    args = parse_arguments()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    image_files = get_files_with_suffix(args.input_dir, config.BDDA_IMAGE_SUFFIX)
    for image_file in tqdm(image_files, desc="Generating fake gazemaps..."):
        generate_fake_gazemaps(image_file, args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
