import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def compute_intersectional_metrics(df, y_true, y_pred, bias_columns):
    if not bias_columns:
        return {}

    y_true_series = pd.Series(y_true, index=df.index)
    y_pred_series = pd.Series(y_pred, index=df.index)
    labels = sorted(set(y_true_series.dropna().tolist()) | set(y_pred_series.dropna().tolist()))
    positive_label = 1 if 1 in labels else (labels[-1] if labels else 1)

    intersectional_metrics = {}
    grouped = df.groupby(bias_columns)

    for group_key, group_df in grouped:
        group_indices = group_df.index
        if len(group_indices) == 0:
            continue

        y_true_group = y_true_series.loc[group_indices]
        y_pred_group = y_pred_series.loc[group_indices]
        if len(y_true_group) == 0:
            continue

        if isinstance(group_key, tuple):
            group_name = "|".join(str(value) for value in group_key)
        else:
            group_name = str(group_key)

        intersectional_metrics[group_name] = {
            "accuracy": accuracy_score(y_true_group, y_pred_group),
            "precision": precision_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
            "recall": recall_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
            "f1": f1_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
        }

    return intersectional_metrics
