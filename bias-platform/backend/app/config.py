import os
from pathlib import Path
from dotenv import load_dotenv


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=_BACKEND_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
