from app.modules.module7.encoder import encode_context
from app.modules.module7.injector import apply_context


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
    bias_score = sum(abs(a - b) for a, b in zip(probabilities, adjusted)) / len(adjusted)
    impact = _classify_bias_impact(bias_score)

    return {
        "original_probabilities": probabilities,
        "adjusted_probabilities": adjusted,
        "bias_score": bias_score,
        "impact": impact,
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
