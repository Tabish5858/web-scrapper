import unittest
from src.utils.scraper import scrape_website

class TestScraper(unittest.TestCase):

    def test_scrape_website_valid_url(self):
        url = "http://example.com"
        result = scrape_website(url)
        self.assertEqual(result["url"], url)
        self.assertNotEqual(result["company_name"], "N/A")
        self.assertNotEqual(result["email"], "N/A")
        self.assertNotEqual(result["phone_number"], "N/A")
        self.assertNotEqual(result["address"], "N/A")

    def test_scrape_website_invalid_url(self):
        url = "http://invalid-url"
        result = scrape_website(url)
        self.assertEqual(result["url"], url)
        self.assertIn("error", result)

    def test_scrape_website_empty_url(self):
        url = ""
        result = scrape_website(url)
        self.assertEqual(result["url"], url)
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
