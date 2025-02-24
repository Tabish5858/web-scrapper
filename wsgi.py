import sys
import os

# Add your project directory to Python path
path = '/home/tabish/flask-web-scraper'
if path not in sys.path:
    sys.path.append(path)

from src.app import app as application
