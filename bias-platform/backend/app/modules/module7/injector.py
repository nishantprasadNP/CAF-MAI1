def apply_context(probabilities: list[float], context_weights: dict) -> list[float]:
    adjusted = []
    total_adjustment = sum(context_weights.values()) if context_weights else 0

    for prob in probabilities:
        new_prob = max(0.0, min(1.0, float(prob) + total_adjustment))
        adjusted.append(new_prob)

    if not adjusted:
        return adjusted

    total = sum(adjusted)
    if total == 0:
        uniform_prob = 1 / len(adjusted)
        return [uniform_prob for _ in adjusted]

    return [p / total for p in adjusted]
