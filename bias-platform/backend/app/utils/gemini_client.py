from app.config import GEMINI_API_KEY

try:
    import google.generativeai as genai
except Exception:
    genai = None

_FALLBACK_EXPLANATION = "Explanation unavailable"
_MODEL = None

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _MODEL = genai.GenerativeModel("models/gemini-2.5-flash")
    except Exception:
        _MODEL = None


def generate_explanation(prompt: str) -> str:
    """Generate short explanation using Gemini (safe, no crashes)."""

    clean_prompt = str(prompt or "").strip()

    if not clean_prompt or _MODEL is None:
        return _FALLBACK_EXPLANATION

    try:
        formatted_prompt = f"Explain briefly: {clean_prompt}"

        response = _MODEL.generate_content(formatted_prompt)
        text = (getattr(response, "text", "") or "").strip()

        if len(text) > 250:
            text = text[:250]

        return text or _FALLBACK_EXPLANATION

    except Exception:
        return _FALLBACK_EXPLANATION