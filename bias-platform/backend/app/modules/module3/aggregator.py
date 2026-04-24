from typing import Any


def aggregate_results(
    dataset: dict[str, Any],
    profile: dict[str, Any],
    module2_result: dict[str, Any],
    module4_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = sorted(
        set(dataset.get("B_user", []))
        | set(dataset.get("B_suggested", []))
        | set(dataset.get("B_hidden", []))
    )
    return {
        "dataset": dataset,
        "profile": profile,
        "module2": module2_result,
        "module4": module4_result,
        "registry": registry,
    }
