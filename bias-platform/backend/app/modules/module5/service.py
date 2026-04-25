from app.modules.module5.bias_gap import compute_bias_gap
from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module5.intersectional import compute_intersectional_metrics
from app.modules.module5.subgroup import compute_subgroup_metrics


def run_module5(df, y_true, y_pred, bias_columns):
    subgroup_metrics = compute_subgroup_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )
    bias_gaps = compute_bias_gap(subgroup_metrics=subgroup_metrics)
    intersectional = compute_intersectional_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )
    fairness_metrics = compute_fairness_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    summary = {
        "demographic_parity": 0.0,
        "equal_opportunity": 0.0,
        "bias_gap": 0.0,
        "groups": {},
    }
    if fairness_metrics:
        dp_values = []
        eo_values = []
        for column_groups in fairness_metrics.values():
            if not isinstance(column_groups, dict):
                continue
            for group, metric_values in column_groups.items():
                if not isinstance(metric_values, dict):
                    continue
                dp = metric_values.get("demographic_parity")
                eo = metric_values.get("equal_opportunity")
                if isinstance(dp, (int, float)):
                    dp_values.append(float(dp))
                    summary["groups"][str(group)] = round(float(dp), 6)
                if isinstance(eo, (int, float)):
                    eo_values.append(float(eo))
        if dp_values:
            summary["demographic_parity"] = round(sum(dp_values) / len(dp_values), 6)
        if eo_values:
            summary["equal_opportunity"] = round(sum(eo_values) / len(eo_values), 6)

    gap_candidates = []
    for column_gaps in bias_gaps.values():
        if not isinstance(column_gaps, dict):
            continue
        for gap_value in column_gaps.values():
            if isinstance(gap_value, (int, float)):
                gap_candidates.append(float(gap_value))
    if gap_candidates:
        summary["bias_gap"] = round(max(gap_candidates), 6)

    return {
        "subgroup_metrics": subgroup_metrics,
        "bias_gaps": bias_gaps,
        "intersectional": intersectional,
        "fairness_metrics": fairness_metrics,
        "summary": summary,
    }
