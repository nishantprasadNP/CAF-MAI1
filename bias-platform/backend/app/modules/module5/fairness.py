import pandas as pd


# ---------------- FAIRNESS METRICS ---------------- #

def compute_fairness_metrics(df, y_true, y_pred, bias_columns):
    if not bias_columns:
        return {}

    y_true_series = pd.Series(y_true, index=df.index)
    y_pred_series = pd.Series(y_pred, index=df.index)

    labels = pd.Index(y_true_series).append(pd.Index(y_pred_series)).dropna().unique()

    # Only binary supported
    if len(labels) != 2:
        return {"note": "Fairness metrics require binary classification"}

    positive_label = 1 if 1 in labels else labels[-1]

    fairness_metrics = {}

    def _confusion_counts(y_true_group, y_pred_group):
        tp = int(((y_true_group == positive_label) & (y_pred_group == positive_label)).sum())
        fp = int(((y_true_group != positive_label) & (y_pred_group == positive_label)).sum())
        tn = int(((y_true_group != positive_label) & (y_pred_group != positive_label)).sum())
        fn = int(((y_true_group == positive_label) & (y_pred_group != positive_label)).sum())
        return tp, fp, tn, fn

    for column in bias_columns:
        if column not in df.columns:
            continue

        column_metrics = {}
        group_confusion_matrix = {}
        tpr_values = []
        fpr_values = []
        precision_values = []
        grouped = df.groupby(column)

        for subgroup_value, subgroup_df in grouped:
            idx = subgroup_df.index
            if len(idx) == 0:
                continue

            y_true_group = y_true_series.loc[idx]
            y_pred_group = y_pred_series.loc[idx]

            total = len(y_pred_group)
            predicted_positive = (y_pred_group == positive_label).sum()

            demographic_parity = predicted_positive / total if total > 0 else 0.0

            tp, fp, tn, fn = _confusion_counts(y_true_group, y_pred_group)
            tpr_denom = tp + fn
            fpr_denom = fp + tn
            precision_denom = tp + fp

            equal_opportunity = tp / tpr_denom if tpr_denom > 0 else 0.0
            fpr = fp / fpr_denom if fpr_denom > 0 else 0.0
            precision = tp / precision_denom if precision_denom > 0 else 0.0

            tpr_values.append(float(equal_opportunity))
            fpr_values.append(float(fpr))
            precision_values.append(float(precision))
            group_confusion_matrix[str(subgroup_value)] = {
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            }

            column_metrics[str(subgroup_value)] = {
                "demographic_parity": float(demographic_parity),
                "equal_opportunity": float(equal_opportunity),
                "equalized_odds": {
                    "tpr": float(equal_opportunity),
                    "fpr": float(fpr),
                },
                "predictive_parity": {
                    "precision": float(precision),
                },
                "confusion_matrix": group_confusion_matrix[str(subgroup_value)],
            }

        if column_metrics:
            fairness_metrics[column] = {
                "groups": column_metrics,
                "demographic_parity": {
                    "max_diff": float(max(column_metrics[g]["demographic_parity"] for g in column_metrics) - min(column_metrics[g]["demographic_parity"] for g in column_metrics))
                },
                "equalized_odds": {
                    "tpr_diff": float(max(tpr_values) - min(tpr_values)) if tpr_values else 0.0,
                    "fpr_diff": float(max(fpr_values) - min(fpr_values)) if fpr_values else 0.0,
                },
                "predictive_parity": {
                    "precision_diff": float(max(precision_values) - min(precision_values)) if precision_values else 0.0,
                },
                "group_confusion_matrix": group_confusion_matrix,
            }

    return fairness_metrics
