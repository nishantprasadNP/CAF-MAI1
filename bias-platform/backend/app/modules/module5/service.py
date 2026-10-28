import math

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from app.modules.module5.bias_gap import compute_bias_gap
from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module5.intersectional import compute_intersectional_metrics
from app.modules.module5.subgroup import compute_subgroup_metrics
from app.utils.gemini_client import generate_explanation

# Shared by every stage that labels a bias gap (decision, monitoring, UI).
BIAS_LEVEL_THRESHOLDS = {"moderate": 0.1, "high": 0.2}


def _safe_float(x):
    try:
        val = float(x)
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val
    except Exception:
        return 0.0


def classify_bias(bias_gap: float) -> str:
    if bias_gap >= BIAS_LEVEL_THRESHOLDS["high"]:
        return "high"
    if bias_gap >= BIAS_LEVEL_THRESHOLDS["moderate"]:
        return "moderate"
    return "low"


def _interpret_bias(bias_gap: float) -> dict:
    level = classify_bias(bias_gap)
    messages = {
        "low": "Model is fairly balanced",
        "moderate": "Some disparity detected across groups",
        "high": "Significant bias detected across subgroups",
    }
    return {"bias_level": level, "message": messages[level]}


def max_bias_gap(bias_gaps: dict) -> float:
    gaps = [
        float(col["gap"])
        for col in bias_gaps.values()
        if isinstance(col, dict) and isinstance(col.get("gap"), (int, float))
    ]
    return round(max(gaps), 4) if gaps else 0.0


def compute_bias_gap_only(df, y_pred, bias_columns) -> float:
    """Bias gap for a set of predictions without the full metric suite."""
    subgroup_metrics = compute_subgroup_metrics(df=df, y_true=None, y_pred=y_pred, bias_columns=bias_columns)
    return max_bias_gap(compute_bias_gap(subgroup_metrics=subgroup_metrics))


def generate_ai_insight(summary):
    prompt = f"""
    Analyze fairness of a binary classification model:

    Bias Gap (max difference in positive-prediction rate between groups): {summary.get("bias_gap")}
    Average Demographic Parity: {summary.get("demographic_parity")}
    Average Equal Opportunity: {summary.get("equal_opportunity")}

    Give a short 2-line explanation of fairness issues.
    """
    explanation = generate_explanation(prompt)
    return None if explanation == "Explanation unavailable" else explanation


# ---------------- MAIN ---------------- #

def run_module5(df, y_true, y_pred, bias_columns, explain: bool = False):

    # ---------------- GLOBAL METRICS ---------------- #
    try:
        accuracy = _safe_float(accuracy_score(y_true, y_pred))
        f1 = _safe_float(f1_score(y_true, y_pred, zero_division=0))
    except Exception:
        accuracy = 0.0
        f1 = 0.0

    # ---------------- SUBGROUP ---------------- #
    subgroup_metrics = compute_subgroup_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- BIAS GAP ---------------- #
    bias_gaps = compute_bias_gap(subgroup_metrics=subgroup_metrics)

    # ---------------- INTERSECTIONAL ---------------- #
    intersectional = compute_intersectional_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- FAIRNESS ---------------- #
    fairness_metrics = compute_fairness_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- SUMMARY ---------------- #
    summary = {
        "demographic_parity": 0.0,
        "equal_opportunity": 0.0,
        "bias_gap": max_bias_gap(bias_gaps),
        "groups": {},
    }

    dp_values = []
    eo_values = []

    if isinstance(fairness_metrics, dict):
        for column, column_payload in fairness_metrics.items():
            if not isinstance(column_payload, dict):
                continue

            column_groups = column_payload.get("groups", {})
            for group, metric_values in column_groups.items():

                dp = metric_values.get("demographic_parity")
                eo = metric_values.get("equal_opportunity")

                if isinstance(dp, (int, float)):
                    dp_values.append(dp)
                    summary["groups"][f"{column}={group}"] = round(dp, 4)

                if isinstance(eo, (int, float)):
                    eo_values.append(eo)

    if dp_values:
        summary["demographic_parity"] = round(sum(dp_values) / len(dp_values), 4)

    if eo_values:
        summary["equal_opportunity"] = round(sum(eo_values) / len(eo_values), 4)

    # ---------------- GLOBAL CONFUSION MATRIX ---------------- #
    try:
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        global_cm = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    except Exception:
        global_cm = {"tn": 0, "fp": 0, "fn": 0, "tp": 0}

    # ---------------- OUTCOME DISTRIBUTION ---------------- #
    y_true_counts = pd.Series(y_true).value_counts().to_dict()
    y_pred_counts = pd.Series(y_pred).value_counts().to_dict()
    outcome_distribution = {
        "actual": {str(k): int(v) for k, v in y_true_counts.items()},
        "predicted": {str(k): int(v) for k, v in y_pred_counts.items()},
    }

    # ---------------- INTERPRETATION ---------------- #
    insight = _interpret_bias(summary["bias_gap"])
    insight["ai_explanation"] = generate_ai_insight(summary) if explain else None

    return {
        "accuracy": accuracy,
        "f1": f1,
        "evaluated_rows": int(len(df)),
        # Demographic parity, equal opportunity, equalized odds, predictive parity per attribute.
        "num_fairness_metrics": 4 * sum(1 for v in fairness_metrics.values() if isinstance(v, dict) and "groups" in v),
        "subgroup_metrics": subgroup_metrics,
        "bias_gaps": bias_gaps,
        "intersectional": intersectional,
        "fairness_metrics": fairness_metrics,
        "summary": summary,
        "insight": insight,
        "global_confusion_matrix": global_cm,
        "outcome_distribution": outcome_distribution,
    }
