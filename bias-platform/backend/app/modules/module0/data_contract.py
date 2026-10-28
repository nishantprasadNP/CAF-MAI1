from typing import Any
import pandas as pd
import numpy as np


class DataContract:
    """
    Validates a raw dataframe against the selected target and produces the
    dataset dict consumed by the pipeline.

    The platform models binary decisions (approve / reject), so the target must
    have exactly two distinct values. Those values are encoded to 0 / 1 and the
    original labels are kept in metadata["class_labels"].
    """

    def __init__(self, df: pd.DataFrame, target_column: str, bias_columns: list[str]) -> None:
        if df is None or df.empty:
            raise ValueError("Dataset is empty. Upload a CSV with at least one data row.")

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' is not present in dataset.")

        missing_bias = [col for col in bias_columns if col not in df.columns]
        if missing_bias:
            raise ValueError(f"Bias columns not found: {missing_bias}")

        if df.shape[1] < 2:
            raise ValueError("Dataset needs at least one feature column besides the target.")

        # Not copied: build() only derives new frames, and datasets can be millions of rows.
        self.df = df

        self.target_column = target_column
        self.bias_columns = sorted(set(bias_columns))

    # ---------------- COLUMN TYPE NORMALIZATION ---------------- #

    def _normalize_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure each column has consistent type:
        - numeric → float (missing values stay NaN for the model's imputer)
        - categorical → string (missing values stay NaN)
        """
        df = df.copy(deep=False)

        for col in df.columns:
            series = df[col]

            if isinstance(series.dtype, pd.CategoricalDtype):
                # Already compact (set at upload); just make sure categories are text.
                df[col] = series.cat.rename_categories([str(c) for c in series.cat.categories])
            elif pd.api.types.is_bool_dtype(series):
                df[col] = series.astype(str)
            elif pd.api.types.is_numeric_dtype(series):
                df[col] = pd.to_numeric(series, errors="coerce").astype(float).replace([np.inf, -np.inf], np.nan)
            else:
                df[col] = series.astype(object).where(series.isna(), series.astype(str))

        return df

    # ---------------- COLUMN TYPES ---------------- #

    def _infer_column_types(self) -> dict[str, str]:
        out: dict[str, str] = {}

        for col in self.df.columns:
            dtype = self.df[col].dtype

            if pd.api.types.is_bool_dtype(dtype):
                out[col] = "boolean"
            elif pd.api.types.is_numeric_dtype(dtype):
                out[col] = "numeric"
            else:
                out[col] = "categorical"

        return out

    # ---------------- TARGET ENCODING ---------------- #

    def _encode_target(self, y: pd.Series) -> tuple[pd.Series, dict[str, str]]:
        values = sorted(y.dropna().unique().tolist(), key=lambda v: (str(type(v)), v))

        if len(values) < 2:
            raise ValueError(
                f"Target column '{self.target_column}' has only one distinct value. "
                "Choose a column with exactly two outcomes (e.g. yes/no, 0/1)."
            )

        if len(values) > 2:
            if pd.api.types.is_numeric_dtype(y) and len(values) > 20:
                kind = "looks continuous (regression)"
            else:
                kind = f"has {len(values)} distinct values"
            raise ValueError(
                f"Target column '{self.target_column}' {kind}. "
                "Bias analysis requires a binary target with exactly two outcomes."
            )

        # Sorted order keeps 0/1 and False/True as-is; for text labels the
        # alphabetically second value (e.g. "yes" over "no") is the positive outcome.
        negative, positive = values

        encoded = y.map({negative: 0, positive: 1})
        return encoded, {"0": str(negative), "1": str(positive)}

    # ---------------- IDENTIFIER COLUMNS ---------------- #

    @staticmethod
    def identifier_columns(x: pd.DataFrame) -> list[str]:
        """
        Text columns that are (nearly) unique per row, e.g. customer or
        transaction IDs. They carry no generalisable signal and would explode
        one-hot encoding, so they are excluded from modelling.
        """
        n = len(x)
        return [
            col for col in x.columns
            if not pd.api.types.is_numeric_dtype(x[col])
            and DataContract.is_identifier(x[col].nunique(dropna=True), n)
        ]

    @staticmethod
    def is_identifier(distinct: int, n: int) -> bool:
        if n < 20:
            return False
        return distinct > 0.5 * n or (distinct > 1000 and distinct > 0.05 * n)

    # ---------------- BUILD ---------------- #

    def build(self) -> dict[str, Any]:
        # Rows without a target value cannot be used for training or evaluation.
        has_target = self.df[self.target_column].notna()
        df = self.df if has_target.all() else self.df[has_target].reset_index(drop=True)
        dropped = len(self.df) - len(df)

        x = df.drop(columns=[self.target_column])
        id_columns = self.identifier_columns(x)
        x = self._normalize_column_types(x.drop(columns=id_columns))
        if x.shape[1] == 0:
            raise ValueError("No usable feature columns remain after excluding identifier columns.")

        target = df[self.target_column]
        if isinstance(target.dtype, pd.CategoricalDtype):
            target = target.astype(object)
        y, class_labels = self._encode_target(target)

        return {
            "X": x,
            "Y": y.astype(int),
            "B_user": self.bias_columns,
            "metadata": {
                "column_types": self._infer_column_types(),
                "target_type": "binary_classification",
                "target_column": self.target_column,
                "class_labels": class_labels,
                "rows": len(df),
                "dropped_rows_missing_target": dropped,
                "excluded_id_columns": id_columns,
            },
        }
