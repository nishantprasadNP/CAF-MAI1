from typing import Any


DECISION_MAP = {
    "approve": "allocate_resources",
    "reject": "no_action",
}


def _safe_confidence(value: Any) -> float:
    try:
        val = float(value)
        if val < 0:
            return 0.0
        if val > 1:
            return 1.0
        return val
    except Exception:
        return 0.5


def compute_required_resources(decision_output: dict[str, Any], action: str) -> int:
    """
    Dynamically compute required resources based on model confidence.
    """
    if action == "no_action":
        return 0

    confidence = _safe_confidence(decision_output.get("confidence", 0.5))

    # Scale requirement (1–10 range)
    required = max(1, min(10, int(confidence * 10)))
    return required


def check_feasibility(required: int, available: int) -> bool:
    return required <= max(0, available)


def validate_decision(
    decision_output: dict[str, Any],
    available_resources: int = 8,
    required_resources: int | None = None,
) -> dict[str, Any]:

    decision = str(decision_output.get("decision", "reject")).lower()
    action = DECISION_MAP.get(decision, "no_action")

    available_resources = max(0, int(available_resources))

    # ---------------- REQUIRED ---------------- #
    if required_resources is None:
        required_resources = compute_required_resources(decision_output, action)

    # ---------------- FEASIBILITY ---------------- #
    feasible = check_feasibility(required_resources, available_resources)

    if feasible:
        return {
            "status": "feasible",
            "action": action,
            "required_resources": required_resources,
            "available_resources": available_resources,
            "utilization": round(required_resources / max(available_resources, 1), 2),
            "reason": f"sufficient resources (needed {required_resources}, available {available_resources})",
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
        "reason": f"insufficient resources (needed {required_resources}, available {available_resources})",
        "alternative": alternative,
    }