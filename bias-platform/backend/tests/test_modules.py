import numpy as np
import pandas as pd
import pytest

from app.modules.module0.data_contract import DataContract
from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module5.service import classify_bias, run_module5
from app.modules.module6.service import apply_debiasing, compute_reweighing_weights, run_module6
from app.modules.module8.decision import run_module8
from app.modules.module9.service import validate_decision
from app.modules.module11.service import run_monitoring


# ---------------- MODULE 0 ---------------- #

def test_contract_encodes_text_target():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": ["yes", "no", "yes", "no"]})
    ds = DataContract(df, "y", []).build()
    assert ds["Y"].tolist() == [1, 0, 1, 0]
    assert ds["metadata"]["class_labels"] == {"0": "no", "1": "yes"}


def test_contract_keeps_missing_values_for_imputer():
    df = pd.DataFrame({"x": [1.0, None], "s": ["a", None], "y": [0, 1]})
    row = DataContract(df, "y", []).build()["X"].iloc[1]
    assert pd.isna(row["x"])
    assert pd.isna(row["s"])


def test_contract_drops_rows_missing_target():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [0, None, 1]})
    ds = DataContract(df, "y", []).build()
    assert ds["Y"].tolist() == [0, 1]
    assert ds["metadata"]["dropped_rows_missing_target"] == 1


def test_contract_excludes_identifier_columns():
    n = 40
    df = pd.DataFrame({"customer_id": [f"C{i}" for i in range(n)], "kind": ["a", "b"] * 20, "y": [0, 1] * 20})
    ds = DataContract(df, "y", []).build()
    assert ds["metadata"]["excluded_id_columns"] == ["customer_id"]
    assert list(ds["X"].columns) == ["kind"]


@pytest.mark.parametrize(
    "target, message",
    [
        ([0, 1, 2, 0, 1, 2], "3 distinct values"),
        ([1, 1, 1, 1, 1, 1], "only one distinct value"),
        (list(np.linspace(0, 1, 30)), "continuous"),
    ],
)
def test_contract_rejects_non_binary_targets(target, message):
    df = pd.DataFrame({"x": range(len(target)), "y": target})
    with pytest.raises(ValueError, match=message):
        DataContract(df, "y", []).build()


# ---------------- MODULE 5 ---------------- #

def test_fairness_metrics_shape():
    df = pd.DataFrame({"gender": ["A", "A", "A", "B", "B", "B", "B", "A"]})
    y_true = pd.Series([1, 0, 1, 0, 1, 0, 1, 0])
    y_pred = pd.Series([1, 1, 1, 0, 0, 0, 1, 0])

    result = compute_fairness_metrics(df=df, y_true=y_true, y_pred=y_pred, bias_columns=["gender"])
    payload = result["gender"]
    assert {"equalized_odds", "predictive_parity", "group_confusion_matrix"} <= payload.keys()
    assert payload["demographic_parity"]["max_diff"] == pytest.approx(0.75 - 0.25)


def test_module5_outputs_distribution_and_gap():
    df = pd.DataFrame({"g": ["A"] * 4 + ["B"] * 4})
    y_true = pd.Series([1, 1, 0, 0, 1, 1, 0, 0])
    y_pred = pd.Series([1, 1, 1, 1, 0, 0, 0, 0])

    out = run_module5(df=df, y_true=y_true, y_pred=y_pred, bias_columns=["g"])
    assert out["outcome_distribution"]["predicted"] == {"1": 4, "0": 4}
    assert out["summary"]["bias_gap"] == out["bias_gaps"]["g"]["gap"]
    assert out["insight"]["bias_level"] == "high"
    assert out["global_confusion_matrix"] == {"tn": 2, "fp": 2, "fn": 2, "tp": 2}


def test_classify_bias_thresholds():
    assert classify_bias(0.05) == "low"
    assert classify_bias(0.15) == "moderate"
    assert classify_bias(0.25) == "high"


# ---------------- MODULE 6 ---------------- #

def test_reweighing_balances_group_label_mass():
    groups = pd.Series(["A"] * 6 + ["B"] * 4)
    y = pd.Series([1, 1, 1, 1, 1, 0, 1, 0, 0, 0])
    w = compute_reweighing_weights(groups, y)
    frame = pd.DataFrame({"g": groups, "y": y, "w": w})
    weighted_rate = frame.groupby("g").apply(lambda d: (d.w * d.y).sum() / d.w.sum(), include_groups=False)
    assert weighted_rate["A"] == pytest.approx(weighted_rate["B"])


def test_module6_skips_when_gap_small():
    out = run_module6(pd.DataFrame({"g": ["A"]}), pd.Series([1]), ["g"], {"summary": {"bias_gap": 0.01}})
    assert out["status"] == "skipped"


def test_module6_reduces_gap_and_stays_in_range(biased_df):
    ds = DataContract(biased_df, "approved", []).build()
    X, y = pd.DataFrame(ds["X"]), pd.Series(ds["Y"])

    out = run_module6(X, y, ["sex"], {"summary": {"bias_gap": 0.4}})
    assert out["status"] == "applied"
    preds, probs = apply_debiasing(out["_runtime"], X)
    assert ((probs >= 0) & (probs <= 1)).all()
    assert ((probs >= 0.5).astype(int) == preds).all()

    rates = pd.Series(preds).groupby(X["sex"]).mean()
    assert abs(rates["M"] - rates["F"]) < 0.1


# ---------------- MODULE 8 ---------------- #

def test_module8_decision():
    result = run_module8(
        probabilities=[0.2, 0.8],
        original_probabilities=[0.3, 0.7],
        fairness_output={"summary": {"bias_gap": 0.25}, "bias_gaps": {}},
        top_features={"f3": 0.1, "f1": -0.8, "f2": 0.4, "f5": 0.2, "f4": 0.3, "f6": 0.05},
    )
    assert result["decision"] == "approve"
    assert result["confidence"] == 0.8
    assert result["bias_flag"] == "high"
    assert [f["feature"] for f in result["top_features"]] == ["f1", "f2", "f4", "f5", "f3"]
    assert result["original_probabilities"] == [0.3, 0.7]
    assert ".." not in result["explanation"]


# ---------------- MODULE 9 ---------------- #

def test_validation_fallback_when_resources_short():
    out = validate_decision({"decision": "approve", "confidence": 0.9}, available_resources=5)
    assert out["status"] == "fallback"
    assert out["alternative"] == "partial_allocation:5"


def test_validation_reject_needs_nothing():
    out = validate_decision({"decision": "reject", "confidence": 0.9}, available_resources=0)
    assert out["status"] == "feasible"
    assert out["required_resources"] == 0


# ---------------- MODULE 11 ---------------- #

def test_monitoring_baseline_then_trend():
    df = pd.DataFrame({"score": np.linspace(0, 1, 50)})
    history: list[float] = []

    first = run_monitoring(reference_df=df, current_df=df, fairness_output={"summary": {"bias_gap": 0.05}}, bias_history=history)
    assert first["trend"] == "baseline"
    assert first["bias_drift"] == 0.0
    assert first["data_drift"] == pytest.approx(0.0, abs=1e-6)

    second = run_monitoring(reference_df=df, current_df=df, fairness_output={"summary": {"bias_gap": 0.35}}, bias_history=history)
    assert second["trend"] == "increasing"
    assert second["bias_drift"] == pytest.approx(0.3)
    assert any("increased" in a for a in second["alerts"])


def test_monitoring_detects_shift():
    ref = pd.DataFrame({"x": np.linspace(0, 1, 200)})
    cur = pd.DataFrame({"x": np.linspace(0.6, 1, 200)})
    out = run_monitoring(reference_df=ref, current_df=cur, fairness_output={"summary": {"bias_gap": 0}}, bias_history=[])
    assert out["data_drift"] > 0.15
    assert "'x'" in out["alerts"][0]


def test_fairness_ignores_unused_categories():
    df = pd.DataFrame({"g": pd.Categorical(["A", "A", "B", "B"], categories=["A", "B", "C"])})
    out = run_module5(df=df, y_true=pd.Series([1, 0, 1, 0]), y_pred=pd.Series([1, 1, 0, 0]), bias_columns=["g"])
    assert list(out["subgroup_metrics"]["g"]) == ["A", "B"]
    assert list(out["fairness_metrics"]["g"]["groups"]) == ["A", "B"]
