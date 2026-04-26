from app.modules.module7.encoder import encode_context
from app.modules.module7.injector import apply_context
from app.utils.gemini_client import generate_explanation


def _classify_bias_impact(bias_score: float) -> str:
    if bias_score <= 0.05:
        return "negligible"
    if bias_score <= 0.15:
        return "low"
    if bias_score <= 0.30:
        return "moderate"
    return "high"


class ContextService:
    def __init__(self):
        self._context = {}

    def set_context(self, context: dict):
        self._context = context

    def get_context(self) -> dict:
        return self._context

    def apply_context_to_predictions(self, probabilities: list[float]) -> dict:
        context = self.get_context()
        weights = encode_context(context)
        adjusted_probs = apply_context(probabilities, weights)
        return {
            "original_probabilities": probabilities,
            "adjusted_probabilities": adjusted_probs,
            "context_weights": weights,
        }


context_service = ContextService()


def _safe_probability(probs: list[float], preferred_idx: int = 1) -> float:
    if not probs:
        return 0.0
    idx = preferred_idx if len(probs) > preferred_idx else len(probs) - 1
    try:
        return float(probs[idx])
    except Exception:
        return 0.0


def compute_context_impact(
    *,
    base_probs: list[float],
    context_probs: list[float],
    dominant_feature: str = "context",
) -> dict:
    base_bias = _safe_probability(base_probs)
    context_bias = _safe_probability(context_probs)
    context_delta = context_bias - base_bias
    cbas = context_bias - base_bias

    magnitude = abs(context_delta)
    if magnitude > 0.2:
        confidence = "high"
    elif magnitude > 0.05:
        confidence = "medium"
    else:
        confidence = "low"

    fallback_reason = f"{dominant_feature} increased prediction by {round(context_delta, 2)}"
    context_dict = context_service.get_context() or {}
    prompt = f"""
Model prediction changed from {base_bias} to {context_bias}.
Context: {context_dict}

Explain WHY this change happened in simple, human-readable terms.
Focus on cause-effect reasoning.
"""
    explanation = generate_explanation(prompt)
    reason = explanation if explanation != "Explanation unavailable" else fallback_reason

    return {
        "base_probability": base_probs,
        "final_probability": context_probs,
        "impact": float(context_delta),
        "cbas": float(cbas),
        "confidence": confidence,
        "reason": reason,
    }


def compute_context_weight(context: dict) -> float:
    weights = {
        "resource_level": {"low": 0.8, "medium": 1.0, "high": 1.1},
        "hospital_type": {"rural": 0.9, "urban": 1.1, "government": 0.95, "private": 1.05},
        "region": {"rural": 0.9, "urban": 1.1},
        "time_of_day": {"night": 0.95, "day": 1.02},
    }
    scalar = 1.0
    for key, mapping in weights.items():
        value = str(context.get(key, "")).lower()
        if value == "unknown":
            scalar *= 1.0
            continue
        if value in mapping:
            scalar *= float(mapping[value])
    return scalar


def apply_context_probabilities(probabilities: list[float], context: dict) -> list[float]:
    if not probabilities:
        return []
    scalar = compute_context_weight(context)
    scaled = [max(0.0, min(1.0, p * scalar)) for p in probabilities]
    total = sum(scaled)
    if total <= 0:
        return [1.0 / len(probabilities) for _ in probabilities]
    return [p / total for p in scaled]


def calculate_bias_score(probabilities: list[float]) -> dict:
    context = context_service.get_context()
    if not probabilities:
        return {
            "original_probabilities": [],
            "adjusted_probabilities": [],
            "bias_score": 0.0,
            "impact": "none" if not context else "negligible",
            "details": "No input probabilities provided",
        }

    if not context:
        return {
            "original_probabilities": probabilities,
            "adjusted_probabilities": probabilities,
            "bias_score": 0.0,
            "impact": "none",
            "details": "No context was set, so predictions were unchanged",
        }

    result = context_service.apply_context_to_predictions(probabilities)
    adjusted = result["adjusted_probabilities"]
    context_impact = compute_context_impact(
        base_probs=probabilities,
        context_probs=adjusted,
        dominant_feature="context",
    )
    bias_score = sum(abs(a - b) for a, b in zip(probabilities, adjusted)) / len(adjusted)
    bias_impact = _classify_bias_impact(bias_score)

    return {
        "original_probabilities": probabilities,
        "adjusted_probabilities": adjusted,
        "bias_score": bias_score,
        "impact": bias_impact,
        "context_delta": float(context_impact["impact"]),
        "cbas": float(context_impact["cbas"]),
        "confidence": context_impact["confidence"],
        "reason": context_impact["reason"],
        "details": "Context altered prediction confidence",
    }


def context_confidence(context: dict) -> str:
    if not context:
        return "low"
    unknown_count = 0
    valid_count = 0
    for key in ("region", "hospital_type", "resource_level", "time_of_day"):
        value = str(context.get(key, "")).strip().lower()
        if not value or value == "unknown":
            unknown_count += 1
        else:
            valid_count += 1
    if valid_count >= 3:
        return "high"
    if valid_count >= 2 and unknown_count <= 1:
        return "moderate"
    return "low"
