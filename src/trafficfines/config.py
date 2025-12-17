# config.py
import os
from pathlib import Path

# Get project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database configuration
DATABASE_PATH = str(PROJECT_ROOT / 'traffic_fines.db')

# Google Calendar API configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = str(PROJECT_ROOT / 'credentials.json')
TOKEN_FILE = str(PROJECT_ROOT / 'token.pickle')

# PDF scanning configuration
DEFAULT_PDF_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'multas')

# Logging configuration
LOG_FILE = str(PROJECT_ROOT / 'app.log')

