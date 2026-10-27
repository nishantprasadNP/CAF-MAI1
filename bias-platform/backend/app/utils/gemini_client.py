import logging

from app.config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL, GEMINI_TIMEOUT_MS

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None

logger = logging.getLogger(__name__)

_FALLBACK_EXPLANATION = "Explanation unavailable"
_MAX_CHARS = 600
_CLIENT = None

if genai is not None and GEMINI_API_KEY:
    try:
        _CLIENT = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
    except Exception:
        logger.exception("Failed to initialise Gemini client")
        _CLIENT = None


def _trim(text: str) -> str:
    """Cap length at a sentence boundary instead of cutting mid-word."""
    if len(text) <= _MAX_CHARS:
        return text
    cut = text[:_MAX_CHARS]
    end = max(cut.rfind(". "), cut.rfind(".\n"))
    return cut[: end + 1] if end > 0 else cut.rsplit(" ", 1)[0] + "…"


def generate_explanation(prompt: str) -> str:
    """Generate short explanation using Gemini (safe, no crashes)."""

    clean_prompt = str(prompt or "").strip()

    if not clean_prompt or _CLIENT is None:
        return _FALLBACK_EXPLANATION

    # Fall back to a lighter model when the primary is overloaded or retired.
    for model in dict.fromkeys([GEMINI_MODEL, GEMINI_FALLBACK_MODEL]):
        try:
            response = _CLIENT.models.generate_content(
                model=model,
                contents=f"Explain briefly in at most 3 sentences, plain text: {clean_prompt}",
            )
            text = (getattr(response, "text", "") or "").strip()
            if text:
                return _trim(text)

        except Exception as e:
            logger.warning("Gemini request to %s failed: %s", model, str(e)[:200])

    return _FALLBACK_EXPLANATION
