import numpy as np
import pandas as pd

from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module4.preprocess import resample_dataset
from app.modules.module4.train import train_with_weights


# ---------------- UTILS ---------------- #

def _normalize_probs(probs):
    try:
        probs = [float(p) for p in probs]
    except Exception:
        return [0.5, 0.5]

    total = sum(probs)
    if total <= 0:
        return [0.5, 0.5]

    return [p / total for p in probs]


def _ensure_two_class_probs(p):
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        return _normalize_probs(p)

    try:
        p1 = float(p)
        return [1 - p1, p1]
    except Exception:
        return [0.5, 0.5]


# ---------------- MAIN ---------------- #

def run_module6(df, X_train, y_train, bias_columns, module5_results):

    print("\n[MODULE 6 START]")

    summary = module5_results.get("summary", {})
    bias_gap = float(summary.get("bias_gap", 0.0))

    print("Bias Gap:", bias_gap)

    if bias_gap < 0.03:
        return {
            "status": "skipped",
            "reason": "low bias gap",
            "debiasing_effect": {
                "before": round(bias_gap, 4),
                "after": round(bias_gap, 4),
                "improvement": 0.0,
                "changed": False,
            },
        }

    # ---------------- STEP 1: TRAIN ---------------- #
    weighted_output = train_with_weights(X_train, y_train, np.ones(len(y_train)))
    all_probs = weighted_output.get("probabilities", [])

    # ---------------- STEP 2: GLOBAL RATE ---------------- #
    base_preds = []
    prob_list = []

    for p in all_probs:
        probs = _ensure_two_class_probs(p)
        p1 = probs[1]

        prob_list.append(p1)
        base_preds.append(1 if p1 >= 0.5 else 0)

    global_rate = sum(base_preds) / max(len(base_preds), 1)

    # ---------------- STEP 3: GROUP RATES ---------------- #
    group_rates = {}
    bias_col = bias_columns[0] if bias_columns else None

    if bias_col and bias_col in df.columns:
        df_temp = df.copy()
        df_temp["_pred"] = base_preds

        for group, gdf in df_temp.groupby(bias_col):
            rate = gdf["_pred"].mean()
            group_rates[group] = rate

    print("[M6] Group rates:", group_rates)

    # ---------------- STEP 4: ADAPTIVE THRESHOLDS ---------------- #
    debiased_predictions = []
    debiased_probs = []

    for i, p1 in enumerate(prob_list):

        if bias_col and bias_col in df.columns:
            group = df.iloc[i][bias_col]
            group_rate = group_rates.get(group, global_rate)

            # 🔥 ADAPTIVE SHIFT
            delta = global_rate - group_rate

            # stronger adjustment if bias is large
            threshold = 0.5 - (delta * 0.5)

            # clamp threshold
            threshold = max(0.3, min(0.7, threshold))
        else:
            threshold = 0.5

        pred = 1 if p1 >= threshold else 0

        debiased_predictions.append(pred)
        debiased_probs.append(p1)

    print("[M6] Sample preds:", debiased_predictions[:10])

    # ---------------- STEP 5: FAIRNESS AFTER ---------------- #
    try:
        after_metrics = compute_fairness_metrics(
            df=df,
            y_true=y_train,
            y_pred=pd.Series(debiased_predictions, index=df.index),
            bias_columns=bias_columns,
        )
        after_bias = float(after_metrics.get("summary", {}).get("bias_gap", bias_gap))
    except Exception as e:
        print("[M6 ERROR]:", e)
        after_bias = bias_gap

    # ---------------- STEP 6: IMPROVEMENT ---------------- #
    improvement = max(0.0, bias_gap - after_bias)
    changed = improvement > 0.01

    print("[M6] Before:", bias_gap, "After:", after_bias)

    # ---------------- OPTIONAL RESAMPLING ---------------- #
    X_res, y_res = resample_dataset(X_train, y_train)
    resampled_output = train_with_weights(X_res, y_res, np.ones(len(y_res)))

    # ---------------- FINAL ---------------- #
    return {
        "status": "applied",
        "reason": "adaptive debiasing applied",

        "reweighted_results": {
            "predictions": debiased_predictions,
            "probabilities": debiased_probs,
        },

        "resampled_results": {
            "predictions": resampled_output.get("predictions", []),
            "probabilities": [
                _ensure_two_class_probs(p)[1]
                for p in resampled_output.get("probabilities", [])
            ],
        },

        "debiasing_effect": {
            "before": round(bias_gap, 4),
            "after": round(after_bias, 4),
            "improvement": round(improvement, 4),
            "changed": changed,
        },
    }