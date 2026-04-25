from typing import Any


def _confidence_bucket(value: float) -> str:
    if value < 0.15:
        return "low"
    if value < 0.35:
        return "medium"
    return "high"


def make_decision(probabilities: list[float]) -> dict[str, Any]:
    if not probabilities:
        return {"label": -1, "confidence": 0.0}
    label = int(max(range(len(probabilities)), key=lambda i: probabilities[i]))
    confidence = float(probabilities[label])
    return {"label": label, "confidence": confidence}


def generate_explanation(
    *,
    decision_label: int,
    confidence: float,
    bias_flag: str,
    context_influence: str,
    top_features: list[str] | None = None,
) -> str:
    features_text = (
        f"Top features influencing this outcome: {', '.join(top_features[:3])}. "
        if top_features
        else ""
    )
    return (
        f"Prediction resolved to class {decision_label} with confidence {confidence:.2f}. "
        f"Bias impact is {bias_flag} and context influence is {context_influence}. "
        f"{features_text}"
    ).strip()


def run_module8(
    *,
    probabilities: list[float],
    original_probabilities: list[float],
    fairness_output: dict[str, Any],
    top_features: list[str] | None = None,
) -> dict[str, Any]:
    decision = make_decision(probabilities)
    bias_gaps = fairness_output.get("bias_gaps", {}) if isinstance(fairness_output, dict) else {}
    max_gap = 0.0
    for column_gaps in bias_gaps.values():
        if isinstance(column_gaps, dict):
            for value in column_gaps.values():
                if isinstance(value, (int, float)):
                    max_gap = max(max_gap, float(value))
    if max_gap > 0.2:
        bias_flag = "high"
    elif max_gap > 0.08:
        bias_flag = "moderate"
    else:
        bias_flag = "low"

    if probabilities and original_probabilities and len(probabilities) == len(original_probabilities):
        shift = sum(abs(a - b) for a, b in zip(probabilities, original_probabilities)) / len(probabilities)
    else:
        shift = 0.0
    context_influence = _confidence_bucket(shift)

    explanation_text = generate_explanation(
        decision_label=decision["label"],
        confidence=decision["confidence"],
        bias_flag=bias_flag,
        context_influence=context_influence,
        top_features=top_features or [],
    )

    direction_features = []
    for idx, name in enumerate((top_features or [])[:5]):
        impact_raw = 0.12 - (idx * 0.03)
        signed = impact_raw if decision["label"] == 1 else -impact_raw
        direction_features.append(
            {
                "feature": str(name),
                "impact": f"{signed:+.2f}",
            }
        )

    context_score = min(0.3, max(0.0, shift))
    bias_score = min(0.3, max(0.0, max_gap))
    feature_score = max(0.0, 1.0 - context_score - bias_score)

    explanation_structured = {
        "summary": (
            f"Model predicts {'APPROVE' if decision['label'] == 1 else 'REJECT'} "
            f"due to strong influence of {direction_features[0]['feature'] if direction_features else 'key features'} "
            f"and {bias_flag} bias risk."
        ),
        "top_features": direction_features,
        "contributions": {
            "feature": round(float(feature_score), 4),
            "context": round(float(context_score), 4),
            "bias": round(float(bias_score), 4),
        },
    }

    return {
        "decision": "approve" if decision["label"] == 1 else "reject",
        "label": decision["label"],
        "confidence": decision["confidence"],
        "bias_flag": bias_flag,
        "context_influence": context_influence,
        "explanation": explanation_text,
        "explanation_structured": explanation_structured,
        "feature_importance": {item["feature"]: item["impact"] for item in direction_features},
        "probabilities": probabilities,
        "original_probabilities": original_probabilities,
    }
