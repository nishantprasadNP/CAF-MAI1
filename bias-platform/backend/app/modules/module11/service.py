from collections import Counter
import math
from typing import Any

import pandas as pd

_BIAS_HISTORY: list[float] = []


def _psi(expected: pd.Series, actual: pd.Series) -> float:
    expected = expected.dropna()
    actual = actual.dropna()
    if expected.empty or actual.empty:
        return 0.0
    bins = min(10, max(2, int(expected.nunique())))
    exp_bins = pd.cut(expected, bins=bins, duplicates="drop")
    act_bins = pd.cut(actual, bins=exp_bins.cat.categories)
    exp_dist = exp_bins.value_counts(normalize=True).sort_index()
    act_dist = act_bins.value_counts(normalize=True).sort_index()
    idx = exp_dist.index.union(act_dist.index)
    exp_dist = exp_dist.reindex(idx, fill_value=1e-6)
    act_dist = act_dist.reindex(idx, fill_value=1e-6)
    ratio = act_dist / exp_dist
    psi_value = ((act_dist - exp_dist) * ratio.map(lambda x: 0.0 if x <= 0 else math.log(x))).sum()
    try:
        return float(psi_value)
    except Exception:
        return 0.0


def run_monitoring(
    *,
    df: pd.DataFrame,
    fairness_output: dict[str, Any],
    decision_output: dict[str, Any],
    bias_columns: list[str],
) -> dict[str, Any]:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if numeric_cols and len(df) > 4:
        col = numeric_cols[0]
        half = len(df) // 2
        data_drift = _psi(df[col].iloc[:half], df[col].iloc[half:])
    else:
        data_drift = 0.0

    current_bias = 0.0
    for column_gaps in fairness_output.get("bias_gaps", {}).values():
        if isinstance(column_gaps, dict):
            current_bias = max(current_bias, *[float(v) for v in column_gaps.values() if isinstance(v, (int, float))], 0.0)
    previous_bias = float(_BIAS_HISTORY[-1]) if _BIAS_HISTORY else 0.0
    _BIAS_HISTORY.append(float(current_bias))
    bias_drift = float(_BIAS_HISTORY[-1] - previous_bias) if len(_BIAS_HISTORY) > 1 else 0.0

    alerts: list[str] = []
    if data_drift > 0.1:
        alerts.append("data drift increasing")
    if bias_drift > 0.1:
        alerts.append("bias increasing over time")

    if bias_columns and decision_output.get("decision") == "approve":
        counts = Counter(df[bias_columns[0]].astype(str).tolist()) if bias_columns[0] in df.columns else Counter()
        if counts:
            dominant_group, dominant_count = counts.most_common(1)[0]
            if dominant_count / max(1, len(df)) > 0.7:
                alerts.append(f"same group repeatedly advantaged: {bias_columns[0]}={dominant_group}")

    if not alerts:
        alerts = ["No anomalies detected"]

    return {
        "data_drift": float(data_drift),
        "previous_bias_drift": previous_bias,
        "current_bias_drift": float(current_bias),
        "bias_drift": float(bias_drift),
        "alerts": alerts,
    }
