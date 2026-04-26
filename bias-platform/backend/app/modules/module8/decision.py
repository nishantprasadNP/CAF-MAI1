from typing import Any
from app.utils.gemini_client import generate_explanation as generate_gemini_explanation


# ---------------- DECISION ---------------- #

def make_decision(probabilities: list[float]) -> dict[str, Any]:
    if not probabilities:
        return {"label": -1, "confidence": 0.5}

    label = int(max(range(len(probabilities)), key=lambda i: probabilities[i]))
    confidence = float(probabilities[label])

    # 🔥 FIX: normalize confidence
    if confidence < 0.5:
        confidence = 1 - confidence

    return {"label": label, "confidence": round(confidence, 3)}


# ---------------- BIAS FLAG ---------------- #

def _get_bias_flag(fairness_output: dict) -> float:
    bias_gaps = fairness_output.get("bias_gaps", {}) if isinstance(fairness_output, dict) else {}

    max_gap = 0.0
    for col in bias_gaps.values():
        if isinstance(col, dict):
            for val in col.values():
                if isinstance(val, (int, float)):
                    max_gap = max(max_gap, float(val))

    if max_gap > 0.2:
        return "high", max_gap
    elif max_gap > 0.08:
        return "moderate", max_gap
    return "low", max_gap


# ---------------- FEATURE EXTRACTION ---------------- #

def _get_top_features(top_features: dict) -> list:
    if not top_features:
        return [
            {"feature": "bias_score", "impact": 0.2},
            {"feature": "model_output", "impact": 0.1},
        ]

    sorted_features = sorted(
        top_features.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]

    return [
        {"feature": str(name), "impact": round(float(score), 3)}
        for name, score in sorted_features
    ]


# ---------------- MAIN ---------------- #

def run_module8(
    *,
    probabilities: list[float],
    original_probabilities: list[float],
    fairness_output: dict[str, Any],
    top_features: dict[str, float] | None = None,
) -> dict[str, Any]:

    probabilities = probabilities or [0.5, 0.5]
    original_probabilities = original_probabilities or probabilities
    top_features = top_features or {}

    # ---------------- DECISION ---------------- #
    decision = make_decision(probabilities)

    # ---------------- BIAS ---------------- #
    bias_flag, max_gap = _get_bias_flag(fairness_output)

    # ---------------- FEATURES ---------------- #
    top_features_list = _get_top_features(top_features)

    # ---------------- CONTRIBUTIONS ---------------- #
    feature_score = sum(abs(f["impact"]) for f in top_features_list)
    bias_score = max_gap

    total = feature_score + bias_score + 1e-6

    feature_contribution = feature_score / total
    bias_contribution = bias_score / total

    # ---------------- EXPLANATION ---------------- #
    summary_text = (
        f"Model predicts {'APPROVE' if decision['label'] == 1 else 'REJECT'} "
        f"with confidence {decision['confidence']:.2f}. "
        f"Bias risk is {bias_flag}."
    )

    # 🔥 Gemini (single call only)
    gemini_prompt = f"""
    Decision: {"approve" if decision['label'] == 1 else "reject"}
    Confidence: {decision['confidence']}
    Bias Gap: {max_gap}

    Top Features: {top_features_list}

    Explain why this decision was made in simple terms.
    """

    ai_explanation = generate_gemini_explanation(gemini_prompt)
    if ai_explanation == "Explanation unavailable":
        ai_explanation = summary_text

    # ---------------- FINAL ---------------- #
    return {
        "decision": "approve" if decision["label"] == 1 else "reject",
        "label": decision["label"],
        "confidence": decision["confidence"],

        "bias_flag": bias_flag,
        "biasContribution": round(float(max_gap), 4),

        "top_features": top_features_list,
        "featureContribution": round(feature_contribution, 4),

        "explanation": summary_text,
        "ai_explanation": ai_explanation,

        "probabilities": probabilities,
        "original_probabilities": original_probabilities,
    }