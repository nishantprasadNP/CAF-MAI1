import numpy as np
import pandas as pd

from app.modules.module5.fairness import (
    compute_sample_weights,
    compute_fairness_metrics,
    validate_debiasing,
)
from app.modules.module4.preprocess import resample_dataset
from app.modules.module4.train import train_with_weights


def run_module6(df, X_train, y_train, bias_columns, module5_results):
    """
    Orchestrate Module 6 debiasing pipeline.
    
    This function coordinates the debiasing workflow by:
    1. Computing fairness-aware sample weights
    2. Training a weighted model
    3. Resampling the dataset
    4. Training on resampled data
    5. Comparing fairness metrics before and after
    
    Args:
        df: DataFrame with bias columns
        X_train: Training features
        y_train: Training labels
        bias_columns: List of bias column names
        module5_results: Results from Module 5 (before debiasing)
        
    Returns:
        Dictionary containing:
            - weights_summary: Statistics of computed weights
            - reweighted_results: Results from weighted model training
            - resampled_results: Results from resampled model training
            - debiasing_effect: Validation comparing before and after metrics
    """
    # Step 1: Compute fairness-aware sample weights
    weights = compute_sample_weights(df, y_train, bias_columns)
    
    # Step 2: Train weighted model
    weighted_output = train_with_weights(X_train, y_train, weights)
    
    # Step 3: Resample dataset
    X_res, y_res = resample_dataset(X_train, y_train)
    
    # Step 4: Train model on resampled data (uniform weights)
    resampled_output = train_with_weights(
        X_res, y_res, np.ones(len(y_res))
    )
    
    # Step 5: Recompute fairness metrics using new predictions.
    # After the train.py fix, predictions are a plain list at the top level.
    new_fairness_metrics = compute_fairness_metrics(
        df=df,
        y_true=y_train,
        y_pred=pd.Series(weighted_output["predictions"], index=df.index),
        bias_columns=bias_columns,
    )
    
    # Step 6: Compare before and after debiasing
    # Extract fairness_metrics from module5_results if available
    before_metrics = {}
    if isinstance(module5_results, dict):
        before_metrics = module5_results.get("fairness_metrics", {})
    
    validation = validate_debiasing(
        before_metrics,
        new_fairness_metrics
    )
    
    # Step 7: Return orchestration results.
    # Exclude '_runtime' keys (sklearn pipeline objects) so the dict is JSON-safe.
    def _strip(d):
        return {k: v for k, v in d.items() if k != "_runtime"}

    return {
        "weights_summary": {
            "min": float(weights.min()),
            "max": float(weights.max()),
            "mean": float(weights.mean()),  
        },
        "reweighted_results": _strip(weighted_output),
        "resampled_results": _strip(resampled_output),
        "debiasing_effect": validation,
    }