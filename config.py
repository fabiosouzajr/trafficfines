# config.py
import os

# Database configuration
DATABASE_PATH = 'traffic_fines.db'

# Google Calendar API configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# PDF scanning configuration
DEFAULT_PDF_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'multas')
