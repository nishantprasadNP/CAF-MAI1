"""
Module 6: bias mitigation.

Two standard, auditable steps, both fitted on the training split only:

1. Reweighing (Kamiran & Calders): each training row gets weight
   P(group) * P(label) / P(group, label), so group and label look independent
   to the learner.
2. Group-specific decision thresholds: per protected group, the threshold is
   chosen so that the group's positive-prediction rate on the training split
   matches the overall rate (demographic-parity post-processing).

The pipeline evaluates the result on the held-out test split.
"""

import logging

import numpy as np
import pandas as pd

from app.modules.module4.train import train_with_weights
from app.modules.module5.service import compute_bias_gap_only

logger = logging.getLogger(__name__)

MIN_BIAS_GAP = 0.03
MIN_GROUP_SIZE = 5
THRESHOLD_BOUNDS = (0.05, 0.95)


# ---------------- UTILS ---------------- #

def _group_keys(df: pd.DataFrame, bias_columns: list[str]) -> pd.Series:
    cols = [c for c in bias_columns if c in df.columns]
    if not cols:
        return pd.Series(["all"] * len(df), index=df.index)
    keys = df[cols[0]].astype(str)
    for col in cols[1:]:
        keys = keys + "|" + df[col].astype(str)
    return keys


def compute_reweighing_weights(groups: pd.Series, y: pd.Series) -> np.ndarray:
    frame = pd.DataFrame({"g": np.asarray(groups), "y": np.asarray(y)})
    n = len(frame)

    p_group = frame["g"].map(frame["g"].value_counts(normalize=True))
    p_label = frame["y"].map(frame["y"].value_counts(normalize=True))
    p_joint = frame.groupby(["g", "y"])["y"].transform("size") / n

    weights = (p_group * p_label / p_joint).to_numpy(dtype=float)
    return weights / weights.mean()


def _fit_group_thresholds(probs: np.ndarray, groups: pd.Series) -> dict[str, float]:
    target_rate = float((probs >= 0.5).mean())
    if target_rate in (0.0, 1.0):
        return {}

    thresholds = {}
    for g in groups.unique():
        group_probs = probs[(groups == g).to_numpy()]
        if len(group_probs) < MIN_GROUP_SIZE:
            continue
        t = float(np.quantile(group_probs, 1 - target_rate))
        thresholds[str(g)] = float(np.clip(t, *THRESHOLD_BOUNDS))
    return thresholds


def apply_debiasing(runtime: dict, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (predictions, adjusted positive-class probabilities) for df.

    The adjusted probability moves each row's log-odds by the group threshold's
    log-odds, so adjusted >= 0.5 exactly when the raw probability clears its
    group threshold, without pinning values at 0 or 1.
    """
    probs = runtime["model"].predict_proba(df)[:, 1]
    groups = _group_keys(df, runtime["bias_columns"])
    thresholds = groups.map(runtime["thresholds"]).fillna(0.5).to_numpy(dtype=float)

    eps = 1e-6
    p = np.clip(probs, eps, 1 - eps)
    logit = np.log(p / (1 - p)) - np.log(thresholds / (1 - thresholds))
    adjusted = 1 / (1 + np.exp(-logit))
    predictions = (probs >= thresholds).astype(int)
    return predictions, adjusted


# ---------------- MAIN ---------------- #

def run_module6(X_train, y_train, bias_columns, module5_results):

    summary = module5_results.get("summary", {})
    bias_gap = float(summary.get("bias_gap", 0.0))

    logger.info("Module 6: bias gap before mitigation = %.4f", bias_gap)

    if not bias_columns or bias_gap < MIN_BIAS_GAP:
        return {
            "status": "skipped",
            "reason": f"bias gap {bias_gap:.4f} is below the {MIN_BIAS_GAP} mitigation threshold",
        }

    groups = _group_keys(X_train, bias_columns)

    # ---------------- STEP 1: REWEIGHED TRAINING ---------------- #
    weights = compute_reweighing_weights(groups, y_train)
    model = train_with_weights(X_train, y_train, weights)

    # ---------------- STEP 2: GROUP THRESHOLDS (train split) ---------------- #
    train_probs = model.predict_proba(X_train)[:, 1]
    thresholds = _fit_group_thresholds(train_probs, groups.reset_index(drop=True))

    runtime = {"model": model, "thresholds": thresholds, "bias_columns": bias_columns}

    train_preds, _ = apply_debiasing(runtime, X_train)
    train_gap_after = compute_bias_gap_only(X_train, pd.Series(train_preds), bias_columns)

    logger.info("Module 6: group thresholds = %s", thresholds)

    return {
        "_runtime": runtime,
        "status": "applied",
        "reason": "reweighing + group-specific decision thresholds (fitted on training split)",
        "group_thresholds": {g: round(t, 4) for g, t in thresholds.items()},
        "train_bias_gap_after": train_gap_after,
    }
