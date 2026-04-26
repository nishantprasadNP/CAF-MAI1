from typing import Any

from app.modules.module4.predict import predict_batch, predict_single
from app.modules.module4.train import train_baseline_model


def run_module4(dataset: dict[str, Any]) -> dict[str, Any]:
    train_result = train_baseline_model(dataset=dataset)

    # 🔥 KEEP RUNTIME (CRITICAL)
    runtime = train_result["_runtime"]
    model_pipeline = runtime["pipeline"]
    x_test_records = runtime["x_test"].to_dict(orient="records")

    # -------- INFERENCE -------- #
    batch_out = predict_batch(model_pipeline=model_pipeline, rows=x_test_records)

    single_out = (
        predict_single(model_pipeline=model_pipeline, row=x_test_records[0])
        if x_test_records else None
    )

    return {
        "_runtime": runtime,   # 🔥 IMPORTANT FIX
        "model": {
            "name": train_result.get("model_name", "logistic_regression"),
            "metrics": train_result.get("metrics", {}),
            "feature_importance": train_result.get("feature_importance", {}),
        },
        "preprocessing": train_result.get("preprocessing", {}),
        "inference": {
            "batch": batch_out,
            "single": single_out,
        },
    }