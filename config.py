from dotenv import load_dotenv
from pathlib import Path
import os


load_dotenv()
ENV = os.getenv("GS_ENV", "dev")

BASE_DIR = Path.home() / ".gs-project_internal"
BASE_DIR.mkdir(exist_ok=True)

ASSIGN_FILE = BASE_DIR / "assignments.enc"
STATE_FILE = BASE_DIR / "state.log"
ADMIN_FILE = BASE_DIR / "admin.hash"

IS_PROD = ENV == "prod"
