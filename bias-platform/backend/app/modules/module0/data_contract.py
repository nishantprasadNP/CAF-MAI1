from typing import Any
import pandas as pd
import numpy as np


class DataContract:
    def __init__(self, df: pd.DataFrame, target_column: str, bias_columns: list[str]) -> None:
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' is not present in dataset.")

        missing_bias = [col for col in bias_columns if col not in df.columns]
        if missing_bias:
            raise ValueError(f"Bias columns not found: {missing_bias}")

        # Copy + sanitize infinities
        self.df = df.copy()
        self.df = self.df.replace([np.inf, -np.inf], np.nan)

        self.target_column = target_column
        self.bias_columns = sorted(set(bias_columns))

    # ---------------- COLUMN TYPE NORMALIZATION ---------------- #

    def _normalize_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure each column has consistent type:
        - numeric → float
        - categorical → string
        """
        df = df.copy()

        for col in df.columns:
            series = df[col]

            if pd.api.types.is_numeric_dtype(series):
                df[col] = pd.to_numeric(series, errors="coerce").fillna(0.0)
            else:
                # Convert everything else to string (important!)
                df[col] = series.astype(str)

        return df

    # ---------------- COLUMN TYPES ---------------- #

    def _infer_column_types(self) -> dict[str, str]:
        out: dict[str, str] = {}

        for col in self.df.columns:
            dtype = self.df[col].dtype

            if pd.api.types.is_numeric_dtype(dtype):
                out[col] = "numeric"
            elif pd.api.types.is_bool_dtype(dtype):
                out[col] = "boolean"
            else:
                out[col] = "categorical"

        return out

    # ---------------- TARGET TYPE ---------------- #

    def _infer_target_type(self) -> str:
        target = self.df[self.target_column]

        if pd.api.types.is_numeric_dtype(target):
            if target.nunique(dropna=True) <= 20:
                return "classification"
            return "regression"

        return "classification"

    # ---------------- NAN CLEANER ---------------- #

    def _clean_nan(self, obj: Any) -> Any:
        """
        Recursively remove NaN / inf values (JSON safe)
        """
        if isinstance(obj, dict):
            return {k: self._clean_nan(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [self._clean_nan(v) for v in obj]

        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return 0.0

        return obj

    # ---------------- BUILD ---------------- #

    def build(self) -> dict[str, Any]:
        # Split features and target
        x = self.df.drop(columns=[self.target_column])
        y = self.df[self.target_column]

        # 🔥 FIX 1: normalize types (CRITICAL for sklearn)
        x = self._normalize_column_types(x)

        # 🔥 FIX 2: ensure target is numeric
        y = pd.to_numeric(y, errors="coerce").fillna(0.0)

        # 🔥 FIX 3: remove NaN / inf
        x = x.replace([np.nan, np.inf, -np.inf], 0.0)

        dataset = {
            "X": x.to_dict(orient="records"),
            "Y": y.tolist(),
            "B_user": self.bias_columns,
            "B_suggested": [],
            "B_hidden": [],
            "metadata": {
                "column_types": self._infer_column_types(),
                "target_type": self._infer_target_type(),
                "target_column": self.target_column,
            },
        }

        # 🔥 FINAL SAFETY
        return self._clean_nan(dataset)