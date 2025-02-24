import sys
import os

# Add project directory to Python path
project_path = '/home/tabish/web-scrapper'
if project_path not in sys.path:
    sys.path.append(project_path)

# Add src directory to Python path
src_path = os.path.join(project_path, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

# Create uploads directory
uploads_path = os.path.join(project_path, 'uploads')
os.makedirs(uploads_path, exist_ok=True)

from app import app as application
