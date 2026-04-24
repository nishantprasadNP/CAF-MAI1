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

    # Serializable result safe to return via /results.
    # The raw pipeline and x_test are NOT included here because sklearn objects
    # cannot be JSON-serialised by Pydantic.  Callers that need the live
    # pipeline for downstream inference (Module 5 / 6) should read the
    # "_runtime" key and then drop it before storing in results.
    return {
        "model_name": model_name,
        # Runtime objects needed by downstream modules – must be stripped
        # before the dict is handed to the aggregator / returned via API.
        "_runtime": {
            "pipeline": pipeline,
            "x_test": x_test,
            "y_test": y_test,
        },
        # Serialisable fields returned to the frontend
        "y_test": y_test.tolist(),
        "predictions": predictions.tolist(),
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


def train_with_weights(X_train, y_train, weights):
    """
    Train a Logistic Regression model using sample weights for fairness-aware training.
    
    Args:
        X_train: Training features (DataFrame or array-like)
        y_train: Training labels (Series or array-like)
        weights: Sample weights array (must match length of X_train)
        
    Returns:
        Dictionary containing:
            - model: trained model
            - predictions: model predictions on training data
            - probabilities: predicted probabilities for positive class
            
    Raises:
        ValueError: If len(weights) != len(X_train)
    """
    import numpy as np
    import pandas as pd
    from sklearn.pipeline import Pipeline
    
    # Convert to DataFrame for consistent handling
    if hasattr(X_train, 'values'):
        X_df = pd.DataFrame(X_train)
    else:
        X_df = pd.DataFrame(X_train)
    
    if hasattr(y_train, 'values'):
        y_array = y_train.values
    else:
        y_array = np.array(y_train)
    
    if hasattr(weights, 'values'):
        weights_array = weights.values
    else:
        weights_array = np.array(weights)
    
    # Validate inputs
    n_samples = len(X_df)
    if len(weights_array) != n_samples:
        raise ValueError(f"Length mismatch: len(weights)={len(weights_array)} != len(X_train)={n_samples}")
    
    # Build preprocessor to handle categorical columns
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(X_df)
    
    # Create pipeline with preprocessor and model
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(solver='liblinear', max_iter=1200)),
        ]
    )
    
    # Train with sample weights
    pipeline.fit(X_df, y_array, model__sample_weight=weights_array)
    
    # Make predictions
    y_pred = pipeline.predict(X_df)
    y_prob = pipeline.predict_proba(X_df)[:, 1]
    
    return {
        # Runtime objects for downstream use – strip before JSON serialisation.
        "_runtime": {
            "model": pipeline,
            "predictions": y_pred,
            "probabilities": y_prob,
        },
        # Serialisable summary
        "predictions": y_pred.tolist(),
        "probabilities": y_prob.tolist(),
    }
 