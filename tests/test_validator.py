# filepath: /flask-web-scraper/flask-web-scraper/tests/test_validator.py
import unittest
from src.utils.validator import validate_csv, is_valid_url

class TestValidator(unittest.TestCase):

    def test_valid_url(self):
        self.assertTrue(is_valid_url("https://www.example.com"))
        self.assertTrue(is_valid_url("http://example.com"))
        self.assertFalse(is_valid_url("invalid-url"))
        self.assertFalse(is_valid_url("ftp://example.com"))

    def test_validate_csv(self):
        valid_csv_path = "tests/valid_urls.csv"  # Path to a valid CSV file for testing
        invalid_csv_path = "tests/invalid_urls.csv"  # Path to an invalid CSV file for testing

        self.assertTrue(validate_csv(valid_csv_path))
        self.assertFalse(validate_csv(invalid_csv_path))

if __name__ == "__main__":
    unittest.main()