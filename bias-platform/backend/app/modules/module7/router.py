from fastapi import APIRouter, HTTPException

from app.modules.module7.schema import ContextSchema, ProbabilitiesRequest
from app.modules.module7.service import calculate_bias_score, context_service

router = APIRouter(prefix="/context", tags=["context"])


def _build_context_explanation(context: dict, context_weights: dict) -> str:
    if not context:
        return "No context applied"
    if not context_weights:
        return "Context provided, but no matching factors affected confidence"
    return "Context influenced prediction confidence using configured context weights."


@router.post("")
def set_context(context: dict):
    try:
        validated = ContextSchema.validate(context)
        context_service.set_context(validated)
        return {"message": "Context set successfully", "context": validated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/apply-context")
def apply_context(payload: dict):
    try:
        if "probabilities" not in payload:
            raise ValueError("Missing 'probabilities' field")
        probabilities = payload["probabilities"]
        if not isinstance(probabilities, list) or len(probabilities) == 0:
            raise ValueError("probabilities must be a non-empty list")
        return context_service.apply_context_to_predictions(probabilities)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/explain")
def explain_context(payload: ProbabilitiesRequest):
    probabilities = payload.probabilities
    context = context_service.get_context()
    result = context_service.apply_context_to_predictions(probabilities)
    return {
        "input_probabilities": probabilities,
        "adjusted_probabilities": result["adjusted_probabilities"],
        "applied_context": context,
        "context_weights": result["context_weights"],
        "explanation": _build_context_explanation(context, result["context_weights"]),
    }


@router.post("/bias-score")
def context_bias_score(payload: ProbabilitiesRequest):
    return calculate_bias_score(payload.probabilities)
