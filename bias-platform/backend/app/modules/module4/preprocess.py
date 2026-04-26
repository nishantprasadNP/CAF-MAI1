from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(x_df: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric_cols = x_df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [col for col in x_df.columns if col not in numeric_cols]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            # Force categorical columns to a uniform string dtype so sklearn
            # encoders never receive mixed float/str values.
            ("to_string", FunctionTransformer(lambda data: pd.DataFrame(data).astype(str), validate=False)),
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_cols),
            ("categorical", categorical_pipeline, categorical_cols),
        ]
    )
    return preprocessor, numeric_cols, categorical_cols


def sanitize_dataset(dataset: dict[str, Any]) -> tuple[pd.DataFrame, pd.Series]:
    x = dataset.get("X", [])
    y = dataset.get("Y", [])
    if not x or not y:
        raise ValueError("Dataset must include non-empty X and Y.")

    x_df = pd.DataFrame(x)
    y_series = pd.Series(y)
    if len(x_df) != len(y_series):
        raise ValueError("Length mismatch: X and Y must have same number of rows.")
    return x_df, y_series


def resample_dataset(X, y):
    """
    Resample dataset to reduce class imbalance using SMOTE or manual oversampling.
    
    Args:
        X: Features (DataFrame or array-like)
        y: Labels (Series or array-like)
        
    Returns:
        Tuple of (X_resampled, y_resampled) with balanced classes
    """
    import numpy as np
    import pandas as pd
    
    # Convert to numpy arrays for consistent handling
    if hasattr(X, 'values'):
        X_array = X.values
        X_is_df = True
        original_columns = X.columns
    else:
        X_array = np.array(X)
        X_is_df = False
        original_columns = None
    
    if hasattr(y, 'values'):
        y_array = y.values
    else:
        y_array = np.array(y)
    
    # Try importing SMOTE
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X_array, y_array)
    except ImportError:
        # Manual oversampling implementation
        # Find class counts
        unique_classes, counts = np.unique(y_array, return_counts=True)
        max_count = counts.max()
        min_count = counts.min()
        
        # If already balanced, return original
        if max_count == min_count:
            return X, y
        
        # Identify minority and majority classes
        minority_class = unique_classes[counts.argmin()]
        majority_class = unique_classes[counts.argmax()]
        
        # Get samples for each class
        minority_mask = (y_array == minority_class)
        majority_mask = (y_array == majority_class)
        
        minority_X = X_array[minority_mask]
        minority_y = y_array[minority_mask]
        
        majority_X = X_array[majority_mask]
        majority_y = y_array[majority_mask]
        
        # Oversample minority class by duplicating
        n_needed = max_count - len(minority_X)
        n_repeats = (n_needed // len(minority_X)) + 1
        oversampled_X = np.tile(minority_X, (n_repeats, 1))[:n_needed]
        oversampled_y = np.tile(minority_y, n_repeats)[:n_needed]
        
        # Combine with majority class
        X_resampled = np.vstack([majority_X, oversampled_X])
        y_resampled = np.concatenate([majority_y, oversampled_y])
    
    # Convert back to original type
    if X_is_df:
        X_result = pd.DataFrame(X_resampled, columns=original_columns)
        y_result = pd.Series(y_resampled)
    else:
        X_result = X_resampled
        y_result = y_resampled
    
    return X_result, y_result
