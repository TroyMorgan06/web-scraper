"""Application settings loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'tracker.db'

# Make data directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Email / SMTP
SMTP_HOST = os.getenv('SMTP_HOST', "smtp.gmail.com")
SMTP_PORT = int(os.getenv('SMTP_PORT', "587"))
SMTP_USER = os.getenv('SMTP_USER', "")
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', "")
ALERT_EMAIL = os.getenv('ALERT_EMAIL', "")

# Flask
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', "dev-secret-change-me")