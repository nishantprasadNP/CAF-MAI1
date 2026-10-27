import math
from typing import Any

import pandas as pd
from app.modules.module5.service import classify_bias
from app.utils.gemini_client import generate_explanation

DATA_DRIFT_ALERT = 0.15
BIAS_DRIFT_ALERT = 0.1
MAX_HISTORY = 20
MIN_DRIFT_ROWS = 30


# ---------------- PSI (DATA DRIFT) ---------------- #

def _psi(expected: pd.Series, actual: pd.Series) -> float:
    expected = expected.dropna()
    actual = actual.dropna()

    if len(expected) < MIN_DRIFT_ROWS or len(actual) < MIN_DRIFT_ROWS:
        return 0.0

    try:
        # Equal-frequency bins from the reference data; ~20 rows per bin in
        # the smaller sample keeps PSI from being dominated by sampling noise.
        bins = min(10, max(2, int(expected.nunique())), max(2, len(actual) // 20))
        edges = expected.quantile([i / bins for i in range(1, bins)]).unique().tolist()
        edges = [-math.inf, *edges, math.inf]
        exp_bins = pd.cut(expected, bins=edges, duplicates="drop")
        act_bins = pd.cut(actual, bins=edges, duplicates="drop")

        exp_dist = exp_bins.value_counts(normalize=True).sort_index()
        act_dist = act_bins.value_counts(normalize=True).sort_index()

        idx = exp_dist.index.union(act_dist.index)
        exp_dist = exp_dist.reindex(idx, fill_value=1e-6).clip(lower=1e-6)
        act_dist = act_dist.reindex(idx, fill_value=1e-6).clip(lower=1e-6)

        psi_value = (
            (act_dist - exp_dist)
            * (act_dist / exp_dist).map(math.log)
        ).sum()

        return float(psi_value)

    except Exception:
        return 0.0


# ---------------- BIAS EXTRACTION ---------------- #

def _extract_current_bias(fairness_output: dict) -> float:
    bias = fairness_output.get("summary", {}).get("bias_gap")
    return float(bias) if isinstance(bias, (int, float)) else 0.0


def _favored_groups(fairness_output: dict) -> list[str]:
    """For each attribute with a non-low gap, name the highest/lowest positive-rate groups."""
    out = []
    for col, payload in fairness_output.get("bias_gaps", {}).items():
        rates = payload.get("group_rates", {})
        if len(rates) < 2 or classify_bias(payload.get("gap", 0.0)) == "low":
            continue
        top = max(rates, key=rates.get)
        bottom = min(rates, key=rates.get)
        out.append(
            f"Model favors {col}={top} ({rates[top]:.0%} positive) over "
            f"{col}={bottom} ({rates[bottom]:.0%} positive)"
        )
    return out


# ---------------- MAIN ---------------- #

def run_monitoring(
    *,
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    fairness_output: dict[str, Any],
    bias_history: list[float],
) -> dict[str, Any]:
    """
    reference_df / current_df: training split vs held-out split (data drift).
    bias_history: previous bias gaps for this dataset configuration; it is
    appended to in place.
    """

    # ---------------- DATA DRIFT ---------------- #
    numeric_cols = [
        c for c in reference_df.columns
        if pd.api.types.is_numeric_dtype(reference_df[c]) and c in current_df.columns
    ]
    drift_by_column = {
        c: round(_psi(reference_df[c], current_df[c]), 4) for c in numeric_cols
    }
    data_drift = max(drift_by_column.values()) if drift_by_column else 0.0

    # ---------------- BIAS DRIFT ---------------- #
    current_bias = _extract_current_bias(fairness_output)
    previous_bias = bias_history[-1] if bias_history else None

    if len(bias_history) >= MAX_HISTORY:
        bias_history.pop(0)
    bias_history.append(current_bias)

    if previous_bias is None:
        bias_drift = 0.0
        trend = "baseline"
    else:
        delta = current_bias - previous_bias
        bias_drift = abs(delta)
        if bias_drift < 0.01:
            trend = "stable"
        else:
            trend = "increasing" if delta > 0 else "decreasing"

    # ---------------- ALERTS ---------------- #
    alerts: list[str] = []

    if data_drift > DATA_DRIFT_ALERT:
        worst = max(drift_by_column, key=drift_by_column.get)
        alerts.append(f"Distribution of '{worst}' differs between training and evaluation data (PSI {data_drift:.2f})")

    if trend == "increasing" and bias_drift > BIAS_DRIFT_ALERT:
        alerts.append(f"Bias gap increased by {bias_drift:.2f} since the previous run")

    alerts.extend(_favored_groups(fairness_output))

    if not alerts:
        alerts = ["System stable — no anomalies detected"]

    # ---------------- EXPLANATION ---------------- #
    if previous_bias is None:
        drift_explanation = "First run for this dataset and attribute selection — this run is the baseline for bias drift."
    elif bias_drift > BIAS_DRIFT_ALERT:
        prompt = f"""
        The bias gap of a model changed from {previous_bias:.3f} to {current_bias:.3f} between runs.

        Explain what this means and why it matters in simple terms.
        """
        drift_explanation = generate_explanation(prompt)

        if drift_explanation == "Explanation unavailable":
            drift_explanation = (
                f"Bias gap moved from {previous_bias:.2f} to {current_bias:.2f}, "
                "indicating a change in fairness behavior between runs."
            )
    else:
        drift_explanation = "System operating within normal conditions"

    # ---------------- FINAL ---------------- #
    return {
        "data_drift": round(float(data_drift), 4),
        "data_drift_by_column": drift_by_column,
        "bias_drift": round(float(bias_drift), 4),
        "previous_bias": round(float(previous_bias), 4) if previous_bias is not None else None,
        "current_bias": round(float(current_bias), 4),
        "trend": trend,
        "runs_tracked": len(bias_history),
        "alerts": alerts,
        "driftExplanation": drift_explanation,
    }
