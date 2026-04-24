from typing import Any

import pandas as pd


class DataContract:
    def __init__(self, df: pd.DataFrame, target_column: str, bias_columns: list[str]) -> None:
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' is not present in dataset.")
        missing_bias = [col for col in bias_columns if col not in df.columns]
        if missing_bias:
            raise ValueError(f"Bias columns not found: {missing_bias}")

        self.df = df.copy()
        self.target_column = target_column
        self.bias_columns = sorted(set(bias_columns))

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

    def _infer_target_type(self) -> str:
        target = self.df[self.target_column]
        if pd.api.types.is_numeric_dtype(target):
            # Heuristic: low-cardinality numeric target is usually classification.
            if target.nunique(dropna=True) <= 20:
                return "classification"
            return "regression"
        return "classification"

    def build(self) -> dict[str, Any]:
        x = self.df.drop(columns=[self.target_column])
        y = self.df[self.target_column]
        return {
            "X": x.where(pd.notna(x), None).to_dict(orient="records"),
            "Y": y.where(pd.notna(y), None).tolist(),
            "B_user": self.bias_columns,
            "B_suggested": [],
            "B_hidden": [],
            "metadata": {
                "column_types": self._infer_column_types(),
                "target_type": self._infer_target_type(),
                "target_column": self.target_column,
            },
        }
