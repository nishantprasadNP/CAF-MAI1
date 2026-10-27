from typing import Any

from app.modules.module4.train import train_baseline_model


def run_module4(dataset: dict[str, Any]) -> dict[str, Any]:
    train_result = train_baseline_model(dataset=dataset)

    return {
        # Fitted model + train/test frames, stripped before results are returned.
        "_runtime": train_result["_runtime"],
        "model": {
            "name": train_result["model_name"],
            "metrics": train_result["metrics"],
            "train_rows": train_result["train_rows"],
            "train_rows_available": train_result["train_rows_available"],
            "test_rows": train_result["test_rows"],
        },
        "preprocessing": train_result["preprocessing"],
    }
