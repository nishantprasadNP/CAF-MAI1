import os
from pathlib import Path
from dotenv import load_dotenv


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=_BACKEND_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash")
# Gemini rejects deadlines under 10s.
GEMINI_TIMEOUT_MS = max(10000, int(os.getenv("GEMINI_TIMEOUT_MS", "10000")))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "1024"))

# Large datasets: train on a stratified sample; fairness is still measured on
# the full held-out split.
MAX_TRAIN_ROWS = int(os.getenv("MAX_TRAIN_ROWS", "500000"))
# A sensitive attribute needs a manageable number of groups (e.g. not an ID or a raw amount).
MAX_BIAS_GROUPS = int(os.getenv("MAX_BIAS_GROUPS", "50"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "10"))
