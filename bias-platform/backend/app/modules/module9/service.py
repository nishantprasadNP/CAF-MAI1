from typing import Any


DECISION_MAP = {
    "approve": "allocate_resources",
    "reject": "no_action",
}

RESOURCE_REQUIREMENTS = {
    "allocate_resources": 10,
    "no_action": 0,
}


def check_feasibility(action: str, available_resources: int) -> bool:
    required = RESOURCE_REQUIREMENTS.get(action, 0)
    return required <= available_resources


def validate_decision(decision_output: dict[str, Any], available_resources: int = 8) -> dict[str, Any]:
    decision = decision_output.get("decision", "reject")
    action = DECISION_MAP.get(decision, "no_action")
    feasible = check_feasibility(action, available_resources)
    if feasible:
        return {
            "status": "feasible",
            "action": action,
            "required_resources": RESOURCE_REQUIREMENTS.get(action, 0),
            "available_resources": available_resources,
            "reason": "sufficient resources",
        }
    partial_allocation = max(0, min(available_resources, RESOURCE_REQUIREMENTS.get(action, 0)))
    return {
        "status": "fallback",
        "action": action,
        "required_resources": RESOURCE_REQUIREMENTS.get(action, 0),
        "available_resources": available_resources,
        "reason": "insufficient resources",
        "alternative": f"partial_allocation:{partial_allocation}" if partial_allocation > 0 else "delay_action",
    }
