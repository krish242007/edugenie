import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file from project root (override existing env if updated)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# Gemini Configuration (Clean whitespaces and optional surrounding quotes)
raw_key = os.getenv("GEMINI_API_KEY", "").strip()
if (raw_key.startswith('"') and raw_key.endswith('"')) or (raw_key.startswith("'") and raw_key.endswith("'")):
    raw_key = raw_key[1:-1].strip()
GEMINI_API_KEY = raw_key

# Model Selection - Default to active stable model (e.g. gemini-3.5-flash, gemini-3.7-flash)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
if (GEMINI_MODEL.startswith('"') and GEMINI_MODEL.endswith('"')) or (GEMINI_MODEL.startswith("'") and GEMINI_MODEL.endswith("'")):
    GEMINI_MODEL = GEMINI_MODEL[1:-1].strip()

# Resilience & Timeouts
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").strip().lower() in ("1", "true", "yes")

# Input Limits for Safety & Sanitization
MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "1000"))
MAX_TOPIC_LENGTH = int(os.getenv("MAX_TOPIC_LENGTH", "300"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "20000"))
MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "20"))


def is_gemini_configured() -> bool:
    """Check if a valid non-placeholder Gemini API key is configured."""
    return bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_gemini_api_key"))


def refresh_config():
    """Reload environment variables if .env was changed at runtime."""
    global GEMINI_API_KEY, GEMINI_MODEL
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
    k = os.getenv("GEMINI_API_KEY", "").strip()
    if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
        k = k[1:-1].strip()
    GEMINI_API_KEY = k
    
    m = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    if (m.startswith('"') and m.endswith('"')) or (m.startswith("'") and m.endswith("'")):
        m = m[1:-1].strip()
    GEMINI_MODEL = m
