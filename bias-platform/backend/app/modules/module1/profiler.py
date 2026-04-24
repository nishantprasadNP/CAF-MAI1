from typing import Any

import pandas as pd


def profile_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    df = pd.DataFrame(dataset["X"])
    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "null_count_by_column": {col: int(df[col].isna().sum()) for col in df.columns},
        "unique_count_by_column": {col: int(df[col].nunique(dropna=True)) for col in df.columns},
    }
    return profile
