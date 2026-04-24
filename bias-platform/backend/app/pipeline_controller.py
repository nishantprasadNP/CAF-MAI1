from io import StringIO
from typing import Any

import pandas as pd

from app.modules.module0.data_contract import DataContract
from app.modules.module1.profiler import profile_dataset
from app.modules.module2.service import detect_hidden_bias, suggest_bias_columns
from app.modules.module3.aggregator import aggregate_results
from app.modules.module4.service import run_module4


class BiasPipeline:
    def __init__(self) -> None:
        self.raw_df: pd.DataFrame | None = None
        self.dataset: dict[str, Any] | None = None
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
        self.results = aggregate_results(
            dataset=self.dataset,
            profile=self.profile,
            module2_result=module2_result,
            module4_result=module4_result,
        )
        return self.results
