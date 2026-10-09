from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_user_id
from backend.app.db.postgres import get_db
from backend.app.llm.openai_provider import LLMError
from backend.app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from backend.app.services.evaluation_service import EvaluationDatasetError
from backend.app.services.experiment_service import (
    ProjectCorpusEmptyError,
    run_project_evaluation,
)
from backend.app.services.project_service import get_owned_project_by_id

router = APIRouter()


@router.post("/projects/{project_id}/evaluations/run", response_model=EvaluationRunResponse)
def evaluate_project(
    project_id: int,
    request: EvaluationRunRequest | None = None,
    db: Session = Depends(get_db),  # noqa: B008
    owner_id: str = Depends(get_current_user_id),
):
    project = get_owned_project_by_id(db=db, project_id=project_id, owner_id=owner_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return run_project_evaluation(db, project_id, request or EvaluationRunRequest())
    except ProjectCorpusEmptyError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except EvaluationDatasetError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LLMError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
