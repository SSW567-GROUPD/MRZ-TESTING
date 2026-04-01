import unittest
from unittest.mock import patch
import MRTD

"""Test cases for the helper that computes Fletcher-8 check digits"""
class TestFletcher8CheckDigit(unittest.TestCase):

    """Test case that a numeric only field returns expected check digit"""
    def test_fletcher8_digits_only(self):
        result = MRTD._fletcher8_check_digit("123456789")
        self.assertEqual(result, 0)

    """Test case that an alphabetic field returns the expected check digit"""
    def test_fletcher8_letters_only(self):
        result = MRTD._fletcher8_check_digit("ABC")
        self.assertEqual(result, 7)
    
    """Test case that filler characters '<' are treated as value 0"""
    def test_fletcher8_fillers(self):
        result = MRTD._fletcher8_check_digit("<<<")
        self.assertEqual(result,0)


if __name__ == "__main__":
    unittest.main()