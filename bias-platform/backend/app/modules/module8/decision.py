from app.modules.module7.decision import build_final_decision


def explain_final(probabilities: list[float]) -> dict:
    result = build_final_decision(probabilities)
    confidence = float(result.get("confidence", 0.0))
    final_decision = result.get("final_decision", -1)
    bias_score = float(result.get("bias_score", 0.0))
    explanation = (
        f"The model selected class {final_decision} with confidence {confidence:.2f}. "
        f"Bias score is {bias_score:.4f} after context adjustment."
    )
    return {
        "final_decision": final_decision,
        "confidence": confidence,
        "bias_score": bias_score,
        "adjusted_probabilities": result.get("adjusted_probabilities", []),
        "explanation": explanation,
    }
