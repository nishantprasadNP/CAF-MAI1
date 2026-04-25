from fastapi import APIRouter

from app.modules.module7.schema import ProbabilitiesRequest
from app.modules.module8.decision import explain_final
from app.modules.module7.decision import build_final_decision

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/final")
def final_decision(payload: ProbabilitiesRequest):
    return build_final_decision(payload.probabilities)


@router.post("/explain-final")
def explain_final_decision(payload: ProbabilitiesRequest):
    return explain_final(payload.probabilities)
