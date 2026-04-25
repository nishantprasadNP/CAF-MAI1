from fastapi import APIRouter
from app.modules.module8.decision import run_module8

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/final")
def final_decision(payload: dict):
    return run_module8(
        probabilities=payload.get("probabilities"),
        original_probabilities=payload.get("original_probabilities"),
        fairness_output=payload.get("fairness_output"),
        top_features=payload.get("top_features"),
    )