"""Argparse common functions and helpers"""

from pathlib import Path
import argparse


def user_confirmation(message):
    """
    Ask user to enter Y or N (case-insensitive).
    :param: message
    :return: True if the answer is Y.
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("%s. Are you sure you want to continue [Y/N]?" % message).lower()
    return answer == "y"


def parse_resolution(resolution):
    """
    Parse image resolution string
    :param resolution:
    :return:
    """
    resolution = resolution.split("x")
    return int(resolution[0]), int(resolution[1])


class ArgumentParserFactory:
    """Argument Parser Factory to setup arparser with common use arguments"""

    def __init__(self, description):
        self.__parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    @property
    def parser(self):
        return self.__parser

    @staticmethod
    def is_dir_path(path_string):
        """
        Argparse type check if path is a directory
        :param path_string:
        :return:
        """
        if Path(path_string).is_dir():
            return path_string
        else:
            raise NotADirectoryError(path_string)

    @staticmethod
    def is_suffix(value):
        if value.startswith("."):
            return value
        raise ValueError(
            "%s is not a valid suffix. A suffix has to start with a >.<." % value
        )

    def add_input_dir_argument(self, help_text):
        self.__parser.add_argument(
            "input_dir",
            type=self.is_dir_path,
            help=help_text,
        )

    def add_output_dir_argument(self, help_text, default):
        self.__parser.add_argument(
            "-o",
            "--output_dir",
            default=default,
            type=str,
            help=help_text,
        )

    def add_common_arguments(self):
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

    def add_resolution_argument(self):
        """
        Add image resolution argument to parser
        :return:
        """

        def check_res(value):
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

    def add_suffix_argument(self):
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

    def add_image_topics_argument(self, help_text):
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
