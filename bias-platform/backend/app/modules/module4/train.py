from typing import Any

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.config import MAX_TRAIN_ROWS
from app.modules.module4.preprocess import build_preprocessor, sanitize_dataset

MIN_ROWS = 20


def _build_pipeline(x_df) -> tuple[Pipeline, list[str], list[str]]:
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(x_df)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1200, solver="liblinear")),
        ]
    )
    return pipeline, numeric_cols, categorical_cols


def train_baseline_model(dataset: dict[str, Any]) -> dict[str, Any]:
    x_df, y_series = sanitize_dataset(dataset)

    if len(x_df) < MIN_ROWS:
        raise ValueError(f"Dataset has {len(x_df)} rows; at least {MIN_ROWS} are needed to train and evaluate.")

    class_counts = y_series.value_counts()
    if class_counts.min() < 2:
        raise ValueError("Each target outcome needs at least 2 rows to build a train/test split.")

    x_train, x_test, y_train, y_test = train_test_split(
        x_df,
        y_series,
        test_size=0.2,
        random_state=42,
        stratify=y_series,
    )
    available_train_rows = len(x_train)
    if available_train_rows > MAX_TRAIN_ROWS:
        # Large datasets: fit on a stratified sample; evaluation keeps the full test split.
        x_train, _, y_train, _ = train_test_split(
            x_train, y_train, train_size=MAX_TRAIN_ROWS, random_state=42, stratify=y_train
        )

    x_train, x_test = x_train.reset_index(drop=True), x_test.reset_index(drop=True)
    y_train, y_test = y_train.reset_index(drop=True), y_test.reset_index(drop=True)

    pipeline, numeric_cols, categorical_cols = _build_pipeline(x_train)
    pipeline.fit(x_train, y_train)

    # -------- METRICS (held-out split) -------- #
    predictions = pipeline.predict(x_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 6),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 6),
        "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 6),
    }

    return {
        "model_name": "logistic_regression",
        "_runtime": {
            "pipeline": pipeline,
            "x_train": x_train,
            "y_train": y_train,
            "x_test": x_test,
            "y_test": y_test,
        },
        "metrics": metrics,
        "train_rows": len(x_train),
        "train_rows_available": available_train_rows,
        "test_rows": len(x_test),
        "preprocessing": {
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
        },
    }


# ---------------- WEIGHTED TRAINING (MODULE 6) ---------------- #

def train_with_weights(X_train, y_train, weights) -> Pipeline:
    pipeline, _, _ = _build_pipeline(X_train)
    pipeline.fit(X_train, y_train, model__sample_weight=weights)
    return pipeline
