from app.modules.module7.service import calculate_bias_score, context_service


def build_final_decision(probabilities: list[float]) -> dict:
    if not probabilities:
        return {
            "original_probabilities": [],
            "adjusted_probabilities": [],
            "final_decision": -1,
            "confidence": 0.0,
            "bias_score": 0.0,
            "context_weights": {},
        }

    apply_result = context_service.apply_context_to_predictions(probabilities)
    adjusted = apply_result["adjusted_probabilities"]
    confidence = max(adjusted) if adjusted else 0.0
    final_decision = adjusted.index(confidence) if adjusted else -1
    bias_result = calculate_bias_score(probabilities)

    return {
        "original_probabilities": apply_result["original_probabilities"],
        "adjusted_probabilities": adjusted,
        "final_decision": final_decision,
        "confidence": confidence,
        "bias_score": float(bias_result["bias_score"]),
        "context_weights": apply_result["context_weights"],
    }
