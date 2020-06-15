"""Test args module"""

import unittest
from unittest.mock import MagicMock, patch

from util.args import parse_resolution, user_confirmation


class ArgsTest(unittest.TestCase):
    """Args test"""

    @patch("builtins.input", MagicMock(return_value="y"))
    def test_user_confirmation__y__true(self):
        self.assertTrue(user_confirmation(""))

    @patch("builtins.input", MagicMock(return_value="n"))
    def test_user_confirmation__n__true(self):
        self.assertFalse(user_confirmation(""))

    def test_parse_resolution__width_x_height__correct(self):
        result = parse_resolution("10x5")
        self.assertEqual((10, 5), result)


if __name__ == "__main__":
    unittest.main()
