from typing import Any
 
from app.modules.module4.predict import predict_batch, predict_single
from app.modules.module4.train import train_baseline_model
 
 
def run_module4(dataset: dict[str, Any], model_name: str = "logistic_regression") -> dict[str, Any]:
    train_result = train_baseline_model(dataset=dataset, model_name=model_name)
 
    # pipeline and x_test live in "_runtime" to avoid Pydantic serialisation errors.
    runtime = train_result["_runtime"]
    model_pipeline = runtime["pipeline"]
    x_test_records = runtime["x_test"].to_dict(orient="records")
 
    batch_out = predict_batch(model_pipeline=model_pipeline, rows=x_test_records)
    single_out = predict_single(model_pipeline=model_pipeline, row=x_test_records[0]) if x_test_records else None
 
    return {
        "model": {
            "name": train_result["model_name"],
            "model_type": train_result.get("model_type", train_result["model_name"]),
            "calibrated": bool(train_result.get("calibrated", False)),
            "metrics": train_result["metrics"],
            "coefficients": train_result.get("coefficients", {}),
            "feature_importance": train_result.get("feature_importance", {}),
        },
        "preprocessing": train_result["preprocessing"],
        "inference": {
            "batch": batch_out,
            "single": single_out,
        },
    }
 