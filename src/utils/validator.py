import re
import pandas as pd

def is_valid_url(url):
    """Validate if the provided URL is well-formed."""
    # Add http:// prefix if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None

def validate_csv(file):
    """Validate the input CSV file and check for well-formed URLs."""
    try:
        # Validate file object
        if not file or not hasattr(file, 'read'):
            raise ValueError("Invalid file object")

        # Reset file pointer to beginning
        file.seek(0)

        # Read first few bytes to check if file is empty
        if len(file.read(1)) == 0:
            raise ValueError("The file is empty")

        # Reset pointer again for pandas to read
        file.seek(0)

        # Try to read the CSV file
        df = pd.read_csv(file)

        # Check if dataframe is empty
        if df.empty:
            raise ValueError("The CSV file contains no data")

        # Check for required column
        if 'Website' not in df.columns:
            raise ValueError("CSV must contain a 'Website' column")

        # Check for empty values in Website column
        if df['Website'].isnull().any():
            raise ValueError("Website column contains empty values")

        # Validate URLs
        invalid_urls = []
        for url in df['Website'].dropna():
            if not isinstance(url, str):
                invalid_urls.append(str(url))
            elif not is_valid_url(str(url).strip()):
                invalid_urls.append(url)

        if invalid_urls:
            raise ValueError(f"Invalid URLs found: {', '.join(invalid_urls)}")

        # Reset file pointer for subsequent reads
        file.seek(0)
        return True

    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded file is empty or not a valid CSV file")
    except pd.errors.ParserError:
        raise ValueError("The file is not a valid CSV format")
    except Exception as e:
        raise ValueError(f"Error validating CSV: {str(e)}")

    
