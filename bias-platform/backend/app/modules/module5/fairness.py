import pandas as pd
import numpy as np


# ---------------- SAMPLE WEIGHTS ---------------- #

def compute_sample_weights(df, y, bias_columns):
    """
    Compute fairness-aware sample weights.
    weight = 1 / P(Y | B)
    """

    n_samples = len(df)

    if not bias_columns:
        return np.ones(n_samples)

    valid_cols = [col for col in bias_columns if col in df.columns]
    if not valid_cols:
        return np.ones(n_samples)

    combined = df[valid_cols].copy()
    combined["_target_"] = y.values

    bias_target_counts = combined.groupby(valid_cols + ["_target_"]).size()
    bias_counts = combined.groupby(valid_cols).size()

    probabilities = {}

    for key, count_b_y in bias_target_counts.items():
        if len(valid_cols) == 1:
            bias_key = (key[0],)
            label = key[1]
        else:
            bias_key = key[:-1]
            label = key[-1]

        count_b = bias_counts.get(bias_key)

        if count_b and count_b > 0:
            probabilities[(bias_key, label)] = count_b_y / count_b

    weights = np.zeros(n_samples)

    for i in range(n_samples):
        bias_vals = tuple(df.iloc[i][col] for col in valid_cols)
        label = y.iloc[i]

        prob = probabilities.get((bias_vals, label))

        weights[i] = 1.0 / prob if prob and prob > 0 else 1.0

    mean_w = weights.mean()
    return weights / mean_w if mean_w > 0 else weights


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

    for column in bias_columns:
        if column not in df.columns:
            continue

        column_metrics = {}
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

            true_positive = ((y_true_group == positive_label) & (y_pred_group == positive_label)).sum()
            false_negative = ((y_true_group == positive_label) & (y_pred_group != positive_label)).sum()

            denom = true_positive + false_negative
            equal_opportunity = true_positive / denom if denom > 0 else 0.0

            column_metrics[str(subgroup_value)] = {
                "demographic_parity": float(demographic_parity),
                "equal_opportunity": float(equal_opportunity),
            }

        if column_metrics:
            fairness_metrics[column] = column_metrics

    return fairness_metrics


# ---------------- DEBIASING VALIDATION ---------------- #

def validate_debiasing(original_probs, debiased_probs):
    """
    Check if debiasing actually changed probabilities.
    """

    if not original_probs or not debiased_probs:
        return {
            "changed": False,
            "avg_shift": 0.0,
            "reason": "missing probabilities"
        }

    if len(original_probs) != len(debiased_probs):
        return {
            "changed": False,
            "avg_shift": 0.0,
            "reason": "length mismatch"
        }

    try:
        # 🔥 FIX: convert to float
        original_probs = [float(p) for p in original_probs]
        debiased_probs = [float(p) for p in debiased_probs]
    except Exception:
        return {
            "changed": False,
            "avg_shift": 0.0,
            "reason": "invalid probability format"
        }

    diffs = [abs(a - b) for a, b in zip(original_probs, debiased_probs)]
    avg_shift = sum(diffs) / len(diffs) if diffs else 0.0

    if avg_shift < 0.01:
        return {
            "changed": False,
            "avg_shift": avg_shift,
            "reason": "no significant change detected"
        }

    return {
        "changed": True,
        "avg_shift": avg_shift,
        "reason": "debiasing altered probabilities"
    }