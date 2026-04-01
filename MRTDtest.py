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

    """Test if trailing filler characters are removed from passport and personal numbers"""
    @patch("MRTD.scanMRZ")
    def test_decodeMRZ_trims_filler_from_variable_length_fields(self, mock_scan):
        line1 = "P<USASMITH<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        passport = "A12<<<<<<"
        passport_cd = str(MRTD._fletcher8_check_digit(passport))
        country = "USA"
        birth = "900101"
        birth_cd = str(MRTD._fletcher8_check_digit(birth))
        sex = "M"
        expiration = "300101"
        expiration_cd = str(MRTD._fletcher8_check_digit(expiration))
        personal = "ABC<<<<<<<<<<<<"
        personal_cd = str(MRTD._fletcher8_check_digit(personal))
        line2 = passport + passport_cd + country + birth + birth_cd + sex + expiration + expiration_cd + personal + personal_cd

        mock_scan.return_value = (line1, line2)

        result = MRTD.decodeMRZ()

        self.assertEqual(result["passport_number"], "A12")
        self.assertEqual(result["personal_number"], "ABC")


"""Unit tests for encodeMRZ(), using mocks for the database stub."""
class TestEncodeMRZ(unittest.TestCase):

    @patch("MRTD.getFromDB")
    def test_encode_mrz_no_data_returned(self, mock_db):
        """Test that encodeMRZ returns an error dict when getFromDB returns None."""
        mock_db.return_value = None

        result = MRTD.encodeMRZ()

        self.assertIn("errors", result)
        self.assertEqual(result["errors"][0]["field"], "getFromDB")
        self.assertEqual(result["errors"][0]["error"], "No data returned from database")

    """Test encoding of a normal valid database record into two 44-character MRZ lines"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_valid_record(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "CIV",
            "last_name": "LYNN",
            "given_name": "NEVEAH BRAM",
            "passport_number": "W620126G5",
            "country_code": "CIV",
            "birth_date": "591010",
            "sex": "F",
            "expiration_date": "970730",
            "personal_number": "AJ010215I",
        }

        line1, line2 = MRTD.encodeMRZ()

        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertEqual(line1, "P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<")
        self.assertEqual(line2, "W620126G58CIV5910107F9707307AJ010215I<<<<<<9")

    """Test if missing sex defaults to '<' in the encoded MRZ"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_missing_sex_defaults_to_filler(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "USA",
            "last_name": "DOE",
            "given_name": "JOHN",
            "passport_number": "123456789",
            "country_code": "USA",
            "birth_date": "900101",
            "expiration_date": "300101",
            "personal_number": "ABC123",
        }

        line1, line2 = MRTD.encodeMRZ()

        self.assertEqual(line2[20], "<")

    """Test if an empty sex string also defaults to '<'"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_empty_sex_defaults_to_filler(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "USA",
            "last_name": "DOE",
            "given_name": "JOHN",
            "passport_number": "123456789",
            "country_code": "USA",
            "birth_date": "900101",
            "sex": "",
            "expiration_date": "300101",
            "personal_number": "ABC123",
        }

        _, line2 = MRTD.encodeMRZ()

        self.assertEqual(line2[20], "<")

    """Test if only the first character of the sex field is encoded"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_only_first_character_of_sex_used(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "USA",
            "last_name": "DOE",
            "given_name": "JOHN",
            "passport_number": "123456789",
            "country_code": "USA",
            "birth_date": "900101",
            "sex": "Female",
            "expiration_date": "300101",
            "personal_number": "ABC123",
        }

        _, line2 = MRTD.encodeMRZ()

        self.assertEqual(line2[20], "F")

    """Test if short fields are padded correctly with fillers or zeros"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_short_fields_are_padded(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "U",
            "last_name": "LEE",
            "given_name": "AN",
            "passport_number": "12",
            "country_code": "U",
            "birth_date": "1",
            "sex": "F",
            "expiration_date": "2",
            "personal_number": "XYZ",
        }

        line1, line2 = MRTD.encodeMRZ()

        self.assertEqual(line1[:5], "P<U<<")
        self.assertEqual(line2[:9], "12<<<<<<<")
        self.assertEqual(line2[10:13], "U<<")
        self.assertEqual(line2[13:19], "100000")
        self.assertEqual(line2[21:27], "200000")
        self.assertEqual(line2[28:43], "XYZ<<<<<<<<<<<<")

    """Test if overly long fields are truncated to MRZ field limits"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_long_fields_are_truncated(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "ABCDE",
            "last_name": "VERYLONGSURNAME",
            "given_name": "ALPHA BETA GAMMA DELTA EPSILON",
            "passport_number": "123456789999",
            "country_code": "ABCDE",
            "birth_date": "90010199",
            "sex": "M",
            "expiration_date": "30010199",
            "personal_number": "12345678901234567890",
        }

        line1, line2 = MRTD.encodeMRZ()

        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertEqual(line1[:5], "P<ABC")
        self.assertEqual(line2[:9], "123456789")
        self.assertEqual(line2[10:13], "ABC")
        self.assertEqual(line2[13:19], "900101")
        self.assertEqual(line2[21:27], "300101")
        self.assertEqual(line2[28:43], "123456789012345")

    """Test if spaces in given names are converted to '<' in line 1"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_given_name_spaces_become_fillers(self, mock_db):
        mock_db.return_value = {
            "issuing_country": "USA",
            "last_name": "DOE",
            "given_name": "JANE ANN",
            "passport_number": "123456789",
            "country_code": "USA",
            "birth_date": "900101",
            "sex": "F",
            "expiration_date": "300101",
            "personal_number": "ABC123",
        }

        line1, _ = MRTD.encodeMRZ()

        self.assertIn("DOE<<JANE<ANN", line1)

    """Test if missing keys use default fallback values instead of crashing"""
    @patch("MRTD.getFromDB")
    def test_encodeMRZ_missing_optional_keys_use_defaults(self, mock_db):
        mock_db.return_value = {
            "last_name": "DOE",
            "given_name": "JOHN",
        }

        line1, line2 = MRTD.encodeMRZ()

        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertEqual(line1[:2], "P<")
        self.assertEqual(line2[20], "<")

"""Unit tests for reporting mismatches"""
class TestReportMismatches(unittest.TestCase):

    """Test if an empty mismatch list is returned when all check digits are valid"""
    def test_report_mismatches_none(self):
        decoded = {
            "check_digits": {
                "passport_number": {"extracted": 4, "computed": 4, "valid": True},
                "birth_date": {"extracted": 6, "computed": 6, "valid": True},
            }
        }

        result = MRTD.reportMismatches(decoded)

        self.assertEqual(result, [])

    """Test if one mismatch is reported correctly"""
    def test_report_mismatches_single(self):
        decoded = {
            "check_digits": {
                "passport_number": {"extracted": 1, "computed": 4, "valid": False},
                "birth_date": {"extracted": 6, "computed": 6, "valid": True},
            }
        }

        result = MRTD.reportMismatches(decoded)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["field"], "passport_number")
        self.assertEqual(result[0]["extracted_check_digit"], 1)
        self.assertEqual(result[0]["computed_check_digit"], 4)

    """Test if multiple mismatches are all collected and returned"""
    def test_report_mismatches_multiple(self):
        decoded = {
            "check_digits": {
                "passport_number": {"extracted": 1, "computed": 4, "valid": False},
                "birth_date": {"extracted": 2, "computed": 6, "valid": False},
                "expiration_date": {"extracted": 2, "computed": 2, "valid": True},
            }
        }

        result = MRTD.reportMismatches(decoded)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["field"], "passport_number")
        self.assertEqual(result[1]["field"], "birth_date")

    """Test if missing check_digits key returns an empty list instead of crashing"""
    def test_report_mismatches_missing_check_digits_key(self):
        decoded = {}

        result = MRTD.reportMismatches(decoded)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
    