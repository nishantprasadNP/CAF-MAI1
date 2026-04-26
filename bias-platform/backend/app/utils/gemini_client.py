from app.config import GEMINI_API_KEY

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None

_FALLBACK_EXPLANATION = "Explanation unavailable"
_MODEL = None

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _MODEL = genai.GenerativeModel("gemini-pro")
    except Exception:
        _MODEL = None


def generate_explanation(prompt: str) -> str:
    """Generate a short natural-language explanation using Gemini.

    The function never raises and always returns a string fallback when
    configuration, import, or API calls fail.
    """
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt or _MODEL is None:
        return _FALLBACK_EXPLANATION

    try:
        response = _MODEL.generate_content(clean_prompt)
        text = (getattr(response, "text", "") or "").strip()
        return text or _FALLBACK_EXPLANATION
    except Exception:
        return _FALLBACK_EXPLANATION
