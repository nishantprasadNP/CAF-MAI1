from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
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
            ("imputer", SimpleImputer(strategy="most_frequent")),
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
