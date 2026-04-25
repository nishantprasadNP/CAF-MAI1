from io import StringIO
from typing import Any

import pandas as pd

from app.modules.module0.data_contract import DataContract
from app.modules.module1.profiler import profile_dataset
from app.modules.module2.service import detect_hidden_bias, suggest_bias_columns
from app.modules.module3.aggregator import aggregate_results
from app.modules.module4.service import run_module4
from app.modules.module5.service import run_module5
from app.modules.module6.service import run_module6
from app.modules.module7.schema import ContextSchema
from app.modules.module7.service import (
    apply_context_probabilities,
    calculate_bias_score,
    context_confidence,
    context_service,
)
from app.modules.module8.service import run_module8
from app.modules.module9.service import validate_decision
from app.modules.module10.service import apply_compliance
from app.modules.module11.service import run_monitoring


def _deep_strip_runtime(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_strip_runtime(v) for k, v in obj.items() if k != "_runtime"}
    if isinstance(obj, list):
        return [_deep_strip_runtime(v) for v in obj]
    return obj


def _normalize_probs(probs: list[float]) -> list[float]:
    if not probs:
        return []
    safe = [max(0.0, float(p)) for p in probs]
    total = sum(safe)
    if total <= 0:
        return [1.0 / len(safe) for _ in safe]
    return [p / total for p in safe]


def _extract_debiased_probabilities(module4_probs: list[float], module6_result: dict[str, Any]) -> list[float]:
    """
    Module 6 currently returns per-row positive-class probabilities.
    For pipeline-level decisioning, derive a compact class probability vector.
    """
    reweighted_probs = (
        module6_result.get("reweighted_results", {}).get("probabilities", [])
        if isinstance(module6_result, dict)
        else []
    )
    if isinstance(reweighted_probs, list) and len(reweighted_probs) >= len(module4_probs) and len(module4_probs) > 0:
        candidate = reweighted_probs[: len(module4_probs)]
        if all(isinstance(x, (int, float)) for x in candidate):
            return _normalize_probs(candidate)
    return _normalize_probs(module4_probs)


class BiasPipeline:
    def __init__(self) -> None:
        self.raw_df: pd.DataFrame | None = None
        self.dataset: dict[str, Any] | None = None
        self.bias_columns: list[str] = []
        self.profile: dict[str, Any] | None = None
        self.pipeline_state: dict[str, Any] = {}
        self.results: dict[str, Any] | None = None

    def upload_data(self, file_bytes: bytes) -> dict[str, Any]:
        csv_text = file_bytes.decode("utf-8")
        self.raw_df = pd.read_csv(StringIO(csv_text))
        preview = self.raw_df.head(5).where(pd.notna(self.raw_df.head(5)), None).to_dict(orient="records")
        return {"columns": self.raw_df.columns.tolist(), "rows": int(len(self.raw_df)), "preview": preview}

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
        return {"B_user": self.dataset["B_user"], "B_suggested": self.dataset["B_suggested"]}

    def run_pipeline(self) -> dict[str, Any]:
        if self.dataset is None:
            raise ValueError("Data contract is not initialized. Call initialize_contract first.")

        self.pipeline_state = {
            "dataset": self.dataset,
            "bias_columns": self.bias_columns,
            "model_output": {},
            "fairness": {},
            "debiasing": {},
            "context": {},
            "decision": {},
            "validation": {},
            "compliance": {},
            "monitoring": {},
        }

        # Module 1/2 pre-inference support
        self.profile = profile_dataset(self.dataset)
        module2_result = detect_hidden_bias(self.dataset, top_n=3)
        self.dataset["B_hidden"] = sorted(set(module2_result.get("B_hidden", [])))

        # Module 4
        module4_result = run_module4(dataset=self.dataset, model_name="logistic_regression")
        self.pipeline_state["model_output"] = module4_result

        # Module 5 fairness
        predictions = module4_result.get("inference", {}).get("batch", {}).get("predictions", [])
        y_eval = pd.Series(self.dataset["Y"]).iloc[: len(predictions)]
        df_eval = pd.DataFrame(self.dataset["X"]).iloc[: len(predictions)]
        module5_result = run_module5(
            df=df_eval,
            y_true=y_eval,
            y_pred=pd.Series(predictions, index=df_eval.index),
            bias_columns=self.bias_columns,
        )
        self.pipeline_state["fairness"] = module5_result

        # Module 6 debiasing
        x_train = pd.DataFrame(self.dataset["X"])
        y_train = pd.Series(self.dataset["Y"])
        module6_result = run_module6(
            df=x_train,
            X_train=x_train,
            y_train=y_train,
            bias_columns=self.bias_columns,
            module5_results=module5_result,
        )

        # 4 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 strict sequential flow
        raw_probs = module4_result.get("inference", {}).get("batch", {}).get("probabilities", [])
        module4_probs = raw_probs[0] if raw_probs else []
        debiased_probs = _extract_debiased_probabilities(module4_probs, module6_result)
        module6_result["debiased_probabilities"] = debiased_probs
        self.pipeline_state["debiasing"] = module6_result

        # Module 7 context injection
        context = context_service.get_context()
        if not context:
            context = ContextSchema.validate(
                {
                    "region": "urban",
                    "hospital_type": "private",
                    "resource_level": "medium",
                    "time_of_day": "day",
                }
            )
            context_service.set_context(context)
        final_probs = apply_context_probabilities(debiased_probs, context)
        context_weights = context_service.apply_context_to_predictions(debiased_probs).get("context_weights", {})
        bias_info = calculate_bias_score(debiased_probs)
        context_conf = context_confidence(context)
        context_reason = (
            "No strong context signal detected"
            if str(context.get("resource_level", "")).lower() == "unknown"
            else f"resource_level = {context.get('resource_level', 'unknown')}"
        )
        self.pipeline_state["context"] = {
            "context": context,
            "original_probabilities": debiased_probs,
            "adjusted_probabilities": final_probs,
            "context_weights": context_weights,
            "bias_score": float(bias_info.get("bias_score", 0.0)),
            "context_confidence": context_conf,
            "reason": context_reason,
        }

        # Module 8 decision + explainability
        module8_result = run_module8(
            probabilities=final_probs,
            original_probabilities=debiased_probs,
            fairness_output=module5_result,
            top_features=self.bias_columns,
        )
        self.pipeline_state["decision"] = module8_result

        # Module 9 decision validation
        self.pipeline_state["validation"] = validate_decision(
            decision_output=module8_result,
            available_resources=8,
        )

        # Module 10 privacy + compliance
        compliance = apply_compliance(
            dataset_df=pd.DataFrame(self.dataset["X"]),
            user="pipeline_user",
            role="analyst",
            action="run_pipeline",
            decision=module8_result.get("decision", "reject"),
        )
        if not compliance.get("compliant", False):
            raise ValueError("Policy violation")
        self.pipeline_state["compliance"] = compliance

        # Module 11 monitoring
        self.pipeline_state["monitoring"] = run_monitoring(
            df=pd.DataFrame(self.dataset["X"]),
            fairness_output=module5_result,
            decision_output=module8_result,
            bias_columns=self.bias_columns,
        )

        # Backward-compatible envelope for existing UI
        legacy = aggregate_results(
            dataset=self.dataset,
            profile=self.profile,
            module2_result=module2_result,
            module4_result=module4_result,
        )
        legacy["module5"] = module5_result
        legacy["module6"] = module6_result
        legacy["module7"] = {
            "adjusted_probabilities": final_probs,
            "context_weights": context_weights,
            "bias_score": self.pipeline_state["context"]["bias_score"],
            "context_confidence": context_conf,
            "reason": context_reason,
        }
        legacy["module8"] = {
            "final_decision": module8_result.get("label"),
            "confidence": module8_result.get("confidence"),
            "explanation": module8_result.get("explanation"),
            "explanation_structured": module8_result.get("explanation_structured"),
            "feature_importance": module8_result.get("feature_importance"),
        }
        legacy["module9"] = self.pipeline_state["validation"]
        legacy["module10"] = self.pipeline_state["compliance"]
        legacy["module11"] = self.pipeline_state["monitoring"]

        final_output = {
            "model_output": self.pipeline_state["model_output"],
            "fairness": self.pipeline_state["fairness"],
            "debiasing": self.pipeline_state["debiasing"],
            "context": self.pipeline_state["context"],
            "decision": self.pipeline_state["decision"],
            "validation": self.pipeline_state["validation"],
            "compliance": self.pipeline_state["compliance"],
            "monitoring": self.pipeline_state["monitoring"],
            # compatibility fields
            "dataset": legacy.get("dataset"),
            "profile": legacy.get("profile"),
            "module2": legacy.get("module2"),
            "module4": legacy.get("module4"),
            "module5": legacy.get("module5"),
            "module6": legacy.get("module6"),
            "module7": legacy.get("module7"),
            "module8": legacy.get("module8"),
            "module9": legacy.get("module9"),
            "module10": legacy.get("module10"),
            "module11": legacy.get("module11"),
            "registry": legacy.get("registry"),
        }

        self.pipeline_state = _deep_strip_runtime(self.pipeline_state)
        self.results = _deep_strip_runtime(final_output)
        return self.results
