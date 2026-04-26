from typing import Any


DECISION_MAP = {
    "approve": "allocate_resources",
    "reject": "no_action",
}


# ---------------- SAFE HELPERS ---------------- #

def _safe_confidence(value: Any) -> float:
    try:
        val = float(value)
        return max(0.0, min(1.0, val))
    except Exception:
        return 0.5


def _extract_bias_flag(decision_output: dict) -> str:
    return str(decision_output.get("bias_flag", "low")).lower()


# ---------------- RESOURCE LOGIC ---------------- #

def compute_required_resources(decision_output: dict[str, Any], action: str) -> int:
    if action == "no_action":
        return 0

    confidence = _safe_confidence(decision_output.get("confidence", 0.5))

    # 🔥 stronger scaling (more realistic)
    required = max(1, min(10, int(confidence * 10)))
    return required


def check_feasibility(required: int, available: int) -> bool:
    return required <= max(0, available)


# ---------------- RISK SCORING ---------------- #

def compute_risk_level(confidence: float, bias_flag: str) -> str:
    if bias_flag == "high":
        return "high"
    if confidence < 0.6:
        return "moderate"
    return "low"


# ---------------- MAIN VALIDATION ---------------- #

def validate_decision(
    decision_output: dict[str, Any],
    available_resources: int = 8,
    required_resources: int | None = None,
) -> dict[str, Any]:

    decision = str(decision_output.get("decision", "reject")).lower()
    action = DECISION_MAP.get(decision, "no_action")

    available_resources = max(0, int(available_resources))
    confidence = _safe_confidence(decision_output.get("confidence", 0.5))
    bias_flag = _extract_bias_flag(decision_output)

    # ---------------- REQUIRED ---------------- #
    if required_resources is None:
        required_resources = compute_required_resources(decision_output, action)

    # ---------------- FEASIBILITY ---------------- #
    feasible = check_feasibility(required_resources, available_resources)

    # ---------------- RISK ---------------- #
    risk_level = compute_risk_level(confidence, bias_flag)

    # ---------------- SUCCESS ---------------- #
    if feasible:
        return {
            "status": "feasible",
            "action": action,

            "required_resources": required_resources,
            "available_resources": available_resources,

            "utilization": round(required_resources / max(available_resources, 1), 2),

            "confidence": confidence,
            "bias_flag": bias_flag,
            "risk_level": risk_level,

            "reason": (
                f"Decision is feasible with {required_resources} resources available. "
                f"Risk level is {risk_level}."
            ),
        }

    # ---------------- FALLBACK ---------------- #
    partial_allocation = max(0, min(available_resources, required_resources))

    if partial_allocation > 0:
        alternative = f"partial_allocation:{partial_allocation}"
    else:
        alternative = "delay_action"

    return {
        "status": "fallback",
        "action": action,

        "required_resources": required_resources,
        "available_resources": available_resources,

        "utilization": round(partial_allocation / max(required_resources, 1), 2),

        "confidence": confidence,
        "bias_flag": bias_flag,
        "risk_level": risk_level,

        "reason": (
            f"Insufficient resources. Required: {required_resources}, "
            f"available: {available_resources}. Risk level is {risk_level}."
        ),

        "alternative": alternative,
    }