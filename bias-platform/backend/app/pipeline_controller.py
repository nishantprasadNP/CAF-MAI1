from io import BytesIO
from typing import Any
import logging
import math
import re
import threading

import numpy as np
import pandas as pd

from app.config import MAX_BIAS_GROUPS
from app.modules.module0.data_contract import DataContract
from app.modules.module4.service import run_module4
from app.modules.module5.service import run_module5
from app.modules.module6.service import apply_debiasing, run_module6
from app.modules.module8.decision import run_module8
from app.modules.module9.service import validate_decision
from app.modules.module11.service import run_monitoring

logger = logging.getLogger(__name__)


# ---------------- UTILS ---------------- #

def _deep_strip_runtime(obj: Any) -> Any:
    """Drop "_runtime" entries and make the payload JSON safe."""
    if isinstance(obj, dict):
        return {str(k): _deep_strip_runtime(v) for k, v in obj.items() if k != "_runtime"}
    if isinstance(obj, (list, tuple)):
        return [_deep_strip_runtime(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (float, np.floating)):
        obj = float(obj)
        return None if math.isnan(obj) or math.isinf(obj) else obj
    return obj


def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    # Parse straight from bytes (no decoded copy of large files); latin-1 never fails.
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(BytesIO(file_bytes), encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode the CSV file.")


def _clean_feature_name(name: str) -> str:
    for prefix in ("numeric__", "categorical__"):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _extract_top_features(pipeline, limit: int = 5) -> dict[str, float]:
    try:
        model = pipeline.named_steps["model"]
        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
        coefs = model.coef_[0]
    except Exception:
        logger.warning("Could not extract feature importance", exc_info=True)
        return {}

    ranked = sorted(zip(feature_names, coefs), key=lambda item: abs(item[1]), reverse=True)[:limit]
    return {_clean_feature_name(str(name)): float(value) for name, value in ranked}


def _binary_columns(df: pd.DataFrame) -> list[str]:
    """Columns with exactly two distinct values, i.e. usable as a target."""
    out = []
    sample = df.head(10_000)
    for col in df.columns:
        # Cheap rejection on a sample before scanning millions of rows.
        if sample[col].nunique(dropna=True) > 2:
            continue
        if df[col].nunique(dropna=True) == 2:
            out.append(col)
    return out


_TARGET_NAME_HINTS = re.compile(r"target|label|outcome|class|survived|approved|default|fraud|churn|^y$", re.I)


def _suggest_target(binary_columns: list[str]) -> str | None:
    named = [c for c in binary_columns if _TARGET_NAME_HINTS.search(c)]
    if named:
        return named[0]
    return binary_columns[-1] if binary_columns else None


# ---------------- PIPELINE ---------------- #

class BiasPipeline:
    def __init__(self):
        self.lock = threading.Lock()
        self.raw_df = None
        self.dataset = None
        self.bias_columns = []
        self.results = None
        self._decision_state = None
        # Bias gap history per (columns, target, bias selection), for drift tracking.
        self._bias_history: dict[tuple, list[float]] = {}

    # ---------------- DATA ---------------- #

    def upload_data(self, file_bytes: bytes):
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        logger.info("Reading CSV (%d bytes)", len(file_bytes))
        try:
            df = _read_csv(file_bytes)
        except pd.errors.EmptyDataError:
            raise ValueError("Uploaded file has no columns. Is it a CSV?")

        if df.empty:
            raise ValueError("CSV has a header but no data rows.")

        df.columns = [str(c).strip() for c in df.columns]
        if len(set(df.columns)) != len(df.columns):
            raise ValueError("CSV has duplicate column names.")

        self.raw_df = df
        self.dataset = None
        self.bias_columns = []
        self.results = None
        self._decision_state = None
        binary_columns = _binary_columns(df)
        return {
            "columns": df.columns.tolist(),
            "rows": len(df),
            "binary_columns": binary_columns,
            "suggested_target": _suggest_target(binary_columns),
        }

    def initialize_contract(self, target_column: str):
        if self.raw_df is None:
            raise ValueError("Upload a CSV before choosing a target column.")

        contract = DataContract(
            df=self.raw_df,
            target_column=target_column,
            bias_columns=[],
        )
        self.dataset = contract.build()
        self.bias_columns = []
        self.results = None
        self._decision_state = None
        return {
            "rows": len(self.dataset["Y"]),
            "columns": self.dataset["X"].columns.tolist(),
            "B_user": [],
            "metadata": self.dataset["metadata"],
        }

    def select_bias(self, bias_columns: list[str]):
        if self.dataset is None:
            raise ValueError("Choose a target column before selecting bias columns.")

        target = self.dataset["metadata"]["target_column"]
        unknown = [c for c in bias_columns if c not in self.raw_df.columns]
        if unknown:
            raise ValueError(f"Bias columns not found in dataset: {unknown}")
        if target in bias_columns:
            raise ValueError(f"'{target}' is the target column and cannot also be a bias column.")

        id_columns = [c for c in bias_columns if c in self.dataset["metadata"].get("excluded_id_columns", [])]
        if id_columns:
            raise ValueError(
                f"{id_columns} look like identifier columns (almost every value is unique) "
                "and cannot be used as sensitive attributes."
            )

        for col in bias_columns:
            groups = self.raw_df[col].nunique(dropna=True)
            if groups > MAX_BIAS_GROUPS:
                raise ValueError(
                    f"'{col}' has {groups:,} distinct values; a sensitive attribute needs at most "
                    f"{MAX_BIAS_GROUPS} groups (e.g. gender, region, age band)."
                )

        self.bias_columns = list(dict.fromkeys(bias_columns))
        self.dataset["B_user"] = self.bias_columns
        self.results = None
        self._decision_state = None
        return {"B_user": self.bias_columns}

    # ---------------- DECISION (per record) ---------------- #

    def decide(self, row_index: int, available_resources: int = 8) -> dict[str, Any]:
        state = self._decision_state
        if state is None:
            raise ValueError("Run the pipeline before requesting a decision.")

        n_rows = len(state["original_probs"])
        if not 0 <= row_index < n_rows:
            raise ValueError(f"row_index must be between 0 and {n_rows - 1}.")

        p_orig = float(state["original_probs"][row_index])
        p_used = float(state["debiased_probs"][row_index])

        decision = run_module8(
            probabilities=[1 - p_used, p_used],
            original_probabilities=[1 - p_orig, p_orig],
            fairness_output=state["fairness"],
            top_features=state["top_features"],
        )
        decision["row_index"] = row_index
        decision["n_rows"] = n_rows
        decision["debiased"] = state["debiased"]
        decision["predicted_class"] = state["class_labels"].get(str(decision["label"]))

        validation = validate_decision(decision, available_resources)

        bundle = _deep_strip_runtime({"decision": decision, "validation": validation})
        if self.results is not None:
            self.results.update(bundle)
        return bundle

    # ---------------- MAIN ---------------- #

    def run_pipeline(self, row_index: int = 0, available_resources: int = 8):
        if self.dataset is None:
            raise ValueError("Upload a CSV and choose a target column before running the pipeline.")
        if not self.bias_columns:
            raise ValueError("Select at least one bias (sensitive attribute) column before running the pipeline.")

        self.results = None
        self._decision_state = None

        try:
            logger.info("Pipeline started")

            # ================= MODULE 4 ================= #
            logger.info("M4: training")
            module4 = run_module4(self.dataset)
            runtime = module4["_runtime"]
            baseline = runtime["pipeline"]
            x_train, y_train = runtime["x_train"], runtime["y_train"]
            x_test, y_test = runtime["x_test"], runtime["y_test"]

            # ================= MODULE 5 (BEFORE, held-out) ================= #
            logger.info("M5: fairness before mitigation")
            y_pred_before = pd.Series(baseline.predict(x_test))
            module5_before = run_module5(
                df=x_test,
                y_true=y_test,
                y_pred=y_pred_before,
                bias_columns=self.bias_columns,
            )

            # ================= MODULE 6 ================= #
            logger.info("M6: mitigation")
            module6 = run_module6(
                X_train=x_train,
                y_train=y_train,
                bias_columns=self.bias_columns,
                module5_results=module5_before,
            )
            debias_runtime = module6.get("_runtime")

            if debias_runtime:
                y_pred_after = pd.Series(apply_debiasing(debias_runtime, x_test)[0])
            else:
                y_pred_after = y_pred_before

            # ================= MODULE 5 (AFTER, held-out) ================= #
            logger.info("M5: fairness after mitigation")
            module5_after = run_module5(
                df=x_test,
                y_true=y_test,
                y_pred=y_pred_after,
                bias_columns=self.bias_columns,
                explain=True,
            )

            before_bias = module5_before["summary"]["bias_gap"]
            after_bias = module5_after["summary"]["bias_gap"]
            module6["debiasing_effect"] = {
                "before": round(before_bias, 4),
                "after": round(after_bias, 4),
                "improvement": round(before_bias - after_bias, 4),
                "accuracy_before": round(module5_before["accuracy"], 4),
                "accuracy_after": round(module5_after["accuracy"], 4),
                "changed": abs(before_bias - after_bias) > 0.01,
            }

            # ================= PER-RECORD SCORING STATE ================= #
            full_x = self.dataset["X"]
            original_probs = baseline.predict_proba(full_x)[:, 1]
            debiased_probs = (
                apply_debiasing(debias_runtime, full_x)[1] if debias_runtime else original_probs
            )

            self._decision_state = {
                "original_probs": original_probs,
                "debiased_probs": debiased_probs,
                "debiased": bool(debias_runtime),
                "fairness": module5_after,
                "top_features": _extract_top_features(baseline),
                "class_labels": self.dataset["metadata"]["class_labels"],
            }

            # ================= MODULE 8 + 9 ================= #
            logger.info("M8/M9: decision + validation for row %d", row_index)
            bundle = self.decide(row_index, available_resources)

            # ================= MODULE 11 ================= #
            logger.info("M11: monitoring")
            history_key = (
                tuple(self.raw_df.columns),
                len(self.raw_df),
                self.dataset["metadata"]["target_column"],
                tuple(sorted(self.bias_columns)),
            )
            monitoring = run_monitoring(
                reference_df=x_train,
                current_df=x_test,
                fairness_output=module5_after,
                bias_history=self._bias_history.setdefault(history_key, []),
            )

            # ================= FINAL ================= #
            self.results = _deep_strip_runtime({
                **bundle,
                "model": module4["model"],
                "class_labels": self.dataset["metadata"]["class_labels"],
                "monitoring": monitoring,
                "fairness": module5_after,
                "fairness_before": module5_before,
                "module6": module6,
            })

            logger.info("Pipeline complete")
            return self.results

        except Exception:
            self._decision_state = None
            logger.exception("Pipeline failed")
            raise
