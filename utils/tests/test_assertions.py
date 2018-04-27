import unittest

from utils.assertions import check_response_length


class TestCheckResponseLength(unittest.TestCase):
    def test_desired_1_actual_1(self):
        """Test should complete without exception thrown"""
        response = [1]
        check_response_length(response, min_length=1, max_length=1)

    def test_desired_1_actual_0(self):
        """Function should throw a Runtime Exception"""
        response = []
        with self.assertRaises(RuntimeError):
            check_response_length(response, min_length=1, max_length=1)

    def test_desired_1_actual_2(self):
        response = [1, 2]
        with self.assertRaises(RuntimeError):
            check_response_length(response, min_length=1, max_length=1)

    def no_max(self):
        response = [1, 2]
        check_response_length(response, min_length=1)

    def test_both_args_none(self):
        with self.assertRaises(RuntimeError):
            check_response_length([1])
