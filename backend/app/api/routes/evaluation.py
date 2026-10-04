from fastapi import APIRouter, Query

from backend.app.services.evaluation_service import evaluate_retrieval


router = APIRouter()


# -----------------------------
# Retrieval Evaluation
# -----------------------------

@router.post("/evaluation/run")
def run_evaluation(
    top_k: int = Query(default=3, ge=1, le=20),
):
    """
    Run the retrieval benchmark across all configured strategies.
    """

    return evaluate_retrieval(top_k=top_k)