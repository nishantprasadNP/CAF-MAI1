import os
import sys
from typing import Any, Callable

import pandas as pd

sys.path.append(os.path.abspath("backend"))
sys.path.append(os.path.abspath("bias-platform/backend"))


def _resolve_callable(module_path: str, preferred: str, fallbacks: list[str]) -> Callable[..., Any]:
    module = __import__(module_path, fromlist=["*"])
    for name in [preferred] + fallbacks:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise AttributeError(
        f"No callable found in {module_path}. Tried: {', '.join([preferred] + fallbacks)}"
    )


def test_module7_context() -> None:
    fn = _resolve_callable(
        "app.modules.module7.service",
        "compute_context_impact",
        ["process_context", "apply_context_probabilities"],
    )
    base_probs = [0.2, 0.6]
    context_probs = [0.1, 0.9]

    result = fn(base_probs=base_probs, context_probs=context_probs, dominant_feature="region")
    expected = context_probs[1] - base_probs[1]

    assert "cbas" in result, "Missing cbas"
    assert abs(float(result["cbas"]) - float(expected)) < 1e-9, "CBAS mismatch"
    assert result.get("confidence") == "high", "Confidence threshold logic failed"
    assert "region" in str(result.get("reason", "")), "Reason string missing dominant feature"


def test_module5_fairness() -> None:
    fn = _resolve_callable(
        "app.modules.module5.fairness",
        "compute_fairness_metrics",
        ["compute_fairness"],
    )
    df = pd.DataFrame(
        {
            "gender": ["A", "A", "A", "B", "B", "B", "B", "A"],
            "x": [1, 2, 3, 4, 5, 6, 7, 8],
        }
    )
    y_true = pd.Series([1, 0, 1, 0, 1, 0, 1, 0], index=df.index)
    y_pred = pd.Series([1, 1, 1, 0, 0, 0, 1, 0], index=df.index)

    result = fn(df=df, y_true=y_true, y_pred=y_pred, bias_columns=["gender"])
    assert "gender" in result, "Missing sensitive attribute results"
    payload = result["gender"]
    assert "equalized_odds" in payload, "Missing equalized_odds"
    assert "predictive_parity" in payload, "Missing predictive_parity"
    assert "group_confusion_matrix" in payload, "Missing group_confusion_matrix"


def test_module6_debiasing() -> None:
    fn = _resolve_callable(
        "app.modules.module6.service",
        "run_module6",
        ["debias"],
    )
    df = pd.DataFrame(
        {
            "gender": ["A", "A", "B", "B", "A", "B"],
            "feature1": [1.0, 2.0, 1.5, 3.5, 2.2, 3.1],
            "feature2": [10, 20, 15, 30, 25, 40],
        }
    )
    y_train = pd.Series([1, 1, 0, 0, 1, 0])
    module5_results = {"summary": {"bias_gap": 0.4}, "fairness_metrics": {}}

    result = fn(
        df=df,
        X_train=df[["feature1", "feature2"]],
        y_train=y_train,
        bias_columns=["gender"],
        module5_results=module5_results,
    )

    adjust = result.get("probability_adjustment", {})
    orig = adjust.get("original_probabilities", [])
    deb = adjust.get("debiased_probabilities", [])
    assert orig and deb, "Missing original/debiased probabilities"
    assert len(orig) == len(deb), "Probability length mismatch"
    assert any(abs(float(a) - float(b)) > 1e-9 for a, b in zip(orig, deb)), "Probabilities did not change"
    assert all(0.0 <= float(p) <= 1.0 for p in deb), "Debiased probabilities out of range [0,1]"


def test_module8_decision() -> None:
    fn = _resolve_callable(
        "app.modules.module8.decision",
        "run_module8",
        ["make_decision"],
    )
    result = fn(
        probabilities=[0.2, 0.8],
        original_probabilities=[0.3, 0.7],
        fairness_output={"bias_gaps": {"gender": {"A_B": 0.25}}},
        top_features={"f3": 0.1, "f1": 0.8, "f2": 0.4, "f5": 0.2, "f4": 0.3},
    )

    top = result.get("top_features", [])
    assert top, "Missing top_features"
    impacts = [float(item["impact"]) for item in top]
    assert impacts == sorted(impacts, reverse=True), "Top features not sorted descending"
    assert "contextContribution" in result, "Missing contextContribution"
    assert "biasContribution" in result, "Missing biasContribution"


def test_module10_compliance() -> None:
    fn = _resolve_callable(
        "app.modules.module10.service",
        "apply_compliance",
        ["check_compliance"],
    )
    df = pd.DataFrame({"gender": ["A", "B"], "score": [0.2, 0.7]})

    restricted = fn(
        dataset_df=df,
        user="u",
        role="analyst",
        action="run_pipeline",
        decision="approve",
        bias_risk="high",
        context_confidence="high",
    )
    assert restricted.get("status") == "restricted", "High bias should restrict compliance"
    assert "High bias risk" in restricted.get("violations", []), "Expected high bias violation missing"

    allowed = fn(
        dataset_df=df,
        user="u",
        role="analyst",
        action="run_pipeline",
        decision="approve",
        bias_risk="low",
        context_confidence="high",
    )
    assert allowed.get("status") == "allowed", "No-violation case should be allowed"
    assert allowed.get("violations") == [], "No-violation case should have empty violations"


def test_module11_monitoring() -> None:
    fn = _resolve_callable(
        "app.modules.module11.service",
        "run_monitoring",
        ["monitor"],
    )
    df = pd.DataFrame(
        {
            "gender": ["A", "A", "A", "B", "B", "B", "B", "A"],
            "score": [0.1, 0.2, 0.15, 0.7, 0.8, 0.75, 0.65, 0.12],
        }
    )

    first = fn(
        df=df,
        fairness_output={"bias_gaps": {"gender": {"A_B": 0.05}}},
        decision_output={"decision": "approve"},
        bias_columns=["gender"],
    )
    second = fn(
        df=df,
        fairness_output={"bias_gaps": {"gender": {"A_B": 0.35}}},
        decision_output={"decision": "approve"},
        bias_columns=["gender"],
    )

    assert "bias_drift" in second, "Missing bias_drift"
    assert abs(float(second["bias_drift"]) - abs(0.35 - 0.05)) < 1e-9, "Bias drift calculation mismatch"
    assert "alerts" in second, "Missing alerts"
    assert any("Bias increasing over time" in str(a) for a in second.get("alerts", [])), \
        "Expected drift alert not triggered"
    assert "bias_drift" in first, "Missing bias_drift in baseline run"


def main() -> None:
    tests = [
        ("Module 7", test_module7_context),
        ("Module 5", test_module5_fairness),
        ("Module 6", test_module6_debiasing),
        ("Module 8", test_module8_decision),
        ("Module 10", test_module10_compliance),
        ("Module 11", test_module11_monitoring),
    ]

    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {name} - {exc}")

    if failures == 0:
        print("All tests passed")
    else:
        print(f"{failures} failures")


if __name__ == "__main__":
    main()
