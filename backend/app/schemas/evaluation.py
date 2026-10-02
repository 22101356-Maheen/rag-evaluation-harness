from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    question: str
    retriever: str
    top_k: int