from sklearn.metrics import accuracy_score, f1_score
import math

from app.modules.module5.bias_gap import compute_bias_gap
from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module5.intersectional import compute_intersectional_metrics
from app.modules.module5.subgroup import compute_subgroup_metrics


def run_module5(df, y_true, y_pred, bias_columns):

    # ---------------- GLOBAL METRICS ---------------- #
    try:
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        if math.isnan(accuracy):
            accuracy = 0.0
        if math.isnan(f1):
            f1 = 0.0
    except Exception:
        accuracy = None
        f1 = None

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
        "bias_gap": 0.0,
        "groups": {},
    }

    dp_values = []
    eo_values = []

    if isinstance(fairness_metrics, dict):
        for column_payload in fairness_metrics.values():
            if not isinstance(column_payload, dict):
                continue

            column_groups = column_payload.get("groups", {})
            if not isinstance(column_groups, dict):
                continue

            for group, metric_values in column_groups.items():
                dp = metric_values.get("demographic_parity")
                eo = metric_values.get("equal_opportunity")

                if isinstance(dp, (int, float)):
                    dp_values.append(dp)
                    summary["groups"][str(group)] = round(dp, 6)

                if isinstance(eo, (int, float)):
                    eo_values.append(eo)

    if dp_values:
        summary["demographic_parity"] = round(sum(dp_values) / len(dp_values), 6)

    if eo_values:
        summary["equal_opportunity"] = round(sum(eo_values) / len(eo_values), 6)

    gap_values = [
        val
        for col in bias_gaps.values()
        for val in col.values()
        if isinstance(val, (int, float))
    ]

    if gap_values:
        summary["bias_gap"] = round(max(gap_values), 6)

    return {
        "accuracy": accuracy,
        "f1": f1,
        "num_fairness_metrics": len(fairness_metrics) if isinstance(fairness_metrics, dict) else 0,
        "subgroup_metrics": subgroup_metrics,
        "bias_gaps": bias_gaps,
        "intersectional": intersectional,
        "fairness_metrics": fairness_metrics,
        "summary": summary,
    }