from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def compute_subgroup_metrics(df, y_true, y_pred, bias_columns):
    labels = sorted(set(y_true.dropna().tolist()) | set(y_pred.dropna().tolist()))
    positive_label = 1 if 1 in labels else (labels[-1] if labels else 1)
    subgroup_metrics = {}

    for column in bias_columns:
        if column not in df.columns:
            continue

        column_metrics = {}
        grouped = df.groupby(column)

        for subgroup_value, subgroup_df in grouped:
            subgroup_indices = subgroup_df.index

            if len(subgroup_indices) == 0:
                continue

            y_true_group = y_true.loc[subgroup_indices]
            y_pred_group = y_pred.loc[subgroup_indices]

            if len(y_true_group) == 0:
                continue

            column_metrics[subgroup_value] = {
                "accuracy": accuracy_score(y_true_group, y_pred_group),
                "precision": precision_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
                "recall": recall_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
                "f1": f1_score(y_true_group, y_pred_group, pos_label=positive_label, zero_division=0),
            }

        subgroup_metrics[column] = column_metrics

    return subgroup_metrics
