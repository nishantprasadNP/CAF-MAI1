from io import StringIO
from typing import Any
import traceback

import pandas as pd
import math 

from app.modules.module0.data_contract import DataContract
from app.modules.module2.service import suggest_bias_columns
from app.modules.module4.service import run_module4
from app.modules.module5.service import run_module5
from app.modules.module6.service import run_module6
from app.modules.module7.schema import ContextSchema
from app.modules.module7.service import (
    apply_context_probabilities,
    context_confidence,
    context_service,
)
from app.modules.module8.service import run_module8
from app.modules.module9.service import validate_decision
from app.modules.module10.service import apply_compliance
from app.modules.module11.service import run_monitoring


# ---------------- UTILS ---------------- #

def log(stage: str, msg: str):
    print(f"[PIPELINE] [{stage}] {msg}")


def _deep_strip_runtime(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: _deep_strip_runtime(v)
            for k, v in obj.items()
            if k != "_runtime"
        }

    if isinstance(obj, list):
        return [_deep_strip_runtime(v) for v in obj]

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0

    return obj


def _normalize_probs(probs):
    try:
        safe = [float(p) for p in probs]
    except Exception:
        return [0.5, 0.5]

    total = sum(max(0.0, p) for p in safe)
    return [p / total for p in safe] if total > 0 else [0.5, 0.5]


def _extract_debiased_probabilities(base_probs, module6_result):
    try:
        reweighted = (module6_result or {}).get("reweighted_results", {}).get("probabilities", [])
        if isinstance(reweighted, list) and len(reweighted) >= len(base_probs):
            return _normalize_probs(reweighted[: len(base_probs)])
    except Exception as e:
        print("[M6 ERROR]", str(e))
    return _normalize_probs(base_probs)


# ---------------- PIPELINE ---------------- #

class BiasPipeline:
    def __init__(self):
        self.raw_df = None
        self.dataset = None
        self.bias_columns = []
        self.results = None

    # ---------------- DATA ---------------- #

    def upload_data(self, file_bytes: bytes):
        log("UPLOAD", "Reading CSV")
        self.raw_df = pd.read_csv(StringIO(file_bytes.decode("utf-8")))
        return {"columns": self.raw_df.columns.tolist(), "rows": len(self.raw_df)}

    def initialize_contract(self, target_column: str):
        if self.raw_df is None:
            raise ValueError("Upload dataset first")

        contract = DataContract(
            df=self.raw_df,
            target_column=target_column,
            bias_columns=[]
        )

        self.dataset = contract.build()

        if self.dataset is None:
            raise ValueError("DataContract.build() failed")

        return self.dataset

    def select_bias(self, bias_columns: list[str]):
        if self.dataset is None:
            raise ValueError("Run /init_contract first")

        self.dataset["B_user"] = bias_columns
        self.bias_columns = bias_columns
        self.dataset["B_suggested"] = suggest_bias_columns(self.dataset)

        return {
            "B_user": bias_columns,
            "B_suggested": self.dataset["B_suggested"]
        }

    # ---------------- MAIN PIPELINE ---------------- #

    def run_pipeline(self):

        if self.dataset is None:
            raise ValueError("Run /init_contract first")

        try:
            log("START", "Pipeline started")

            # -------- MODULE 4 -------- #
            module4 = run_module4(self.dataset) or {}
            inference = module4.get("inference", {}).get("batch", {})
            preds = inference.get("predictions", [])
            probs = inference.get("probabilities", [])

            # -------- MODULE 5 -------- #
            df_eval = pd.DataFrame(self.dataset["X"]).iloc[: len(preds)]
            y_eval = pd.Series(self.dataset["Y"]).iloc[: len(preds)]

            module5 = run_module5(
                df=df_eval,
                y_true=y_eval,
                y_pred=pd.Series(preds),
                bias_columns=self.bias_columns,
            ) or {}

            # -------- MODULE 6 -------- #
            module6 = run_module6(
                df=pd.DataFrame(self.dataset["X"]),
                X_train=pd.DataFrame(self.dataset["X"]),
                y_train=pd.Series(self.dataset["Y"]),
                bias_columns=self.bias_columns,
                module5_results=module5,
            ) or {}

            base_probs = [float(p) for p in probs[0]] if probs else [0.5, 0.5]
            debiased_probs = _extract_debiased_probabilities(base_probs, module6)

            # -------- MODULE 7 -------- #
            context = context_service.get_context() or ContextSchema.validate({
                "region": "urban",
                "hospital_type": "private",
                "resource_level": "medium",
                "time_of_day": "day",
            })

            context_service.set_context(context)

            final_probs = apply_context_probabilities(debiased_probs, context) or debiased_probs
            final_probs = [float(p) for p in final_probs]
            ctx = context_confidence(context)

            if isinstance(ctx, tuple) and len(ctx) >= 2:
                context_conf, reason = ctx[0], ctx[1]
            elif isinstance(ctx, dict):
                context_conf = ctx.get("confidence", "unknown")
                reason = ctx.get("reason", "")
            else:
                context_conf, reason = "unknown", ""

            # -------- MODULE 8 -------- #
            features = module4.get("model", {}).get("feature_importance", {})

            decision = run_module8(
                probabilities=final_probs,
                original_probabilities=debiased_probs,
                fairness_output=module5,
                top_features=features,
            ) or {"decision": "reject", "confidence": 0.5}

            # -------- MODULE 9 -------- #
            resources = {"low": 5, "medium": 10, "high": 15}
            available = resources.get(context.get("resource_level"), 8)

            validation = validate_decision(
                decision_output=decision,
                available_resources=available,
            )

            # -------- MODULE 10 -------- #
            compliance = apply_compliance(
                dataset_df=pd.DataFrame(self.dataset["X"]),
                user="pipeline_user",
                role="analyst",
                action="run_pipeline",
                decision=decision.get("decision", "reject"),
            )

            # -------- MODULE 11 -------- #
            monitoring = run_monitoring(
                df=pd.DataFrame(self.dataset["X"]),
                fairness_output=module5,
                decision_output=decision,
                bias_columns=self.bias_columns,
            )

            # -------- FINAL -------- #
            self.results = _deep_strip_runtime({
                "decision": decision,
                "validation": validation,
                "compliance": compliance,
                "monitoring": monitoring,
                "fairness": module5,
                "context": {
                    "values": context,
                    "confidence": context_conf,
                    "reason": reason,
                    "base_probability": debiased_probs,
                    "final_probability": final_probs,
                },
            })

            log("END", "Pipeline complete")
            return self.results

        except Exception as e:
            log("ERROR", str(e))
            traceback.print_exc()
            raise