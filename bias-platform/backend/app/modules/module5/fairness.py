import numpy as np
import pandas as pd
from typing import List


def compute_sample_weights(df: pd.DataFrame, y: pd.Series, bias_columns: List[str]) -> np.ndarray:
    """
    Compute sample weights for fairness-aware training.
    
    Weight formula: weight = 1 / P(Y | B)
    where P(Y | B) = count(B, Y) / count(B)
    
    Args:
        df: DataFrame with bias columns
        y: Target labels (pandas Series)
        bias_columns: List of column names representing bias attributes
        
    Returns:
        numpy array of shape (n_samples,) with weights
    """
    n_samples = len(df)
    
    # Edge case: empty bias_columns -> uniform weights
    if not bias_columns:
        return np.ones(n_samples)
    
    # Validate bias_columns exist in df
    valid_bias_columns = [col for col in bias_columns if col in df.columns]
    if not valid_bias_columns:
        return np.ones(n_samples)
    
    # Combine df and y into a single dataframe
    combined_df = df[valid_bias_columns].copy()
    combined_df['_target_'] = y.values
    
    # Compute counts using groupby
    # count(B, Y) - number of samples with specific (bias_group, label) combination
    # count(B) - number of samples with specific bias_group
    
    # Group by bias columns and target to get count(B, Y)
    bias_target_counts = combined_df.groupby(valid_bias_columns + ['_target_']).size()
    
    # Group by bias columns only to get count(B)
    bias_counts = combined_df.groupby(valid_bias_columns).size()
    
    # Compute P(Y|B) = count(B, Y) / count(B)
    # Map each (bias_group, label) pair to its probability
    probabilities = {}
    for key, count_b_y in bias_target_counts.items():
        # key structure depends on number of bias columns
        # Single column: key = (value, label)
        # Multiple columns: key = (val1, val2, ..., label)
        if len(valid_bias_columns) == 1:
            bias_key = (key[0],)
            label = key[1]
        else:
            bias_key = key[:-1]
            label = key[-1]
        
        # Get count(B) - need to handle both Series and scalar cases
        count_b = bias_counts.get(bias_key)
        if count_b is not None and count_b > 0:
            probabilities[(bias_key, label)] = count_b_y / count_b
    
    # Compute weights for each row
    weights = np.zeros(n_samples)
    
    for idx in range(n_samples):
        # Get bias group for this row
        bias_values = tuple(df.iloc[idx][col] for col in valid_bias_columns)
        label = y.iloc[idx]
        
        # Look up probability P(Y|B)
        prob = probabilities.get((bias_values, label), None)
        
        if prob is not None and prob > 0:
            weights[idx] = 1.0 / prob
        else:
            # Default weight for unknown groups
            weights[idx] = 1.0
    
    # Normalize weights (divide by mean weight)
    mean_weight = weights.mean()
    if mean_weight > 0:
        weights = weights / mean_weight
    
    return weights


def compute_fairness_metrics(df, y_true, y_pred, bias_columns):
    y_true_series = pd.Series(y_true, index=df.index)
    y_pred_series = pd.Series(y_pred, index=df.index)

    labels = pd.Index(y_true_series).append(pd.Index(y_pred_series)).dropna().unique()
    if len(labels) > 2:
        return {}

    if len(labels) == 0:
        return {}

    positive_label = 1 if 1 in set(labels) else labels[-1]
    fairness_metrics = {}

    for column in bias_columns:
        if column not in df.columns:
            continue

        column_metrics = {}
        grouped = df.groupby(column)

        for subgroup_value, subgroup_df in grouped:
            subgroup_indices = subgroup_df.index
            if len(subgroup_indices) == 0:
                continue

            y_true_group = y_true_series.loc[subgroup_indices]
            y_pred_group = y_pred_series.loc[subgroup_indices]
            if len(y_true_group) == 0:
                continue

            total_group = len(y_pred_group)
            predicted_positive = (y_pred_group == positive_label).sum()
            demographic_parity = predicted_positive / total_group if total_group > 0 else 0.0

            true_positive = ((y_true_group == positive_label) & (y_pred_group == positive_label)).sum()
            false_negative = ((y_true_group == positive_label) & (y_pred_group != positive_label)).sum()
            positive_true_total = true_positive + false_negative
            equal_opportunity = true_positive / positive_true_total if positive_true_total > 0 else 0.0

            column_metrics[subgroup_value] = {
                "demographic_parity": demographic_parity,
                "equal_opportunity": equal_opportunity,
            }

        fairness_metrics[column] = column_metrics

    return fairness_metrics


def validate_debiasing(before_metrics: dict, after_metrics: dict) -> dict:
    """
    Compare fairness metrics before and after debiasing.
    
    Args:
        before_metrics: Dictionary containing fairness metrics before debiasing
        after_metrics: Dictionary containing fairness metrics after debiasing
        
    Returns:
        Dictionary with:
            - bias_reduction: Dictionary showing reduction in bias gaps
            - fairness_improvement: Dictionary showing improvement in fairness metrics
    """
    bias_reduction = {}
    fairness_improvement = {}
    
    # Get all bias columns from both metrics
    all_columns = set()
    if isinstance(before_metrics, dict):
        all_columns.update(before_metrics.keys())
    if isinstance(after_metrics, dict):
        all_columns.update(after_metrics.keys())
    
    for column in all_columns:
        before_column = before_metrics.get(column, {}) if isinstance(before_metrics, dict) else {}
        after_column = after_metrics.get(column, {}) if isinstance(after_metrics, dict) else {}
        
        if not isinstance(before_column, dict) or not isinstance(after_column, dict):
            continue
        
        # Get all subgroups from both metrics
        all_subgroups = set()
        all_subgroups.update(before_column.keys())
        all_subgroups.update(after_column.keys())
        
        column_bias_reduction = {}
        column_fairness_improvement = {}
        
        for metric_name in ["demographic_parity", "equal_opportunity"]:
            subgroup_values = []
            before_values = []
            after_values = []
            
            for subgroup in all_subgroups:
                before_subgroup = before_column.get(subgroup, {}) if isinstance(before_column, dict) else {}
                after_subgroup = after_column.get(subgroup, {}) if isinstance(after_column, dict) else {}
                
                if isinstance(before_subgroup, dict) and isinstance(after_subgroup, dict):
                    before_val = before_subgroup.get(metric_name)
                    after_val = after_subgroup.get(metric_name)
                    
                    if before_val is not None and after_val is not None:
                        subgroup_values.append(subgroup)
                        before_values.append(before_val)
                        after_values.append(after_val)
            
            # Compute bias gap (max - min) for each set
            if before_values and after_values:
                before_gap = max(before_values) - min(before_values) if len(before_values) > 1 else 0.0
                after_gap = max(after_values) - min(after_values) if len(after_values) > 1 else 0.0
                
                # Bias reduction: positive means gap decreased
                bias_gap_reduction = before_gap - after_gap
                column_bias_reduction[metric_name] = round(float(bias_gap_reduction), 6)
                
                # Fairness improvement: average of improvements
                improvements = [b - a for b, a in zip(before_values, after_values)]
                avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
                column_fairness_improvement[metric_name] = round(float(avg_improvement), 6)
        
        if column_bias_reduction:
            bias_reduction[column] = column_bias_reduction
        if column_fairness_improvement:
            fairness_improvement[column] = column_fairness_improvement
    
    return {
        "bias_reduction": bias_reduction,
        "fairness_improvement": fairness_improvement
    }
