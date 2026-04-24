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

    return {
        "subgroup_metrics": subgroup_metrics,
        "bias_gaps": bias_gaps,
        "intersectional": intersectional,
        "fairness_metrics": fairness_metrics,
    }
