"""Run all tests of this project"""

import unittest
import argparse


def parse_arguments():
    """
    Parse command line arguments
    :return:
    """

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--integration_tests", action="store_true", help="Run integration tests",
    )

    return parser.parse_args()


if __name__ == "__main__":
    ARGS = parse_arguments()

    if ARGS.integration_tests:
        print("Running all integration tests...")
        ALL_TESTS = unittest.TestLoader().discover("test", pattern="*_test.py")
    else:
        print("Running all unit tests...")
        ALL_TESTS = unittest.TestLoader().discover("test")

    unittest.TextTestRunner().run(ALL_TESTS)
