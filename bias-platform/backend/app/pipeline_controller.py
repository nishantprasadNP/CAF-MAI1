from io import StringIO
from typing import Any
import traceback
import pandas as pd
import math

from app.modules.module0.data_contract import DataContract
from app.modules.module4.service import run_module4
from app.modules.module5.service import run_module5
from app.modules.module6.service import run_module6
from app.modules.module8.service import run_module8
from app.modules.module9.service import validate_decision
from app.modules.module11.service import run_monitoring


# ---------------- LOG ---------------- #

def log(stage: str, msg: str):
    print(f"[PIPELINE] [{stage}] {msg}")


# ---------------- UTILS ---------------- #

def _deep_strip_runtime(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_strip_runtime(v) for k, v in obj.items() if k != "_runtime"}
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
        contract = DataContract(
            df=self.raw_df,
            target_column=target_column,
            bias_columns=[]
        )
        self.dataset = contract.build()
        return self.dataset

    def select_bias(self, bias_columns: list[str]):
        self.bias_columns = bias_columns
        self.dataset["B_user"] = bias_columns
        return {"B_user": bias_columns}

    # ---------------- MAIN PIPELINE ---------------- #

    def run_pipeline(self):
        try:
            log("START", "Pipeline started")

            # ================= MODULE 4 ================= #
            log("M4", "Training + Inference")

            module4 = run_module4(self.dataset) or {}
            runtime = module4.get("_runtime", {})
            pipeline = runtime.get("pipeline")

            if pipeline is None:
                raise ValueError("Model pipeline not found in Module 4")

            df_full = pd.DataFrame(self.dataset["X"]).reset_index(drop=True)
            y_full = pd.Series(self.dataset["Y"]).reset_index(drop=True)

            # restore bias columns
            for col in self.bias_columns:
                if col not in df_full.columns and col in self.raw_df.columns:
                    df_full[col] = self.raw_df[col].values

            # predictions (baseline)
            y_pred_full = pd.Series(pipeline.predict(df_full)).reset_index(drop=True)

            # ================= MODULE 5 (BEFORE) ================= #
            log("M5", "Fairness (before debiasing)")

            module5_before = run_module5(
                df=df_full,
                y_true=y_full,
                y_pred=y_pred_full,
                bias_columns=self.bias_columns,
            ) or {}

            print("\n[M5 BEFORE DEBUG]")
            print(module5_before)

            # ================= MODULE 6 ================= #
            log("M6", "Debiasing")

            module6 = run_module6(
                df=df_full,
                X_train=pd.DataFrame(self.dataset["X"]),
                y_train=pd.Series(self.dataset["Y"]),
                bias_columns=self.bias_columns,
                module5_results=module5_before,
            ) or {}

            print("\n[M6 DEBUG]")
            print(module6)

            # ================= APPLY DEBIASING ================= #
            debias_preds = module6.get("reweighted_results", {}).get("predictions")
            debias_probs = module6.get("reweighted_results", {}).get("probabilities")

            if debias_preds:
                y_pred_used = pd.Series(debias_preds, index=df_full.index)
                print("\n[PIPELINE] Using DEBIASED predictions")
            else:
                y_pred_used = y_pred_full
                print("\n[PIPELINE] Using ORIGINAL predictions")

            # ================= MODULE 5 (AFTER) ================= #
            log("M5", "Fairness (after debiasing)")

            module5_after = run_module5(
                df=df_full,
                y_true=y_full,
                y_pred=y_pred_used,
                bias_columns=self.bias_columns,
            ) or {}

            print("\n[M5 AFTER DEBUG]")
            print(module5_after)

            # ================= MODULE 8 ================= #
            log("M8", "Decision")

            if debias_probs:
                p1 = float(debias_probs[0])
                probs_used = [1 - p1, p1]
            else:
                probs = pipeline.predict_proba(df_full)[0]
                probs_used = _normalize_probs(probs)

            decision = run_module8(
                probabilities=probs_used,
                original_probabilities=probs_used,
                fairness_output=module5_after,
                top_features={},
            ) or {}

            print("\n[M8 DEBUG]")
            print(decision)

            # ================= MODULE 9 ================= #
            log("M9", "Validation")

            validation = validate_decision(decision, 10)

            print("\n[M9 DEBUG]")
            print(validation)

            # ================= MODULE 11 ================= #
            log("M11", "Monitoring")

            monitoring = run_monitoring(
                df=df_full,
                fairness_output=module5_after,
                decision_output=decision,
                bias_columns=self.bias_columns,
            )

            print("\n[M11 DEBUG]")
            print(monitoring)

            # ================= FINAL ================= #
            self.results = _deep_strip_runtime({
                "decision": decision,
                "validation": validation,
                "monitoring": monitoring,
                "fairness": module5_after,
                "module6": module6,
            })

            log("END", "Pipeline complete")

            return self.results

        except Exception as e:
            log("ERROR", str(e))
            traceback.print_exc()
            raise