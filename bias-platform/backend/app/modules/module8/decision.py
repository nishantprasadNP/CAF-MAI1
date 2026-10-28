from typing import Any
from app.modules.module5.service import classify_bias, max_bias_gap
from app.utils.gemini_client import generate_explanation as generate_gemini_explanation
from app.utils.gemini_client import is_configured as gemini_configured


# ---------------- DECISION ---------------- #

def make_decision(probabilities: list[float]) -> dict[str, Any]:
    if not probabilities:
        return {"label": -1, "confidence": 0.5}

    label = int(max(range(len(probabilities)), key=lambda i: probabilities[i]))
    confidence = float(probabilities[label])

    return {"label": label, "confidence": round(confidence, 3)}


# ---------------- BIAS FLAG ---------------- #

def _get_bias_flag(fairness_output: dict) -> tuple[str, float]:
    if not isinstance(fairness_output, dict):
        return "low", 0.0

    gap = fairness_output.get("summary", {}).get("bias_gap")
    if not isinstance(gap, (int, float)):
        gap = max_bias_gap(fairness_output.get("bias_gaps", {}))

    return classify_bias(float(gap)), float(gap)


# ---------------- FEATURE EXTRACTION ---------------- #

def _get_top_features(top_features: dict) -> list:
    """
    Top 5 features by absolute model coefficient; empty if none are available.
    """

    if not top_features:
        return []

    sorted_features = sorted(
        top_features.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]

    return [
        {"feature": str(name), "impact": round(float(score), 3)}
        for name, score in sorted_features
    ]


# ---------------- HUMAN EXPLANATION ---------------- #

def _build_feature_explanation(top_features_list: list, positive_outcome: str) -> str:
    if not top_features_list:
        return "No dominant features identified."

    parts = []
    for f in top_features_list[:3]:
        direction = "raises" if f["impact"] > 0 else "lowers"
        parts.append(
            f"{f['feature']} ({direction} the odds of {positive_outcome}, coefficient {f['impact']:+.2f})"
        )

    return "Key factors: " + ", ".join(parts)


# ---------------- MAIN ---------------- #

def run_module8(
    *,
    probabilities: list[float],
    original_probabilities: list[float],
    fairness_output: dict[str, Any],
    top_features: dict[str, float] | None = None,
    target_column: str = "outcome",
    class_labels: dict[str, str] | None = None,
) -> dict[str, Any]:

    probabilities = probabilities or [0.5, 0.5]
    original_probabilities = original_probabilities or probabilities
    top_features = top_features or {}
    class_labels = class_labels or {"0": "0", "1": "1"}

    # ---------------- DECISION ---------------- #
    decision = make_decision(probabilities)

    # ---------------- BIAS ---------------- #
    bias_flag, max_gap = _get_bias_flag(fairness_output)

    # ---------------- FEATURES ---------------- #
    top_features_list = _get_top_features(top_features)

    # ---------------- EXPLANATION ---------------- #

    # Word everything in terms of the dataset's own target, not approve/reject.
    predicted = f"{target_column} = {class_labels.get(str(decision['label']), decision['label'])}"
    positive_outcome = f"{target_column} = {class_labels.get('1', '1')}"

    feature_expl = _build_feature_explanation(top_features_list, positive_outcome)

    summary_text = (
        f"Prediction: {predicted} "
        f"(confidence {decision['confidence']:.2f}). "
        f"{feature_expl.rstrip('.')}. "
        f"Bias risk: {bias_flag}."
    )

    # ---------------- GEMINI ---------------- #

    feature_lines = "\n".join(
        f"    - {f['feature']}: coefficient {f['impact']:+.3f}" for f in top_features_list
    ) or "    (none)"
    gemini_prompt = f"""
    A logistic-regression model predicts "{target_column}".
    Positive outcome: {positive_outcome}. Prediction for this record: {predicted}
    (confidence {decision['confidence']}).
    Bias gap between groups of the sensitive attribute: {max_gap} (risk: {bias_flag}).

    Top features with model coefficients:
{feature_lines}
    A POSITIVE coefficient means higher values of that feature RAISE the odds of
    {positive_outcome}; a NEGATIVE coefficient means they LOWER those odds. These
    are global coefficients, not values for this particular record.

    Explain what drove this prediction and whether the bias gap is concerning.
    Use the outcome names above; do not describe it as approval or rejection.
    Do not contradict the coefficient signs.
    """

    ai_explanation = generate_gemini_explanation(gemini_prompt)

    # No fallback copy here: the rule-based summary is already in "explanation".
    if ai_explanation == "Explanation unavailable":
        ai_explanation = None
    ai_status = "ok" if ai_explanation else ("unavailable" if gemini_configured() else "not_configured")

    # ---------------- FINAL ---------------- #

    return {
        "decision": "approve" if decision["label"] == 1 else "reject",
        "label": decision["label"],
        "confidence": decision["confidence"],

        "bias_flag": bias_flag,
        "bias_gap": round(float(max_gap), 4),

        "top_features": top_features_list,

        "explanation": summary_text,
        "ai_explanation": ai_explanation,
        "ai_status": ai_status,

        "probabilities": probabilities,
        "original_probabilities": original_probabilities,
    }