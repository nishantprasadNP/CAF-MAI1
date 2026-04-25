def encode_context(context: dict) -> dict:
    weights = {}

    if context.get("region") == "rural":
        weights["region"] = -0.1
    elif context.get("region") == "urban":
        weights["region"] = 0.05

    if context.get("resource_level") == "low":
        weights["resource_level"] = -0.15
    elif context.get("resource_level") == "high":
        weights["resource_level"] = 0.1

    if context.get("hospital_type") == "government":
        weights["hospital_type"] = -0.05
    elif context.get("hospital_type") == "private":
        weights["hospital_type"] = 0.05

    if context.get("time_of_day") == "night":
        weights["time_of_day"] = -0.03
    elif context.get("time_of_day") == "day":
        weights["time_of_day"] = 0.02

    return weights
