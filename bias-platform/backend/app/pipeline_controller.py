from io import StringIO
from typing import Any
import traceback
import pandas as pd
import math
import numpy as np

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


# ---------------- FEATURE NAME EXTRACTION ---------------- #

def _get_feature_names(pipeline, X_df):
    """
    Handles:
    - Raw models
    - ColumnTransformer pipelines
    """
    try:
        if hasattr(pipeline, "named_steps"):
            for step in pipeline.named_steps.values():
                if hasattr(step, "get_feature_names_out"):
                    return list(step.get_feature_names_out())

        # fallback → original columns
        return list(X_df.columns)

    except Exception:
        return list(X_df.columns)


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

    # ---------------- MAIN ---------------- #

    def run_pipeline(self):
        try:
            log("START", "Pipeline started")

            # ================= MODULE 4 ================= #
            log("M4", "Training + Inference")

            module4 = run_module4(self.dataset) or {}
            runtime = module4.get("_runtime", {})
            pipeline = runtime.get("pipeline")

            if pipeline is None:
                raise ValueError("Model pipeline not found")

            df_full = pd.DataFrame(self.dataset["X"]).reset_index(drop=True)
            y_full = pd.Series(self.dataset["Y"]).reset_index(drop=True)

            # restore bias columns
            for col in self.bias_columns:
                if col not in df_full.columns and col in self.raw_df.columns:
                    df_full[col] = self.raw_df[col].values

            y_pred_full = pd.Series(pipeline.predict(df_full)).reset_index(drop=True)

            # ================= MODULE 5 (BEFORE) ================= #
            log("M5", "Fairness (before)")

            module5_before = run_module5(
                df=df_full,
                y_true=y_full,
                y_pred=y_pred_full,
                bias_columns=self.bias_columns,
            ) or {}

            # ================= MODULE 6 ================= #
            log("M6", "Debiasing")

            module6 = run_module6(
                df=df_full,
                X_train=pd.DataFrame(self.dataset["X"]),
                y_train=pd.Series(self.dataset["Y"]),
                bias_columns=self.bias_columns,
                module5_results=module5_before,
            ) or {}

            # ================= APPLY DEBIAS ================= #
            debias_preds = module6.get("reweighted_results", {}).get("predictions")
            debias_probs = module6.get("reweighted_results", {}).get("probabilities")

            if debias_preds:
                y_pred_used = pd.Series(debias_preds, index=df_full.index)
                print("[PIPELINE] Using DEBIASED predictions")
            else:
                y_pred_used = y_pred_full
                print("[PIPELINE] Using ORIGINAL predictions")

            # ================= MODULE 5 (AFTER) ================= #
            log("M5", "Fairness (after)")

            module5_after = run_module5(
                df=df_full,
                y_true=y_full,
                y_pred=y_pred_used,
                bias_columns=self.bias_columns,
            ) or {}

            # ================= FIX DEBIAS EFFECT ================= #
            before_bias = module5_before.get("summary", {}).get("bias_gap", 0.0)
            after_bias = module5_after.get("summary", {}).get("bias_gap", 0.0)

            module6["debiasing_effect"] = {
                "before": round(before_bias, 4),
                "after": round(after_bias, 4),
                "improvement": round(max(0.0, before_bias - after_bias), 4),
                "changed": abs(before_bias - after_bias) > 0.01,
            }

            # ================= ROBUST FEATURE EXTRACTION ================= #

            top_features = {}

            try:
                # 1️⃣ Get final model
                if hasattr(pipeline, "named_steps"):
                    model = list(pipeline.named_steps.values())[-1]
                else:
                    model = pipeline

                # 2️⃣ Get feature names properly
                feature_names = []

                for step in pipeline.named_steps.values():
                    if hasattr(step, "get_feature_names_out"):
                        try:
                            feature_names = list(step.get_feature_names_out())
                            break
                        except Exception:
                            pass

                # fallback → original columns
                if not feature_names:
                    feature_names = list(df_full.columns)

                # 3️⃣ Extract importance
                raw_importance = None

                if hasattr(model, "coef_"):
                    raw_importance = model.coef_[0]

                elif hasattr(model, "feature_importances_"):
                    raw_importance = model.feature_importances_

                # 4️⃣ Map safely
                if raw_importance is not None and len(raw_importance) > 0:
                    size = min(len(raw_importance), len(feature_names))

                    mapped = {
                        feature_names[i]: float(raw_importance[i])
                        for i in range(size)
                    }

                    # take top 5
                    sorted_feats = sorted(
                        mapped.items(),
                        key=lambda x: abs(x[1]),
                        reverse=True
                    )[:5]

                    top_features = dict(sorted_feats)

                print("\n[PIPELINE] Extracted top features:")
                print(top_features)

            except Exception as e:
                print("[PIPELINE FEATURE ERROR]", e)

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
                top_features=top_features,
            ) or {}

            # ================= MODULE 9 ================= #
            log("M9", "Validation")

            validation = validate_decision(decision, 10)

            # ================= MODULE 11 ================= #
            log("M11", "Monitoring")

            monitoring = run_monitoring(
                df=df_full,
                fairness_output=module5_after,
                decision_output=decision,
                bias_columns=self.bias_columns,
            )

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