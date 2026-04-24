from typing import Any

from app.modules.module4.predict import predict_batch, predict_single
from app.modules.module4.train import train_baseline_model


def run_module4(dataset: dict[str, Any], model_name: str = "logistic_regression") -> dict[str, Any]:
    train_result = train_baseline_model(dataset=dataset, model_name=model_name)
    model_pipeline = train_result["pipeline"]
    x_test_records = train_result["x_test"].to_dict(orient="records")

    batch_out = predict_batch(model_pipeline=model_pipeline, rows=x_test_records)
    single_out = predict_single(model_pipeline=model_pipeline, row=x_test_records[0]) if x_test_records else None

    return {
        "model": {
            "name": train_result["model_name"],
            "metrics": train_result["metrics"],
        },
        "preprocessing": train_result["preprocessing"],
        "inference": {
            "batch": batch_out,
            "single": single_out,
        },
    }
