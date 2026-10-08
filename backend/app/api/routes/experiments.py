from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_user_id
from backend.app.db.postgres import get_db
from backend.app.schemas.experiment import (
    ExperimentBatchRequest,
    ExperimentConfig,
    ProjectExperimentBatchRequest,
)
from backend.app.services.evaluation_service import EvaluationDatasetError
from backend.app.services.experiment_run_service import save_experiment_run
from backend.app.services.experiment_service import (
    ProjectCorpusEmptyError,
    run_experiment,
    run_experiment_batch,
    run_project_experiment_batch,
)
from backend.app.services.project_service import get_owned_project_by_id


router = APIRouter()


# -----------------------------
# Run One Experiment
# -----------------------------

@router.post("/experiments/run")
def run_single_experiment(
    experiment: ExperimentConfig,
):
    """
    Run one controlled RAG experiment.
    """

    return run_experiment(
        config=experiment,
    )


# -----------------------------
# Compare Experiments
# -----------------------------

@router.post("/experiments/compare")
def compare_multiple_experiments(
    request: ExperimentBatchRequest,
):
    """
    Compare multiple controlled RAG configurations.
    """

    return run_experiment_batch(
        configs=request.experiments,
    )


# -----------------------------
# Project Experiment Comparison
# -----------------------------

@router.post(
    "/projects/{project_id}/experiments/compare"
)
def compare_project_experiments(
    project_id: int,
    request: ProjectExperimentBatchRequest,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    Run experiments only for a project owned by the current user.
    """

    # make sure this project belongs to the current user.
    project = get_owned_project_by_id(
        db=db,
        project_id=project_id,
        owner_id=owner_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    try:
        comparison = run_project_experiment_batch(
            project_id=project_id,
            configs=request.experiments,
            evaluation_queries=request.evaluation_queries,
        )
    except ProjectCorpusEmptyError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except EvaluationDatasetError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    best_experiment = comparison["best_experiment"]

    experiment_run = save_experiment_run(
        db=db,
        project_id=project_id,
        best_experiment=best_experiment,
    )

    return {
        "project_id": project_id,
        "project_name": project.name,
        "experiment_run_id": experiment_run.id,
        "experiment_count": comparison["experiment_count"],
        "evaluation_query_count": comparison[
            "evaluation_query_count"
        ],
        "best_experiment": best_experiment,
        "ranking": comparison["ranking"],
    }
