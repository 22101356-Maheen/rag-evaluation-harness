from backend.app.schemas.evaluation import EvaluationRequest


def preview_evaluation(request: EvaluationRequest):
    return {
        "message": "Evaluation request received",
        "question": request.question,
        "retriever": request.retriever,
        "top_k": request.top_k
    }