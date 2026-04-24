from typing import Any

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.modules.module4.preprocess import build_preprocessor, sanitize_dataset

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover - optional dependency
    XGBClassifier = None


def _build_model(model_name: str):
    normalized = model_name.lower()
    if normalized == "xgboost":
        if XGBClassifier is None:
            raise ValueError("xgboost is not installed. Use model_name='logistic_regression' or install xgboost.")
        return XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )
    return LogisticRegression(max_iter=1200)


def train_baseline_model(dataset: dict[str, Any], model_name: str = "logistic_regression") -> dict[str, Any]:
    x_df, y_series = sanitize_dataset(dataset)
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(x_df)
    estimator = _build_model(model_name)

    x_train, x_test, y_train, y_test = train_test_split(
        x_df,
        y_series,
        test_size=0.2,
        random_state=42,
        stratify=y_series if y_series.nunique(dropna=True) > 1 else None,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
        "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 6),
        "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 6),
        "f1_score": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 6),
    }

    transformed = pipeline.named_steps["preprocessor"].transform(x_df)
    transformed_feature_count = transformed.shape[1]

    return {
        "model_name": model_name,
        "pipeline": pipeline,
        "x_test": x_test,
        "y_test": y_test.tolist(),
        "metrics": metrics,
        "preprocessing": {
            "imputation": {
                "numeric": "median",
                "categorical": "most_frequent",
            },
            "encoding": "one_hot",
            "normalization": "standard_scaler",
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "transformed_feature_count": int(transformed_feature_count),
        },
    }
