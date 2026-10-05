from fastapi import APIRouter

from backend.app.schemas.experiment import (
    ExperimentBatchRequest,
    ExperimentConfig,
)
from backend.app.services.experiment_service import (
    run_experiment,
    run_experiment_batch,
)


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