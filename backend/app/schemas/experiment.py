from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# -----------------------------
# Experiment Configuration
# -----------------------------

class ExperimentConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

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

    @model_validator(mode="after")
    def validate_chunk_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        return self


# -----------------------------
# Batch Experiment Request
# -----------------------------

class ExperimentBatchRequest(BaseModel):
    experiments: list[ExperimentConfig] = Field(min_length=1)


# -----------------------------
# Project Evaluation Dataset
# -----------------------------

class ProjectEvaluationQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1)
    expected_evidence: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expected_evidence(self):
        cleaned_evidence = [
            evidence.strip()
            for evidence in self.expected_evidence
            if evidence.strip()
        ]

        if not cleaned_evidence:
            raise ValueError(
                "expected_evidence must contain non-empty text"
            )

        self.expected_evidence = cleaned_evidence
        return self


class ProjectExperimentBatchRequest(BaseModel):
    experiments: list[ExperimentConfig] = Field(min_length=1)
    evaluation_queries: list[ProjectEvaluationQuery] = Field(
        min_length=1
    )
