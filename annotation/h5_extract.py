"""Extract data from hdf5 file"""

import argparse
import sys
from pathlib import Path

try:
    sys.path.append(str(Path(__file__).absolute().parent.parent))
except IndexError:
    pass

from util.args import ArgumentParserFactory
from util.h5 import HDF5Extractor


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """
    factory = ArgumentParserFactory(__doc__)
    factory.parser.add_argument(
        "h5_files",
        type=argparse.FileType("r"),
        nargs="+",
        help="Path to the hdf5 files.",
    )
    factory.add_output_dir_argument(
        "Path to the output directory",
        Path(__file__).parent,
    )
    return factory.parser.parse_args()


def main():
    """main"""
    args = parse_arguments()

    for h5_file in args.h5_files:
        extractor = HDF5Extractor(Path(h5_file.name))
        print(f"Extract data from {h5_file.name} into {args.output_dir}")
        extractor.extract_data(args.output_dir)


if __name__ == "__main__":
    main()
