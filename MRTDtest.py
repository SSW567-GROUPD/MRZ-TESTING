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

    """Test case that tests mixed MRZ-style field with letters, fillers and digits"""
    def test_fletcher8_mixed_characters(self):
        result = MRTD._fletcher8_check_digit("A12<BC9")
        self.assertEqual(result, 2)
    
    """Test that the lowercase and uppercase letters create same check digit"""
    def test_fletcher8_case_insensitive(self):
        upper_result = MRTD._fletcher8_check_digit("ABC123")
        lower_result = MRTD._fletcher8_check_digit("abc123")
        self.assertEqual(upper_result, lower_result)

"""Unit tests for the decodeMRZ()"""
class TestDecodeMRZ(unittest.TestCase):

    """Test if decodeMRZ returns an error dict when scanMRZ returns None"""
    @patch("MRTD.scanMRZ")
    def test_decodeMRZ_no_data_returned(self, mock_scan):
        mock_scan.return_value = None

        result = MRTD.decodeMRZ()

        self.assertIn("errors", result)
        self.assertEqual(result["errors"][0]["field"], "scanMRZ")
        self.assertEqual(result["errors"][0]["error"], "No data returned from scanner")
    
    """Test if decodeMRZ reports both lin length errors when both are invalid"""
    @patch("MRTD.scanMRZ")
    def test_decodeMRZ_invalid_line_length(self, mock_scan):
        mock_scan.return_value = ("short", "too_short")
        result = MRTD.decodeMRZ()

        self.assertIn("errors", result)
        self.assertEqual(len(result["errors"]), 2)
        self.assertEqual(result["errors"][0]["field"], "line1")
        self.assertEqual(result["errors"][1]["field"], "line2")
    
    """Test if decoding of a valid MRZ record with all check digits matching"""
    @patch("MRTD.scanMRZ")
    def test_decodeMRZ_valid_record_digits_valid(self, mock_scan):
        line1 = "P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<"
        line2 = "W620126G58CIV5910107F9707307AJ010215I<<<<<<9"
        mock_scan.return_value = (line1, line2)
        result = MRTD.decodeMRZ()


        self.assertEqual(result["issuing_country"], "CIV")
        self.assertEqual(result["last_name"], "LYNN")
        self.assertEqual(result["given_name"], "NEVEAH BRAM")
        self.assertEqual(result["passport_number"], "W620126G5")
        self.assertEqual(result["country_code"], "CIV")
        self.assertEqual(result["birth_date"], "591010")
        self.assertEqual(result["sex"], "F")
        self.assertEqual(result["expiration_date"], "970730")
        self.assertEqual(result["personal_number"], "AJ010215I")

        self.assertTrue(result["check_digits"]["passport_number"]["valid"])
        self.assertTrue(result["check_digits"]["birth_date"]["valid"])
        self.assertTrue(result["check_digits"]["expiration_date"]["valid"])
        self.assertTrue(result["check_digits"]["personal_number"]["valid"])






if __name__ == "__main__":
    unittest.main()