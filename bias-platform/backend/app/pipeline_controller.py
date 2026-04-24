from io import StringIO
from typing import Any

import pandas as pd


def _deep_strip_runtime(obj: Any) -> Any:
    """Recursively remove '_runtime' keys so sklearn objects never reach the JSON serialiser."""
    if isinstance(obj, dict):
        return {k: _deep_strip_runtime(v) for k, v in obj.items() if k != "_runtime"}
    if isinstance(obj, list):
        return [_deep_strip_runtime(i) for i in obj]
    return obj

from app.modules.module0.data_contract import DataContract
from app.modules.module1.profiler import profile_dataset
from app.modules.module2.service import detect_hidden_bias, suggest_bias_columns
from app.modules.module3.aggregator import aggregate_results
from app.modules.module4.service import run_module4
from app.modules.module5.service import run_module5
from app.modules.module6.service import run_module6


class BiasPipeline:
    def __init__(self) -> None:
        self.raw_df: pd.DataFrame | None = None
        self.dataset: dict[str, Any] | None = None
        self.bias_columns: list[str] = []
        self.profile: dict[str, Any] | None = None
        self.results: dict[str, Any] | None = None

    def upload_data(self, file_bytes: bytes) -> dict[str, Any]:
        csv_text = file_bytes.decode("utf-8")
        self.raw_df = pd.read_csv(StringIO(csv_text))
        preview = self.raw_df.head(5).where(pd.notna(self.raw_df.head(5)), None).to_dict(orient="records")
        return {
            "columns": self.raw_df.columns.tolist(),
            "rows": int(len(self.raw_df)),
            "preview": preview,
        }

    def initialize_contract(self, target_column: str) -> dict[str, Any]:
        if self.raw_df is None:
            raise ValueError("No uploaded dataset found. Call upload_data first.")
        contract = DataContract(df=self.raw_df, target_column=target_column, bias_columns=[])
        self.dataset = contract.build()
        return self.dataset

    def select_bias(self, bias_columns: list[str]) -> dict[str, Any]:
        if self.dataset is None:
            raise ValueError("Data contract is not initialized. Call initialize_contract first.")

        x_df = pd.DataFrame(self.dataset["X"])
        invalid = [col for col in bias_columns if col not in x_df.columns]
        if invalid:
            raise ValueError(f"Bias columns not found in contract X: {invalid}")

        self.dataset["B_user"] = sorted(set(bias_columns))
        self.bias_columns = self.dataset["B_user"]
        self.dataset["B_suggested"] = suggest_bias_columns(self.dataset, top_k=5)
        return {
            "B_user": self.dataset["B_user"],
            "B_suggested": self.dataset["B_suggested"],
        }

    def run_pipeline(self) -> dict[str, Any]:
        if self.dataset is None:
            raise ValueError("Data contract is not initialized. Call initialize_contract first.")

        self.profile = profile_dataset(self.dataset)
        module2_result = detect_hidden_bias(self.dataset, top_n=3)
        self.dataset["B_hidden"] = sorted(set(module2_result["B_hidden"]))
        module4_result = run_module4(dataset=self.dataset, model_name="logistic_regression")
        predictions = module4_result["inference"]["batch"]["predictions"]
        y_test = pd.Series(self.dataset["Y"]).iloc[: len(predictions)]
        df_for_module5 = pd.DataFrame(self.dataset["X"]).iloc[: len(predictions)]
        module5_results = run_module5(
            df=df_for_module5,
            y_true=y_test,
            y_pred=pd.Series(predictions, index=df_for_module5.index),
            bias_columns=self.bias_columns,
        )
        self.results = aggregate_results(
            dataset=self.dataset,
            profile=self.profile,
            module2_result=module2_result,
            module4_result=module4_result,
        )
        self.results["module5"] = module5_results
        
        # Run Module 6 debiasing pipeline
        X_train = pd.DataFrame(self.dataset["X"])
        y_train = pd.Series(self.dataset["Y"])
        module6_results = run_module6(
            df=pd.DataFrame(self.dataset["X"]),
            X_train=X_train,
            y_train=y_train,
            bias_columns=self.bias_columns,
            module5_results=module5_results
        )
        self.results["module6"] = module6_results

        # Strip all non-serialisable sklearn/numpy objects from every module
        # before results are stored and returned via /results.
        self.results = _deep_strip_runtime(self.results)

        return self.results
 