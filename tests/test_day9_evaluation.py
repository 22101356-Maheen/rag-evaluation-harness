import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from openai import APITimeoutError, OpenAI
from pydantic import SecretStr
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.auth import get_current_user_id
from backend.app.core.config import settings
from backend.app.db.postgres import Base, get_db
from backend.app.llm.openai_provider import LLMError, OpenAIProvider, encoded_size
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.evaluation_case import EvaluationCase
from backend.app.models.evaluation_dataset import EvaluationDataset
from backend.app.models.experiment_run import ExperimentRun
from backend.app.models.project import Project
from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.schemas.evaluation import (
    AnswerJudgeResult,
    CaseValidation,
    EvaluationRunRequest,
    GeneratedAnswer,
    SourceQuote,
    SyntheticCandidates,
    SyntheticQuestionCandidate,
)
from backend.app.schemas.experiment import ExperimentConfig
from backend.app.services import experiment_service as experiments
from backend.app.services import synthetic_dataset_service as datasets
from backend.app.services.answer_evaluation_service import (
    calculate_metrics,
    evaluate_answer,
)
from backend.app.services.evaluation_service import EvaluationDatasetError
from backend.app.services.experiment_run_service import save_experiment_run


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.reject_validation = False

    def close(self):
        self.closed = True

    def structured(self, *, model, instructions, payload, schema):
        self.calls.append((schema, payload))

        if schema is SyntheticCandidates:
            source = payload["source"]

            return SyntheticCandidates(
                cases=[
                    SyntheticQuestionCandidate(
                        question="What fruit is described?",
                        reference_answer=(
                            "Oranges are citrus fruit rich in vitamin C."
                        ),
                        evidence=[
                            SourceQuote(
                                chunk_id=source["chunk_id"],
                                quote=source["text"],
                            )
                        ],
                    )
                ]
            )

        if schema is CaseValidation:
            return CaseValidation(
                answerable=True,
                standalone=True,
                reference_fully_supported=not self.reject_validation,
            )

        if schema is GeneratedAnswer:
            return GeneratedAnswer(
                answer="Oranges are citrus fruit.",
                insufficient_context=False,
                cited_chunk_ids=[
                    payload["retrieved_context"][0]["chunk_id"]
                ],
            )

        if schema is AnswerJudgeResult:
            return judge_result(
                payload["retrieved_context"][0]["chunk_id"]
            )

        raise AssertionError(schema)


def judge_result(chunk_id="11:0"):
    return AnswerJudgeResult(
        claims=[
            {
                "claim": "Oranges are citrus fruit.",
                "context_supported": True,
                "supporting_chunk_ids": [chunk_id],
                "reference_verdict": "matches",
            }
        ],
        reference_claims=[
            {
                "claim": "Oranges are citrus fruit.",
                "covered": True,
            }
        ],
        relevance_rating=4,
        valid_abstention=False,
    )


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                Project(
                    id=7,
                    owner_id="owner",
                    name="Owned",
                ),
                Project(
                    id=8,
                    owner_id="other",
                    name="Other",
                ),
            ]
        )
        session.commit()

        session.add_all(
            [
                Document(
                    id=11,
                    project_id=7,
                    filename="fruit.txt",
                    status="ready",
                ),
                Document(
                    id=12,
                    project_id=7,
                    filename="failed.txt",
                    status="failed",
                ),
            ]
        )
        session.commit()

        yield session

    engine.dispose()


@pytest.fixture
def chunks():
    return [
        {
            "chunk_id": "11:0",
            "document_id": 11,
            "chunk_index": 0,
            "text": "Oranges are citrus fruit rich in vitamin C.",
        }
    ]


def test_dataset_reuse_and_fingerprint_invalidation(db, chunks):
    provider = FakeProvider()
    request = EvaluationRunRequest(case_count=1)

    dataset, cases, reused = datasets.get_or_create_dataset(
        db,
        7,
        chunks,
        request,
        provider,
    )

    assert not reused

    assert cases[0].source_evidence[0]["chunk_id"] == "11:0"

    assert (
        cases[0].source_evidence[0]["content_hash"]
        == datasets.digest(chunks[0]["text"])
    )

    call_count = len(provider.calls)

    cached, _, reused = datasets.get_or_create_dataset(
        db,
        7,
        chunks,
        request,
        provider,
    )

    assert reused
    assert cached.id == dataset.id
    assert len(provider.calls) == call_count

    changed = [
        {
            **chunks[0],
            "text": (
                chunks[0]["text"]
                + " Fresh oranges are orange."
            ),
        }
    ]

    new_dataset, _, reused = datasets.get_or_create_dataset(
        db,
        7,
        changed,
        request,
        provider,
    )

    assert not reused
    assert new_dataset.id != dataset.id

    assert (
        db.scalar(
            select(func.count()).select_from(EvaluationCase)
        )
        == 2
    )


def test_fingerprint_order_and_project_cache_scope(db, chunks):
    assert datasets.corpus_fingerprint(
        chunks * 2
    ) == datasets.corpus_fingerprint(
        list(reversed(chunks * 2))
    )

    first, _, _ = datasets.get_or_create_dataset(
        db,
        7,
        chunks,
        EvaluationRunRequest(case_count=1),
        FakeProvider(),
    )

    second, _, reused = datasets.get_or_create_dataset(
        db,
        8,
        chunks,
        EvaluationRunRequest(case_count=1),
        FakeProvider(),
    )

    assert second.cache_key != first.cache_key
    assert not reused


@pytest.mark.parametrize(
    "bad_id,quote",
    [
        ("999:0", "Oranges"),
        ("11:0", "A warranty lasts forever"),
    ],
)
def test_fake_evidence_rejected(chunks, bad_id, quote):
    candidate = SyntheticQuestionCandidate(
        question="What fruit?",
        reference_answer="Oranges.",
        evidence=[
            SourceQuote(
                chunk_id=bad_id,
                quote=quote,
            )
        ],
    )

    with pytest.raises(EvaluationDatasetError):
        datasets.resolve_evidence(
            candidate,
            chunks,
        )


def test_unsupported_reference_never_persisted(db, chunks):
    provider = FakeProvider()
    provider.reject_validation = True

    with pytest.raises(EvaluationDatasetError):
        datasets.get_or_create_dataset(
            db,
            7,
            chunks,
            EvaluationRunRequest(case_count=1),
            provider,
        )

    assert (
        db.scalar(
            select(func.count()).select_from(EvaluationDataset)
        )
        == 0
    )


def test_manual_mode_resolves_evidence_and_validates(
    db,
    chunks,
):
    request = EvaluationRunRequest(
        mode="manual",
        manual_cases=[
            {
                "question": "What fruit?",
                "reference_answer": "Oranges.",
                "expected_evidence": [
                    chunks[0]["text"]
                ],
            }
        ],
    )

    provider = FakeProvider()

    dataset, cases, reused = datasets.get_or_create_dataset(
        db,
        7,
        chunks,
        request,
        provider,
    )

    assert dataset.mode == "manual"
    assert not reused

    assert (
        cases[0].source_evidence[0]["document_id"]
        == 11
    )

    assert [
        call[0] for call in provider.calls
    ] == [CaseValidation]


def test_windows_are_bounded_and_spread_across_documents():
    chunks = [
        {
            "document_id": doc,
            "chunk_index": i,
            "chunk_id": f"{doc}:{i}",
            "text": (
                f"Document {doc} section {i} "
                + "some factual source text " * 300
            ),
        }
        for doc in (1, 2, 3)
        for i in range(10)
    ]

    windows = datasets.evidence_windows(
        chunks,
        4,
    )

    assert [
        window["chunk_id"]
        for window in windows[:3]
    ] == [
        "1:0",
        "2:0",
        "3:0",
    ]

    assert all(
        len(
            window["text"].encode("utf-8")
        )
        <= 1600
        for window in windows
    )

    assert len(windows) == 4


def test_generation_has_no_hidden_ground_truth_and_judge_gets_exact_context(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "llm_context_token_budget",
        160,
    )

    provider = FakeProvider()

    case = SimpleNamespace(
        id=1,
        question="What fruit?",
        reference_answer="SECRET_REFERENCE",
        source_evidence=[
            {
                "quote": "SECRET_EVIDENCE",
                "chunk_id": "secret:0",
            }
        ],
    )

    results = [
        {
            "chunk_id": "11:0",
            "text": (
                "Oranges are citrus fruit. "
                * 40
            ),
        },
        {
            "chunk_id": "12:0",
            "text": "NOT_IN_TOP_K",
        },
    ]

    output = evaluate_answer(
        case,
        results,
        1,
        provider,
    )

    generation = provider.calls[0][1]

    serialized = json.dumps(generation)

    assert "SECRET" not in serialized
    assert "NOT_IN_TOP_K" not in serialized

    assert set(generation) == {
        "question",
        "retrieved_context",
    }

    assert (
        encoded_size(
            generation["retrieved_context"]
        )
        <= 160
    )

    assert (
        provider.calls[1][1]["retrieved_context"]
        == generation["retrieved_context"]
    )

    assert (
        provider.calls[1][1][
            "hidden_reference_answer"
        ]
        == "SECRET_REFERENCE"
    )

    assert output["context_truncated"]


def test_metric_math_and_abstention():
    judge = judge_result()

    judge.claims.append(
        judge.claims[0].model_copy(
            update={
                "context_supported": False,
                "supporting_chunk_ids": [],
                "reference_verdict": "contradicts",
            }
        )
    )

    answer = GeneratedAnswer(
        answer="An answer.",
        cited_chunk_ids=[],
        insufficient_context=False,
    )

    metrics = calculate_metrics(
        judge,
        answer,
        [{"chunk_id": "11:0"}],
    )

    assert metrics == {
        "faithfulness": 0.5,
        "hallucination": 0.5,
        "correctness": 0.6667,
        "relevance": 1.0,
    }

    judge.claims = []

    with pytest.raises(LLMError):
        calculate_metrics(
            judge,
            answer,
            [],
        )

    answer.insufficient_context = True
    judge.valid_abstention = True
    judge.relevance_rating = 0

    assert (
        calculate_metrics(
            judge,
            answer,
            [],
        )["correctness"]
        == 0
    )


def test_boundary_spanning_labels_and_repeated_text():
    text = " ".join(
        ["repeat"] * 250
    )

    stored = [
        {
            "document_id": 11,
            "chunk_id": f"11:{i}",
            "chunk_index": i,
            "text": part,
        }
        for i, part in enumerate(
            chunk_text(text)
        )
    ]

    assert (
        experiments._snapshot_documents(
            stored
        )[0]["text"]
        == text
    )

    words = [
        f"word{i}"
        for i in range(90)
    ]

    docs = [
        {
            "document_id": 11,
            "text": " ".join(words),
        }
    ]

    case = SimpleNamespace(
        question="Boundary?",
        source_evidence=[
            {
                "document_id": 11,
                "quote": " ".join(
                    words[38:42]
                ),
            }
        ],
    )

    queries = experiments._case_queries(
        [case],
        docs,
        ExperimentConfig(
            name="test",
            chunk_size=40,
            chunk_overlap=0,
        ),
    )

    assert (
        queries[0]["relevant_ids"]
        == {
            "11:0",
            "11:1",
        }
    )


def test_evidence_without_trailing_punctuation_maps_to_chunks(
    chunks,
):
    candidate = SyntheticQuestionCandidate(
        question="Which fruit?",
        reference_answer="Oranges.",
        evidence=[
            SourceQuote(
                chunk_id="11:0",
                quote="rich in vitamin C",
            )
        ],
    )

    evidence = datasets.resolve_evidence(
        candidate,
        chunks,
    )

    case = SimpleNamespace(
        question=candidate.question,
        source_evidence=evidence,
    )

    queries = experiments._case_queries(
        [case],
        [
            {
                "document_id": 11,
                "text": chunks[0]["text"],
            }
        ],
        ExperimentConfig(
            name="punctuation"
        ),
    )

    assert (
        queries[0]["relevant_ids"]
        == {"11:0"}
    )

    assert (
        datasets.quote_spans(
            "range",
            "Oranges are fruit",
        )
        == []
    )


def test_dataset_transaction_rolls_back_on_case_insert_failure(
    db,
    chunks,
    monkeypatch,
):
    def fail(_):
        raise RuntimeError(
            "simulated insert failure"
        )

    monkeypatch.setattr(
        db,
        "add_all",
        fail,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated",
    ):
        datasets.get_or_create_dataset(
            db,
            7,
            chunks,
            EvaluationRunRequest(
                case_count=1
            ),
            FakeProvider(),
        )

    assert (
        db.scalar(
            select(func.count()).select_from(
                EvaluationDataset
            )
        )
        == 0
    )


def test_new_endpoint_error_paths_do_not_persist_winner(
    db,
    chunks,
    monkeypatch,
):
    from fastapi import HTTPException

    from backend.app.api.routes.project_evaluations import (
        evaluate_project,
    )

    monkeypatch.setattr(
        experiments,
        "get_project_chunks",
        lambda project_id: [],
    )

    with pytest.raises(
        HTTPException
    ) as empty:
        evaluate_project(
            7,
            db=db,
            owner_id="owner",
        )

    assert empty.value.status_code == 400

    monkeypatch.setattr(
        experiments,
        "get_project_chunks",
        lambda project_id: chunks,
    )

    monkeypatch.setattr(
        settings,
        "groq_api_key",
        None,
    )

    with pytest.raises(
        HTTPException
    ) as missing_key:
        evaluate_project(
            7,
            db=db,
            owner_id="owner",
        )

    assert (
        missing_key.value.status_code
        == 503
    )

    assert (
        db.scalar(
            select(func.count()).select_from(
                ExperimentRun
            )
        )
        == 0
    )


def test_endpoint_http_persistence_reuse_and_ownership(
    db,
    chunks,
    monkeypatch,
):
    providers = []

    def create_provider():
        provider = FakeProvider()
        providers.append(provider)
        return provider

    monkeypatch.setattr(
        experiments,
        "OpenAIProvider",
        create_provider,
    )

    def selected_chunks(project_id):
        assert project_id == 7

        return chunks + [
            {
                "document_id": 12,
                "chunk_index": 0,
                "chunk_id": "12:0",
                "text": "FAILED_SOURCE",
            }
        ]

    monkeypatch.setattr(
        experiments,
        "get_project_chunks",
        selected_chunks,
    )

    monkeypatch.setattr(
        experiments,
        "embed_texts",
        lambda texts: [
            [1.0, 0.0]
            for _ in texts
        ],
    )

    from backend.app.rag.retrieval import retriever

    monkeypatch.setattr(
        retriever,
        "embed_query",
        lambda query: [1.0, 0.0],
    )

    app.dependency_overrides[
        get_db
    ] = lambda: db

    app.dependency_overrides[
        get_current_user_id
    ] = lambda: "owner"

    try:
        with TestClient(app) as client:
            assert (
                client.get(
                    "/health"
                ).status_code
                == 200
            )

            assert (
                client.post(
                    "/projects/8/evaluations/run"
                ).status_code
                == 404
            )

            assert (
                client.post(
                    "/projects/999/evaluations/run"
                ).status_code
                == 404
            )

            assert not providers

            first = client.post(
                "/projects/7/evaluations/run"
            )

            assert (
                first.status_code
                == 200
            ), first.text

            assert set(first.json()) == {
                "summary",
                "details",
            }

            assert set(first.json()["summary"]) == {
                "recommended_strategy",
                "recommended_experiment",
                "recommendation_score",
                "configuration",
                "key_metrics",
                "guardrail_status",
                "why_recommended",
                "strengths",
                "weaknesses",
                "next_step",
            }

            assert {
                "project_id",
                "evaluation_dataset_id",
                "dataset_reused",
                "dataset_mode",
                "case_count",
                "experiment_run_id",
                "best_experiment",
                "ranking",
                "report",
            } == set(first.json()["details"])

            assert (
                len(
                    first.json()["details"]["ranking"]
                )
                == 3
            )

            second = client.post(
                "/projects/7/evaluations/run",
                json={},
            )

            assert (
                second.status_code
                == 200
            ), second.text

            assert (
                second.json()["details"][
                    "dataset_reused"
                ]
            )

            assert (
                "reference_answer"
                not in second.text
            )

            assert (
                "FAILED_SOURCE"
                not in json.dumps(
                    providers[0].calls,
                    default=str,
                )
            )

            assert all(
                provider.closed
                for provider in providers
            )

            assert all(
                schema
                is not SyntheticCandidates
                for schema, _ in providers[1].calls
            )

            assert (
                client.post(
                    "/projects/7/evaluations/run",
                    json={
                        "mode": "manual"
                    },
                ).status_code
                == 422
            )

    finally:
        app.dependency_overrides.clear()

    run = db.get(
        ExperimentRun,
        first.json()["details"][
            "experiment_run_id"
        ],
    )

    assert (
        run.evaluation_dataset_id
        == first.json()["details"][
            "evaluation_dataset_id"
        ]
    )

    assert run.faithfulness == 1
    assert run.mrr == 1

    assert (
        db.scalar(
            select(func.count()).select_from(
                ExperimentRun
            )
        )
        == 2
    )


def test_day8_persistence_leaves_day9_fields_null(
    db,
):
    run = save_experiment_run(
        db,
        7,
        {
            "configuration": {
                "strategy": "bm25",
                "chunk_size": 120,
                "chunk_overlap": 20,
                "top_k": 3,
            },
            "metrics": {
                "hit_at_k": 1,
                "precision_at_k": 1,
                "recall_at_k": 1,
                "mrr": 1,
            },
        },
    )

    assert (
        run.evaluation_dataset_id
        is None
    )

    assert run.faithfulness is None


def test_provider_uses_real_sdk_structured_output(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "groq_api_key",
        SecretStr("test-only"),
    )

    provider = OpenAIProvider()
    provider.client.close()

    def transport(request):
        body = json.loads(
            request.content
        )

        assert (
            body["text"]["format"]["type"]
            == "json_schema"
        )

        assert (
            body["text"]["format"]["strict"]
            is True
        )

        # Groq call should not send store=False.
        assert "store" not in body

        assert "tools" not in body

        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": "test",
                "parallel_tool_calls": False,
                "tool_choice": "none",
                "tools": [],
                "output": [
                    {
                        "type": "message",
                        "id": "msg_test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "annotations": [],
                                "text": json.dumps(
                                    {
                                        "answer": (
                                            "Test answer"
                                        ),
                                        "cited_chunk_ids": [],
                                        "insufficient_context": True,
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    provider.client = OpenAI(
        api_key="test-only",
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                transport
            )
        ),
    )

    try:
        result = provider.structured(
            model="test",
            instructions="test",
            payload={},
            schema=GeneratedAnswer,
        )

        assert result.insufficient_context

    finally:
        provider.close()


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(
            status="incomplete",
            output_parsed=None,
        ),
        SimpleNamespace(
            status="completed",
            output_parsed=None,
        ),
    ],
)
def test_refusal_and_incomplete_are_errors(
    response,
):
    provider = object.__new__(
        OpenAIProvider
    )

    provider.client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=lambda **kwargs: response
        )
    )

    with pytest.raises(LLMError):
        provider.structured(
            model="test",
            instructions="test",
            payload={},
            schema=GeneratedAnswer,
        )


def test_timeout_and_malformed_are_errors():
    provider = object.__new__(
        OpenAIProvider
    )

    def timeout(**kwargs):
        raise APITimeoutError(
            request=httpx.Request(
                "POST",
                "https://example.test",
            )
        )

    provider.client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=timeout
        )
    )

    with pytest.raises(
        LLMError
    ) as error:
        provider.structured(
            model="test",
            instructions="test",
            payload={},
            schema=GeneratedAnswer,
        )

    assert error.value.status_code == 504

    def malformed(**kwargs):
        return GeneratedAnswer.model_validate(
            {
                "unexpected": True
            }
        )

    provider.client.responses.parse = (
        malformed
    )

    with pytest.raises(LLMError):
        provider.structured(
            model="test",
            instructions="test",
            payload={},
            schema=GeneratedAnswer,
        )


def test_missing_key_is_optional_at_startup_but_required_for_run(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "groq_api_key",
        None,
    )

    with pytest.raises(
        LLMError
    ) as error:
        OpenAIProvider()

    assert error.value.status_code == 503


def test_migration_upgrade_downgrade_preserves_existing_run():
    path = Path(
        "alembic/versions/"
        "a19d90000001_add_day9_evaluation.py"
    )

    spec = importlib.util.spec_from_file_location(
        "day9_migration",
        path,
    )

    migration = (
        importlib.util.module_from_spec(
            spec
        )
    )

    spec.loader.exec_module(
        migration
    )

    engine = create_engine(
        "sqlite://"
    )

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE projects "
            "(id INTEGER PRIMARY KEY)"
        )

        connection.exec_driver_sql(
            "CREATE TABLE experiment_runs "
            "(id INTEGER PRIMARY KEY, "
            "mrr FLOAT)"
        )

        connection.exec_driver_sql(
            "INSERT INTO experiment_runs "
            "VALUES (1, 0.75)"
        )

        with Operations.context(
            MigrationContext.configure(
                connection
            )
        ):
            migration.upgrade()

            assert (
                connection.exec_driver_sql(
                    "SELECT mrr, faithfulness "
                    "FROM experiment_runs"
                ).one()
                == (0.75, None)
            )

            migration.downgrade()

            assert (
                connection.exec_driver_sql(
                    "SELECT mrr "
                    "FROM experiment_runs"
                ).scalar()
                == 0.75
            )

    engine.dispose()
