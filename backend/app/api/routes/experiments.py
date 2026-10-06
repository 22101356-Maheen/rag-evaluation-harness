from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.postgres import get_db
from backend.app.schemas.experiment import (
    ExperimentBatchRequest,
    ExperimentConfig,
)
from backend.app.services.experiment_run_service import save_experiment_run
from backend.app.services.experiment_service import (
    run_experiment,
    run_experiment_batch,
)
from backend.app.services.project_service import get_project_by_id


router = APIRouter()


# -----------------------------
# Single Experiment
# -----------------------------

@router.post("/experiments/run")
def run_rag_experiment(
    config: ExperimentConfig,
):
    """
    Run one RAG retrieval configuration.
    """

    return run_experiment(config)


# -----------------------------
# Batch Experiment Comparison
# -----------------------------

@router.post("/experiments/compare")
def compare_rag_experiments(
    request: ExperimentBatchRequest,
):
    """
    Run multiple RAG configurations and rank them.
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
    request: ExperimentBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Compare configurations for a project and save the winner.
    """

    # this checks that the requested project actually exists.
    project = get_project_by_id(
        db=db,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # this runs the RAG comparison and finds the best configuration.
    comparison = run_experiment_batch(
        configs=request.experiments,
    )

    best_experiment = comparison["best_experiment"]

    # this connects the winning result to the project in PostgreSQL.
    saved_run = save_experiment_run(
        db=db,
        project_id=project_id,
        best_experiment=best_experiment,
    )

    return {
        "project_id": project_id,
        "project_name": project.name,
        "experiment_run_id": saved_run.id,
        "best_experiment": best_experiment,
        "ranking": comparison["ranking"],
    }