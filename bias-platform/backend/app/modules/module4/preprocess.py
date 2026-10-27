from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


MAX_CATEGORIES = 50


def _to_string(data):
    # Force categorical columns to a uniform string dtype so sklearn
    # encoders never receive mixed float/str values.
    # Plain array so feature names pass through by position ("one-to-one").
    return np.asarray(data, dtype=object).astype(str)


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
            # Impute before stringifying, otherwise NaN becomes the literal "nan".
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("to_string", FunctionTransformer(_to_string, validate=False, feature_names_out="one-to-one")),
            # Rare categories are pooled so high-cardinality columns stay bounded.
            ("encoder", OneHotEncoder(handle_unknown="infrequent_if_exist", max_categories=MAX_CATEGORIES)),
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
    x_df = pd.DataFrame(dataset.get("X"))
    y_series = pd.Series(dataset.get("Y"), dtype="int64")
    if x_df.empty or y_series.empty:
        raise ValueError("Dataset must include non-empty X and Y.")

    if len(x_df) != len(y_series):
        raise ValueError("Length mismatch: X and Y must have same number of rows.")
    return x_df, y_series
