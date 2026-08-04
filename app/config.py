"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _app_base_dir() -> Path:
    """Project root in dev; folder containing the .exe when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _app_base_dir()

# When packaged, Playwright browsers ship next to the .exe
if getattr(sys, "frozen", False):
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(BASE_DIR / "ms-playwright"),
    )

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tracker.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Email / SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
