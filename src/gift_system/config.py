from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("GS_ENV", "dev").lower()
IS_PROD = ENV == "prod"

# Persistent storage directory
BASE_DIR = Path(os.getenv("GS_BASE_DIR", str(Path.cwd() / ".gs-project_internal"))).expanduser()
BASE_DIR.mkdir(parents=True, exist_ok=True)

# SQLite Database path
DB_FILE = BASE_DIR / "gift_system.db"

# Cryptographic key salt
SECRET_SALT = os.getenv("GS_KEY_SALT", "gift-system-secret-salt-2026")

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
APP_URL = os.getenv("APP_URL", "https://end-year-cdn.vercel.app")
