from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.api.routes import experiments as experiment_routes
from backend.app.db import qdrant
from backend.app.rag.evaluation.metrics import get_retrieved_chunk_ids
from backend.app.rag.retrieval.bm25 import retrieve_bm25
from backend.app.rag.retrieval.hybrid import reciprocal_rank_fusion
from backend.app.schemas.experiment import (
    ExperimentBatchRequest,
    ExperimentConfig,
    ProjectEvaluationQuery,
    ProjectExperimentBatchRequest,
)
from backend.app.services import experiment_service


def test_experiment_requests_reject_empty_or_invalid_configs():
    with pytest.raises(ValidationError):
        ExperimentBatchRequest(experiments=[])

    with pytest.raises(ValidationError):
        ExperimentConfig(
            name="invalid",
            chunk_size=40,
            chunk_overlap=40,
        )


def test_hybrid_keeps_same_chunk_index_from_different_documents():
    semantic_results = [
        {
            "chunk_id": "10:0",
            "document_id": 10,
            "chunk_index": 0,
            "text": "alpha",
            "score": 0.9,
        },
        {
            "chunk_id": "20:0",
            "document_id": 20,
            "chunk_index": 0,
            "text": "beta",
            "score": 0.8,
        },
    ]
    bm25_results = retrieve_bm25(
        query="alpha beta",
        chunks=["alpha", "beta"],
        top_k=2,
        chunk_ids=["10:0", "20:0"],
        chunk_metadata=[
            {"document_id": 10, "chunk_index": 0},
            {"document_id": 20, "chunk_index": 0},
        ],
    )

    results = reciprocal_rank_fusion(
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        top_k=2,
    )

    assert set(get_retrieved_chunk_ids(results)) == {"10:0", "20:0"}


def test_project_chunk_loading_filters_and_paginates(monkeypatch):
    calls = []

    class FakeClient:
        def scroll(self, **kwargs):
            calls.append(kwargs)

            if len(calls) == 1:
                return (
                    [
                        SimpleNamespace(
                            payload={
                                "project_id": 7,
                                "document_id": 12,
                                "chunk_index": 0,
                                "text": "second document",
                            }
                        )
                    ],
                    "next-page",
                )

            return (
                [
                    SimpleNamespace(
                        payload={
                            "project_id": 7,
                            "document_id": 11,
                            "chunk_index": 0,
                            "text": "first document",
                        }
                    )
                ],
                None,
            )

    monkeypatch.setattr(qdrant, "client", FakeClient())
    monkeypatch.setattr(qdrant, "ensure_project_collection", lambda: None)

    chunks = qdrant.get_project_chunks(project_id=7)

    project_filter = calls[0]["scroll_filter"]
    assert project_filter.must[0].match.value == 7
    assert calls[1]["offset"] == "next-page"
    assert [chunk["chunk_id"] for chunk in chunks] == ["11:0", "12:0"]


def test_project_batch_uses_only_requested_project_without_resetting(
    monkeypatch,
):
    requested_project_ids = []

    def fake_get_project_chunks(project_id):
        requested_project_ids.append(project_id)
        return [
            {
                "chunk_id": "11:0",
                "document_id": 11,
                "chunk_index": 0,
                "text": "Oranges are citrus fruit rich in vitamin C.",
            },
            {
                "chunk_id": "12:0",
                "document_id": 12,
                "chunk_index": 0,
                "text": "Saturn is a planet with prominent rings.",
            },
        ]

    monkeypatch.setattr(
        experiment_service,
        "get_project_chunks",
        fake_get_project_chunks,
    )
    monkeypatch.setattr(
        experiment_service,
        "embed_texts",
        lambda chunks: [[0.0] for _ in chunks],
    )
    monkeypatch.setattr(
        experiment_service,
        "store_chunks",
        lambda **kwargs: pytest.fail(
            "Project experiments must not reset controlled or project vectors"
        ),
    )

    result = experiment_service.run_project_experiment_batch(
        project_id=7,
        configs=[
            ExperimentConfig(
                name="keyword",
                chunk_size=40,
                chunk_overlap=5,
                top_k=1,
                strategy="bm25",
            )
        ],
        evaluation_queries=[
            ProjectEvaluationQuery(
                query="Which fruit is rich in vitamin C?",
                expected_evidence=[
                    "Oranges are citrus fruit rich in vitamin C."
                ],
            )
        ],
    )

    assert requested_project_ids == [7]
    assert result["experiment_count"] == 1
    assert result["evaluation_query_count"] == 1
    assert result["best_experiment"]["metrics"]["mrr"] == 1.0
    assert result["best_experiment"]["document_count"] == 2


def test_controlled_batch_remains_separate(monkeypatch):
    controlled_calls = []

    def fake_controlled_experiment(config):
        controlled_calls.append(config.name)
        return {
            "configuration": {
                "chunk_size": config.chunk_size,
                "chunk_overlap": config.chunk_overlap,
                "top_k": config.top_k,
                "strategy": config.strategy,
            },
            "chunk_count": 4,
            "evaluation": {
                "strategies": {
                    "semantic": {
                        "average_hit_at_k": 1.0,
                        "average_precision_at_k": 0.5,
                        "average_recall_at_k": 1.0,
                        "mean_reciprocal_rank": 1.0,
                    }
                }
            },
        }

    monkeypatch.setattr(
        experiment_service,
        "run_experiment",
        fake_controlled_experiment,
    )

    result = experiment_service.run_experiment_batch(
        configs=[
            ExperimentConfig(
                name="controlled",
                strategy="semantic",
            )
        ]
    )

    assert controlled_calls == ["controlled"]
    assert result["best_experiment"]["experiment_name"] == "controlled"


def test_project_route_blocks_unowned_project(monkeypatch):
    monkeypatch.setattr(
        experiment_routes,
        "get_owned_project_by_id",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        experiment_routes,
        "run_project_experiment_batch",
        lambda **kwargs: pytest.fail("Unowned projects must not be evaluated"),
    )
    request = ProjectExperimentBatchRequest(
        experiments=[ExperimentConfig(name="test")],
        evaluation_queries=[
            ProjectEvaluationQuery(
                query="question",
                expected_evidence=["evidence"],
            )
        ],
    )

    with pytest.raises(HTTPException) as error:
        experiment_routes.compare_project_experiments(
            project_id=99,
            request=request,
            db=object(),
            owner_id="another-user",
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found"


def test_project_route_persists_owned_project_winner(monkeypatch):
    comparison = {
        "experiment_count": 1,
        "evaluation_query_count": 1,
        "best_experiment": {
            "experiment_name": "keyword",
            "configuration": {
                "strategy": "bm25",
                "chunk_size": 40,
                "chunk_overlap": 5,
                "top_k": 1,
            },
            "metrics": {
                "hit_at_k": 1.0,
                "precision_at_k": 1.0,
                "recall_at_k": 1.0,
                "mrr": 1.0,
            },
            "score": 1.0,
        },
        "ranking": [],
    }
    saved = []

    monkeypatch.setattr(
        experiment_routes,
        "get_owned_project_by_id",
        lambda **kwargs: SimpleNamespace(name="Owned"),
    )
    monkeypatch.setattr(
        experiment_routes,
        "run_project_experiment_batch",
        lambda **kwargs: comparison,
    )

    def fake_save(**kwargs):
        saved.append(kwargs)
        return SimpleNamespace(id=123)

    monkeypatch.setattr(
        experiment_routes,
        "save_experiment_run",
        fake_save,
    )
    request = ProjectExperimentBatchRequest(
        experiments=[ExperimentConfig(name="test")],
        evaluation_queries=[
            ProjectEvaluationQuery(
                query="question",
                expected_evidence=["evidence"],
            )
        ],
    )

    response = experiment_routes.compare_project_experiments(
        project_id=7,
        request=request,
        db=object(),
        owner_id="owner",
    )

    assert response["experiment_run_id"] == 123
    assert saved[0]["project_id"] == 7
    assert saved[0]["best_experiment"] is comparison["best_experiment"]
