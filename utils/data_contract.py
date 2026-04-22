from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


class DataContract:
    def __init__(
        self,
        df: pd.DataFrame,
        target_column: str,
        bias_columns: list[str] | None = None,
    ) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' does not exist in DataFrame")

        self.df = df.copy()
        self.target_column = target_column

        missing_target_rows = self.df[self.target_column].isna().sum()
        if missing_target_rows > 0:
            print(
                f"Warning: Dropping {missing_target_rows} rows with missing target values in "
                f"'{self.target_column}'."
            )
            self.df = self.df.dropna(subset=[self.target_column])

        self.X = self.df.drop(columns=[self.target_column])
        self.Y = self.df[self.target_column]

        self.B_user = bias_columns or []
        self.B_suggested: list[str] = []
        self.B_hidden: list[str] = []

        self.column_types = self._infer_column_types()
        self.target_type = self._infer_target_type()

    def _infer_column_types(self) -> dict[str, str]:
        column_types: dict[str, str] = {}
        for column in self.X.columns:
            dtype = self.X[column].dtype
            if is_numeric_dtype(dtype):
                column_types[column] = "numeric"
            elif is_object_dtype(dtype) or is_categorical_dtype(dtype):
                column_types[column] = "categorical"
            else:
                column_types[column] = "categorical"
        return column_types

    def _infer_target_type(self) -> str:
        y_non_null = self.Y.dropna()
        unique_count = y_non_null.nunique()

        if is_numeric_dtype(y_non_null.dtype) and unique_count > 10:
            return "regression"
        if unique_count == 2:
            return "binary"
        if unique_count > 2:
            return "multiclass"
        return "binary"

    def get_data(self) -> dict[str, Any]:
        return {
            "X": self.X,
            "Y": self.Y,
            "B_user": self.B_user,
            "B_suggested": self.B_suggested,
            "B_hidden": self.B_hidden,
            "metadata": {
                "column_types": self.column_types,
                "target_type": self.target_type,
            },
        }
