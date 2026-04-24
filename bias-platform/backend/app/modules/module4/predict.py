from typing import Any

import pandas as pd


def _predict_with_probability(model_pipeline, frame: pd.DataFrame) -> tuple[list[Any], list[list[float]]]:
    predictions = model_pipeline.predict(frame).tolist()
    if hasattr(model_pipeline, "predict_proba"):
        probabilities = model_pipeline.predict_proba(frame).tolist()
    else:
        probabilities = []
    return predictions, probabilities


def predict_batch(model_pipeline, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("rows for batch inference cannot be empty.")
    frame = pd.DataFrame(rows)
    predictions, probabilities = _predict_with_probability(model_pipeline, frame)
    return {
        "count": len(predictions),
        "predictions": predictions,
        "probabilities": probabilities,
    }


def predict_single(model_pipeline, row: dict[str, Any]) -> dict[str, Any]:
    if not row:
        raise ValueError("row for single inference cannot be empty.")
    frame = pd.DataFrame([row])
    predictions, probabilities = _predict_with_probability(model_pipeline, frame)
    return {
        "prediction": predictions[0],
        "probability": probabilities[0] if probabilities else [],
    }
