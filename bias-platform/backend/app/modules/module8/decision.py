from typing import Any


def _confidence_bucket(value: float) -> str:
    if value < 0.05:
        return "low"
    if value < 0.15:
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
    top_feature: str,
) -> str:
    return (
        f"Model predicts {'APPROVE' if decision_label == 1 else 'REJECT'} "
        f"with confidence {confidence:.2f}. "
        f"Decision is primarily influenced by {top_feature}, "
        f"with {bias_flag} bias risk and {context_influence} context influence."
    )


def run_module8(
    *,
    probabilities: list[float],
    original_probabilities: list[float],
    fairness_output: dict[str, Any],
    top_features: dict[str, float] | None = None,
) -> dict[str, Any]:

    # ---------------- SAFETY ---------------- #
    probabilities = probabilities or [0.5, 0.5]
    original_probabilities = original_probabilities or probabilities
    top_features = top_features or {}

    # ---------------- DECISION ---------------- #
    decision = make_decision(probabilities)

    # ---------------- BIAS ---------------- #
    bias_gaps = fairness_output.get("bias_gaps", {}) if isinstance(fairness_output, dict) else {}

    max_gap = 0.0
    for col in bias_gaps.values():
        if isinstance(col, dict):
            for val in col.values():
                if isinstance(val, (int, float)):
                    max_gap = max(max_gap, float(val))

    if max_gap > 0.2:
        bias_flag = "high"
    elif max_gap > 0.08:
        bias_flag = "moderate"
    else:
        bias_flag = "low"

    # ---------------- CONTEXT SHIFT ---------------- #
    if len(probabilities) == len(original_probabilities):
        shift = sum(abs(a - b) for a, b in zip(probabilities, original_probabilities)) / len(probabilities)
        context_delta = probabilities[1] - original_probabilities[1] if len(probabilities) > 1 else 0.0
    else:
        shift = 0.0
        context_delta = 0.0

    context_influence = _confidence_bucket(shift)

    # ---------------- FEATURE IMPORTANCE (REAL) ---------------- #
    sorted_features = sorted(
        top_features.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]

    direction_features = []

    for name, value in sorted_features:
        signed = value if decision["label"] == 1 else -value
        direction_features.append({
            "feature": str(name),
            "impact": f"{signed:+.3f}",
        })

    top_feature_name = direction_features[0]["feature"] if direction_features else "key features"
    top_features_breakdown = [
        {"feature": str(name), "impact": float(score)}
        for name, score in sorted(top_features.items(), key=lambda x: -x[1])[:5]
    ]

    # ---------------- CONTRIBUTIONS ---------------- #
    feature_score_raw = sum(abs(v) for _, v in sorted_features)
    context_score_raw = shift
    bias_score_raw = max_gap

    total = feature_score_raw + context_score_raw + bias_score_raw + 1e-6

    feature_score = feature_score_raw / total
    context_score = context_score_raw / total
    bias_score = bias_score_raw / total

    # ---------------- EXPLANATION ---------------- #
    explanation_text = generate_explanation(
        decision_label=decision["label"],
        confidence=decision["confidence"],
        bias_flag=bias_flag,
        context_influence=context_influence,
        top_feature=top_feature_name,
    )

    explanation_structured = {
        "summary": explanation_text,
        "top_features": direction_features,
        "contributions": {
            "feature": round(feature_score, 4),
            "context": round(context_score, 4),
            "bias": round(bias_score, 4),
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
        "top_features": top_features_breakdown,
        "contextContribution": round(abs(context_delta), 6),
        "biasContribution": round(float(max_gap), 6),
        "context_delta": round(float(context_delta), 6),
        "feature_importance": {f["feature"]: f["impact"] for f in direction_features},
        "probabilities": probabilities,
        "original_probabilities": original_probabilities,
    }