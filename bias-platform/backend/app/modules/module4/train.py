from typing import Any

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.modules.module4.preprocess import build_preprocessor, sanitize_dataset


def _build_model():
    return LogisticRegression(max_iter=1200, solver="liblinear")


def train_baseline_model(dataset: dict[str, Any]) -> dict[str, Any]:
    x_df, y_series = sanitize_dataset(dataset)

    preprocessor, numeric_cols, categorical_cols = build_preprocessor(x_df)
    estimator = _build_model()

    x_train, x_test, y_train, y_test = train_test_split(
        x_df,
        y_series,
        test_size=0.2,
        random_state=42,
        stratify=y_series if y_series.nunique(dropna=True) > 1 else None,
    )

    # 🔥 FIX: REMOVE calibration (this was killing bias signal)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )

    pipeline.fit(x_train, y_train)

    # -------- PREDICTIONS -------- #
    predictions = pipeline.predict(x_test)
    probabilities = pipeline.predict_proba(x_test)

    # 🔥 DEBUG (remove later if needed)
    print("Unique predictions:", set(predictions))

    # -------- METRICS -------- #
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
        "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 6),
        "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 6),
        "f1_score": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 6),
    }

    # -------- FEATURE IMPORTANCE -------- #
    feature_importance = {}
    try:
        model = pipeline.named_steps["model"]
        preprocessor_fit = pipeline.named_steps["preprocessor"]

        if hasattr(model, "coef_"):
            feature_names = preprocessor_fit.get_feature_names_out()
            coef_values = model.coef_[0]

            for name, value in zip(feature_names, coef_values):
                feature_importance[str(name)] = round(float(abs(value)), 6)

    except Exception:
        feature_importance = {}

    return {
        "model_name": "logistic_regression",
        "_runtime": {
            "pipeline": pipeline,
            "x_test": x_test,
            "y_test": y_test,
        },
        "y_test": y_test.tolist(),
        "predictions": predictions.tolist(),
        "probabilities": probabilities.tolist(),
        "metrics": metrics,
        "feature_importance": feature_importance,
        "preprocessing": {
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
        },
    }


# ---------------- WEIGHTED TRAINING (MODULE 6) ---------------- #

def train_with_weights(X_train, y_train, weights):
    import numpy as np
    import pandas as pd

    if hasattr(X_train, 'values'):
        X_df = pd.DataFrame(X_train)
    else:
        X_df = pd.DataFrame(X_train)

    y_array = np.array(y_train)
    weights_array = np.array(weights)

    preprocessor, _, _ = build_preprocessor(X_df)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1200, solver="liblinear")),
        ]
    )

    pipeline.fit(X_df, y_array, model__sample_weight=weights_array)

    y_pred = pipeline.predict(X_df)
    y_prob = pipeline.predict_proba(X_df)[:, 1]

    return {
        "_runtime": {
            "model": pipeline,
        },
        "predictions": y_pred.tolist(),
        "probabilities": y_prob.tolist(),
    }