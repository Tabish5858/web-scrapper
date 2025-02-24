# src/utils/scraper.py

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
from collections import deque

def is_same_domain(base_url, url_to_check):
    """Check if two URLs belong to the same domain."""
    base_domain = urlparse(base_url).netloc
    check_domain = urlparse(url_to_check).netloc
    return base_domain == check_domain

def scrape_website(url, callback=None, max_pages=5):
    """Scrape website for company information across multiple pages."""
    try:
        # Add https:// prefix if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        visited_urls = set()
        urls_to_visit = deque([url])
        company_data = {
            "url": url,
            "company_name": "N/A",
            "emails": set(),
            "phones": set(),
            "locations": set()
        }

        while urls_to_visit and len(visited_urls) < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls:
                continue

            try:
                print(f"Scraping page: {current_url}")
                response = requests.get(current_url, headers=headers, timeout=15, verify=False)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                visited_urls.add(current_url)

                # Extract company name if not already found
                if company_data["company_name"] == "N/A" and soup.title:
                    company_name = soup.title.string
                    if company_name:
                        company_name = company_name.strip().split('|')[0].strip()
                        company_name = company_name.split('-')[0].strip()
                        company_data["company_name"] = company_name

                # Extract emails
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                for link in soup.find_all('a', href=True):
                    if 'mailto:' in link['href'].lower():
                        email = link['href'].replace('mailto:', '').strip()
                        if re.match(email_pattern, email) and 'example' not in email.lower():
                            company_data["emails"].add(email)

                text_emails = re.findall(email_pattern, soup.text)
                company_data["emails"].update(e for e in text_emails if 'example' not in e.lower())

                # Extract phone numbers
                phone_pattern = r'''
                    (?:
                        (?:\+?1[-.]?)?\s*
                        (?:\([0-9]{3}\)|[0-9]{3})
                        [-.\s]?
                        [0-9]{3}
                        [-.\s]?
                        [0-9]{4}
                    )
                '''
                matches = re.findall(phone_pattern, soup.text, re.VERBOSE | re.MULTILINE)
                for match in matches:
                    clean_number = re.sub(r'[^\d]', '', match)
                    if len(clean_number) == 10:
                        formatted = f"({clean_number[:3]}) {clean_number[3:6]}-{clean_number[6:]}"
                        company_data["phones"].add(formatted)

                # Extract locations
                city_state_pattern = r'([\w\s.-]+?,\s*[A-Z]{2}(?:\s*\d{5})?)'
                locations = re.findall(city_state_pattern, soup.text)
                company_data["locations"].update(loc.strip() for loc in locations)

                # Find additional pages to scrape
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, link['href'])
                    if (is_same_domain(url, next_url) and
                        next_url not in visited_urls and
                        next_url not in urls_to_visit):
                        urls_to_visit.append(next_url)

                time.sleep(1)  # Be nice to servers

            except Exception as e:
                print(f"Error scraping {current_url}: {str(e)}")

        # Compile final results
        result = {
            "url": url,
            "company_name": company_data["company_name"],
            "email": next(iter(company_data["emails"]), "N/A"),
            "phone": next(iter(company_data["phones"]), "N/A"),
            "location": next(iter(company_data["locations"]), "N/A"),
            "all_emails": list(company_data["emails"]),
            "all_phones": list(company_data["phones"]),
            "all_locations": list(company_data["locations"]),
            "pages_scraped": len(visited_urls)
        }

        if callback:
            callback(result)

        return result

    except Exception as e:
        result = {
            "url": url,
            "company_name": "N/A",
            "email": "N/A",
            "phone": "N/A",
            "location": "N/A",
            "error": str(e),
            "pages_scraped": 0
        }
        if callback:
            callback(result)
        return result
