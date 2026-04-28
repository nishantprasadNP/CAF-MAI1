from sklearn.metrics import accuracy_score, f1_score
import math

from app.modules.module5.bias_gap import compute_bias_gap
from app.modules.module5.fairness import compute_fairness_metrics
from app.modules.module5.intersectional import compute_intersectional_metrics
from app.modules.module5.subgroup import compute_subgroup_metrics

try:
    from app.utils.gemini_client import generate_text
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


def _safe_float(x):
    try:
        val = float(x)
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val
    except Exception:
        return 0.0


def _interpret_bias(bias_gap: float) -> dict:
    if bias_gap < 0.05:
        return {"bias_level": "low", "message": "Model is fairly balanced"}
    elif bias_gap < 0.15:
        return {"bias_level": "moderate", "message": "Some disparity detected across groups"}
    else:
        return {"bias_level": "high", "message": "Significant bias detected across subgroups"}


def _generate_ai_insight(summary, bias_gaps):
    if not GEMINI_AVAILABLE:
        return None

    try:
        prompt = f"""
        Analyze fairness of a model:

        Bias Gap: {summary.get("bias_gap")}
        Demographic Parity: {summary.get("demographic_parity")}
        Equal Opportunity: {summary.get("equal_opportunity")}

        Give a short 2-line explanation of fairness issues.
        """

        return generate_text(prompt)
    except Exception:
        return None


# ---------------- MAIN ---------------- #

def run_module5(df, y_true, y_pred, bias_columns):

    # ---------------- GLOBAL METRICS ---------------- #
    try:
        accuracy = _safe_float(accuracy_score(y_true, y_pred))
        f1 = _safe_float(f1_score(y_true, y_pred, zero_division=0))
    except Exception:
        accuracy = 0.0
        f1 = 0.0

    # ---------------- SUBGROUP ---------------- #
    subgroup_metrics = compute_subgroup_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- BIAS GAP ---------------- #
    bias_gaps = compute_bias_gap(subgroup_metrics=subgroup_metrics)

    # ---------------- INTERSECTIONAL ---------------- #
    intersectional = compute_intersectional_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- FAIRNESS ---------------- #
    fairness_metrics = compute_fairness_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
        bias_columns=bias_columns,
    )

    # ---------------- SUMMARY ---------------- #
    summary = {
        "demographic_parity": 0.0,
        "equal_opportunity": 0.0,
        "bias_gap": 0.0,
        "groups": {},
    }

    dp_values = []
    eo_values = []

    if isinstance(fairness_metrics, dict):
        for column_payload in fairness_metrics.values():
            if not isinstance(column_payload, dict):
                continue

            column_groups = column_payload.get("groups", {})
            for group, metric_values in column_groups.items():

                dp = metric_values.get("demographic_parity")
                eo = metric_values.get("equal_opportunity")

                if isinstance(dp, (int, float)):
                    dp_values.append(dp)
                    summary["groups"][str(group)] = round(dp, 4)

                if isinstance(eo, (int, float)):
                    eo_values.append(eo)

    if dp_values:
        summary["demographic_parity"] = round(sum(dp_values) / len(dp_values), 4)

    if eo_values:
        summary["equal_opportunity"] = round(sum(eo_values) / len(eo_values), 4)

    gap_values = [
        val
        for col in bias_gaps.values()
        for val in col.values()
        if isinstance(val, (int, float))
    ]

    if gap_values:
        summary["bias_gap"] = round(max(gap_values), 4)

    # ---------------- GLOBAL CONFUSION MATRIX ---------------- #
    from sklearn.metrics import confusion_matrix
    try:
        cm = confusion_matrix(y_true, y_pred)
        # Handle binary or multiclass
        if cm.size == 4:
            tn, fp, fn, tp = cm.ravel()
            global_cm = {
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp)
            }
        else:
            global_cm = cm.tolist()
    except Exception:
        global_cm = {"tn": 0, "fp": 0, "fn": 0, "tp": 0}

    # ---------------- OUTCOME DISTRIBUTION ---------------- #
    try:
        y_true_counts = pd.Series(y_true).value_counts().to_dict()
        y_pred_counts = pd.Series(y_pred).value_counts().to_dict()
        outcome_distribution = {
            "actual": {str(k): int(v) for k, v in y_true_counts.items()},
            "predicted": {str(k): int(v) for k, v in y_pred_counts.items()}
        }
    except Exception:
        outcome_distribution = {"actual": {}, "predicted": {}}

    # ---------------- INTERPRETATION ---------------- #
    insight = _interpret_bias(summary["bias_gap"])

    # ---------------- GEMINI (OPTIONAL) ---------------- #
    ai_explanation = _generate_ai_insight(summary, bias_gaps)

    insight["ai_explanation"] = ai_explanation

    return {
        "accuracy": accuracy,
        "f1": f1,
        "num_fairness_metrics": len(fairness_metrics) if isinstance(fairness_metrics, dict) else 0,
        "subgroup_metrics": subgroup_metrics,
        "bias_gaps": bias_gaps,
        "intersectional": intersectional,
        "fairness_metrics": fairness_metrics,
        "summary": summary,
        "insight": insight,
        "global_confusion_matrix": global_cm,
        "outcome_distribution": outcome_distribution,
    }