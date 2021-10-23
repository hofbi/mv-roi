"""Argparse common functions and helpers"""

from pathlib import Path
import argparse
from typing import Any


def user_confirmation(message: str) -> bool:
    """
    Ask user to enter Y or N (case-insensitive).
    :param: message
    :return: True if the answer is Y.
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("%s. Are you sure you want to continue [Y/N]?" % message).lower()
    return answer == "y"


def parse_resolution(resolution: str) -> (int, int):
    """
    Parse image resolution string
    :param resolution:
    :return:
    """
    resolution = resolution.split("x")
    return int(resolution[0]), int(resolution[1])


class ArgumentParserFactory:
    """Argument Parser Factory to setup arparser with common use arguments"""

    def __init__(self, description: str):
        self.__parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    @property
    def parser(self) -> argparse.ArgumentParser:
        return self.__parser

    @staticmethod
    def dir_path(path_string: str) -> Path:
        """
        Argparse type check if path is a directory
        :param path_string:
        :return:
        """
        if Path(path_string).is_dir():
            return Path(path_string)
        else:
            raise NotADirectoryError(path_string)

    @staticmethod
    def file_path(path_string: str) -> Path:
        """
        Argparse type check if path is a file
        :param path_string:
        :return:
        """
        if Path(path_string).is_file():
            return Path(path_string)
        else:
            raise NotADirectoryError(path_string)

    @staticmethod
    def is_suffix(value: str) -> str:
        if value.startswith("."):
            return value
        raise ValueError(
            f"{value} is not a valid suffix. A suffix has to start with a >.<."
        )

    def add_input_dir_argument(self, help_text: str) -> None:
        self.__parser.add_argument(
            "input_dir",
            type=self.dir_path,
            help=help_text,
        )

    def add_output_dir_argument(self, help_text: str, default: Any) -> None:
        self.__parser.add_argument(
            "-o",
            "--output_dir",
            default=default,
            type=Path,
            help=help_text,
        )

    def add_common_arguments(self) -> None:
        """
        Add common CLI arguments to argparse parser
        :return:
        """
        self.add_input_dir_argument(
            "Path to the directory which contains the images and labels in json format."
        )
        self.add_output_dir_argument(
            "Path to the directory where the generated files will be put.",
            Path(__file__).parent,
        )
        self.add_suffix_argument()

    def add_resolution_argument(self) -> None:
        """
        Add image resolution argument to parser
        :return:
        """

        def check_res(value: str) -> str:
            if "x" not in value:
                raise argparse.ArgumentTypeError(
                    "No valid camera resolution provided. Should be WIDTHxHEIGHT"
                )
            return value

        self.__parser.add_argument(
            "-r",
            "--res",
            help="Single camera resolution WIDTHxHEIGHT",
            type=check_res,
            default="640x480",
        )

    def add_suffix_argument(self) -> None:
        """
        Add image suffix argument to parser
        :return:
        """
        self.__parser.add_argument(
            "-s",
            "--suffix",
            default=".png",
            type=self.is_suffix,
            help="Suffix of the image files.",
        )

    def add_image_topics_argument(self, help_text: str) -> None:
        """
        Add image topics argument to parser
        :param help_text:
        :return:
        """
        self.__parser.add_argument(
            "--image_topics",
            type=str,
            nargs="+",
            help=help_text,
            default=[
                "front_left",
                "front",
                "front_right",
                "rear_left",
                "rear",
                "rear_right",
            ],
        )
