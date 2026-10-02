from fastapi import APIRouter

from backend.app.schemas.evaluation import EvaluationRequest
from backend.app.services.evaluation_service import preview_evaluation

router = APIRouter()


@router.post("/evaluate/preview")
def evaluate_preview(request: EvaluationRequest):
    return preview_evaluation(request)