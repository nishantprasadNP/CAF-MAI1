from collections import Counter
from typing import Any

import pandas as pd
from sklearn.cluster import KMeans


def _to_dataframe(dataset: dict[str, Any]) -> pd.DataFrame:
    x = dataset.get("X", [])
    if not x:
        raise ValueError("Dataset X is empty.")
    return pd.DataFrame(x)


def suggest_bias_columns(dataset: dict[str, Any], top_k: int = 5) -> list[str]:
    df = _to_dataframe(dataset)
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return []

    variances = {col: float(df[col].fillna(0).var()) for col in numeric_cols}
    ranked = sorted(variances.items(), key=lambda item: item[1], reverse=True)
    return [name for name, _ in ranked[:top_k]]


def detect_hidden_bias(dataset: dict[str, Any], top_n: int = 3) -> dict[str, Any]:
    df = _to_dataframe(dataset)
    work = df.copy()
    for col in work.columns:
        if not pd.api.types.is_numeric_dtype(work[col]):
            work[col] = work[col].astype("category").cat.codes
        work[col] = work[col].fillna(-1)

    n_clusters = 3 if len(work) >= 3 else max(1, len(work))
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto").fit_predict(work).tolist()
    distribution = {str(k): int(v) for k, v in Counter(labels).items()}

    hidden_candidates = suggest_bias_columns(dataset, top_n)
    return {
        "cluster_labels": labels,
        "cluster_distribution": distribution,
        "B_hidden": hidden_candidates,
    }
