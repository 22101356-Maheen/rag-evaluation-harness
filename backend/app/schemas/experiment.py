from typing import Literal

from pydantic import BaseModel, Field


# -----------------------------
# Experiment Configuration
# -----------------------------

class ExperimentConfig(BaseModel):
    name: str = Field(min_length=1)

    chunk_size: int = Field(
        default=120,
        ge=40,
        le=1000,
    )

    chunk_overlap: int = Field(
        default=20,
        ge=0,
        le=300,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
    )

    strategy: Literal[
        "semantic",
        "bm25",
        "hybrid",
    ] = "hybrid"


# -----------------------------
# Batch Experiment Request
# -----------------------------

class ExperimentBatchRequest(BaseModel):
    experiments: list[ExperimentConfig]