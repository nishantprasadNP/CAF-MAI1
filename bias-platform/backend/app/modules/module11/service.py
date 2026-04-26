from collections import Counter
import math
from typing import Any

import pandas as pd
from app.utils.gemini_client import generate_explanation

# safer history
_BIAS_HISTORY: list[float] = []


# ---------------- PSI (DATA DRIFT) ---------------- #

def _psi(expected: pd.Series, actual: pd.Series) -> float:
    expected = expected.dropna()
    actual = actual.dropna()

    if expected.empty or actual.empty:
        return 0.0

    try:
        bins = min(10, max(2, int(expected.nunique())))
        exp_bins = pd.cut(expected, bins=bins, duplicates="drop")
        act_bins = pd.cut(actual, bins=exp_bins.cat.categories)

        exp_dist = exp_bins.value_counts(normalize=True).sort_index()
        act_dist = act_bins.value_counts(normalize=True).sort_index()

        idx = exp_dist.index.union(act_dist.index)
        exp_dist = exp_dist.reindex(idx, fill_value=1e-6)
        act_dist = act_dist.reindex(idx, fill_value=1e-6)

        psi_value = (
            (act_dist - exp_dist)
            * (act_dist / exp_dist).map(lambda x: math.log(x) if x > 0 else 0)
        ).sum()

        return float(psi_value)

    except Exception:
        return 0.0


# ---------------- BIAS EXTRACTION (FIXED) ---------------- #

def _extract_current_bias(fairness_output: dict) -> float:
    """
    Prefer summary bias_gap (correct source).
    Fallback to bias_gaps if needed.
    """
    try:
        summary = fairness_output.get("summary", {})
        bias = summary.get("bias_gap")

        if isinstance(bias, (int, float)):
            return float(bias)
    except Exception:
        pass

    # fallback (older structure)
    current_bias = 0.0
    for column_gaps in fairness_output.get("bias_gaps", {}).values():
        if isinstance(column_gaps, dict):
            for val in column_gaps.values():
                if isinstance(val, (int, float)):
                    current_bias = max(current_bias, float(val))

    return current_bias


# ---------------- MAIN ---------------- #

def run_monitoring(
    *,
    df: pd.DataFrame,
    fairness_output: dict[str, Any],
    decision_output: dict[str, Any],
    bias_columns: list[str],
) -> dict[str, Any]:

    # ---------------- DATA DRIFT ---------------- #
    numeric_cols = [
        c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
    ]

    if numeric_cols and len(df) > 10:
        col = numeric_cols[0]
        half = len(df) // 2
        data_drift = _psi(df[col].iloc[:half], df[col].iloc[half:])
    else:
        data_drift = 0.0

    # ---------------- BIAS DRIFT ---------------- #
    current_bias = _extract_current_bias(fairness_output)

    previous_bias = _BIAS_HISTORY[-1] if _BIAS_HISTORY else 0.0

    # maintain bounded history
    if len(_BIAS_HISTORY) >= 20:
        _BIAS_HISTORY.pop(0)

    _BIAS_HISTORY.append(current_bias)

    bias_drift = abs(current_bias - previous_bias)

    # ---------------- ALERTS ---------------- #
    alerts: list[str] = []

    if data_drift > 0.15:
        alerts.append("Data distribution is shifting significantly")

    if bias_drift > 0.2:
        alerts.append("Bias is increasing across runs")

    if decision_output.get("decision") == "approve" and bias_columns:
        col = bias_columns[0]

        if col in df.columns:
            counts = Counter(df[col].astype(str).tolist())

            if counts:
                dominant_group, dominant_count = counts.most_common(1)[0]

                if dominant_count / max(1, len(df)) > 0.7:
                    alerts.append(
                        f"Model favors dominant group: {col}={dominant_group}"
                    )

    if not alerts:
        alerts = ["System stable — no anomalies detected"]

    # ---------------- EXPLANATION ---------------- #
    drift_explanation = None

    if bias_drift > 0.1:
        prompt = f"""
        Bias drift detected: {bias_drift}

        Explain what this means and why it matters in simple terms.
        """

        drift_explanation = generate_explanation(prompt)

        if drift_explanation == "Explanation unavailable":
            drift_explanation = (
                "Bias drift indicates change in fairness behavior over time."
            )

    # ---------------- FINAL ---------------- #
    return {
        "data_drift": round(float(data_drift), 4),
        "bias_drift": round(float(bias_drift), 4),
        "previous_bias": round(float(previous_bias), 4),
        "current_bias": round(float(current_bias), 4),
        "alerts": alerts,
        "driftExplanation": drift_explanation
        or "System operating within normal conditions",
    }