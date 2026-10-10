import importlib.util
import json
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.app.db.postgres import Base
from backend.app.models.evaluation_dataset import EvaluationDataset  # noqa: F401
from backend.app.models.experiment_run import ExperimentRun
from backend.app.models.project import Project
from backend.app.services import evaluation_report_service as reports
from backend.app.services.experiment_run_service import save_experiment_run


def make_query(
    case_id=1,
    *,
    hit=1.0,
    precision=1.0,
    recall=1.0,
    mrr=1.0,
    faithfulness=1.0,
    hallucination=0.0,
    correctness=1.0,
    relevance=1.0,
):
    return {
        "evaluation_case_id": case_id,
        "question": f"Question {case_id}?",
        "answer": "Public answer",
        "retrieval_metrics": {
            "hit_at_k": hit,
            "precision_at_k": precision,
            "recall_at_k": recall,
            "reciprocal_rank": mrr,
        },
        "answer_metrics": {
            "faithfulness": faithfulness,
            "hallucination": hallucination,
            "correctness": correctness,
            "relevance": relevance,
        },
    }


def make_summary(
    name,
    *,
    hit=1.0,
    precision=1.0,
    recall=1.0,
    mrr=1.0,
    faithfulness=1.0,
    hallucination=0.0,
    correctness=1.0,
    relevance=1.0,
    queries=None,
):
    return {
        "experiment_name": name,
        "configuration": {
            "strategy": name,
            "chunk_size": 120,
            "chunk_overlap": 20,
            "top_k": 3,
        },
        "chunk_count": 2,
        "document_count": 1,
        "metrics": {
            "hit_at_k": hit,
            "precision_at_k": precision,
            "recall_at_k": recall,
            "mrr": mrr,
        },
        "answer_metrics": {
            "faithfulness": faithfulness,
            "hallucination": hallucination,
            "correctness": correctness,
            "relevance": relevance,
        },
        "score": mrr,
        "queries": queries or [make_query()],
    }


def test_query_failure_labels_and_primary_priority():
    query = make_query(
        hit=0,
        faithfulness=0.79,
        hallucination=0.21,
        correctness=0.69,
        relevance=0.74,
    )

    analysis = reports.classify_query(query)

    assert analysis.labels == [
        "retrieval_failure",
        "low_faithfulness",
        "hallucination",
        "low_correctness",
        "low_relevance",
    ]
    assert analysis.primary_classification == "retrieval_failure"
    assert analysis.percentage_metrics["faithfulness"] == "79.0%"


def test_threshold_boundaries_are_good_result():
    analysis = reports.classify_query(
        make_query(
            hit=1,
            faithfulness=0.80,
            hallucination=0,
            correctness=0.70,
            relevance=0.75,
        )
    )

    assert analysis.labels == ["good_result"]
    assert analysis.primary_classification == "good_result"


def test_score_matches_agreed_formula():
    summary = make_summary(
        "hybrid",
        correctness=0.8,
        faithfulness=0.9,
        relevance=0.7,
        mrr=0.6,
        recall=0.5,
        hit=1.0,
        precision=0.4,
    )

    assert reports.recommendation_score(summary) == 0.735


def test_guardrail_passing_configuration_is_preferred_over_higher_score():
    safe = make_summary(
        "safe",
        hit=0.5,
        precision=0.5,
        recall=0.5,
        mrr=0.5,
        faithfulness=0.8,
        hallucination=0.2,
        correctness=0.7,
        relevance=0.75,
    )
    unsafe = make_summary(
        "unsafe",
        faithfulness=0.79,
        hallucination=0.21,
        correctness=1.0,
        relevance=1.0,
    )

    winner, ranking, report = reports.build_evaluation_report([unsafe, safe])

    assert reports.recommendation_score(unsafe) > reports.recommendation_score(safe)
    assert winner["experiment_name"] == "safe"
    assert ranking[0]["experiment_name"] == "safe"
    assert report["passes_guardrails"] is True


def test_no_guardrail_pass_uses_highest_score_and_warns():
    lower = make_summary(
        "lower",
        faithfulness=0.6,
        hallucination=0.4,
        correctness=0.6,
        relevance=0.6,
        mrr=0.5,
    )
    higher = make_summary(
        "higher",
        faithfulness=0.7,
        hallucination=0.3,
        correctness=0.65,
        relevance=0.7,
        mrr=0.9,
    )

    winner, _, report = reports.build_evaluation_report([lower, higher])

    assert winner["experiment_name"] == "higher"
    assert report["passes_guardrails"] is False
    assert report["guardrail_status"].startswith("No configuration passed")
    assert report["why_it_won"].startswith("No configuration passed")


@pytest.mark.parametrize(
    ("field", "first", "second"),
    [
        ("correctness", 0.8, 0.9),
        ("faithfulness", 0.85, 0.95),
        ("mrr", 0.7, 0.9),
        ("recall", 0.7, 0.9),
        ("relevance", 0.8, 0.9),
        ("precision", 0.7, 0.9),
    ],
)
def test_tie_break_metric_order_is_deterministic(monkeypatch, field, first, second):
    monkeypatch.setattr(reports, "recommendation_score", lambda summary: 0.8)
    values = {
        "correctness": 0.8,
        "faithfulness": 0.9,
        "mrr": 0.8,
        "recall": 0.8,
        "relevance": 0.8,
        "precision": 0.8,
    }
    first_values = {**values, field: first}
    second_values = {**values, field: second}
    first_summary = make_summary("first", **first_values)
    second_summary = make_summary("second", **second_values)

    winner, _, _ = reports.build_evaluation_report([first_summary, second_summary])

    # Earlier tie-break fields remain equal in each case, so the varied field decides.
    assert winner["experiment_name"] == "second"


def test_exact_tie_keeps_original_experiment_order(monkeypatch):
    monkeypatch.setattr(reports, "recommendation_score", lambda summary: 0.8)
    first = make_summary("first")
    second = make_summary("second")

    winner, ranking, _ = reports.build_evaluation_report([first, second])

    assert winner["experiment_name"] == "first"
    assert [item["experiment_name"] for item in ranking] == ["first", "second"]


def test_report_is_safe_compact_and_limited_to_five_failures():
    queries = []
    for case_id in range(1, 8):
        query = make_query(case_id, hit=0, correctness=0.2)
        query["reference_answer"] = "SECRET_REFERENCE"
        query["source_evidence"] = "SECRET_EVIDENCE"
        query["results"] = [{"text": "SECRET_CONTEXT"}]
        query["judge"] = "SECRET_JUDGE_INTERNALS"
        queries.append(query)

    _, _, report = reports.build_evaluation_report(
        [make_summary("hybrid", queries=queries)]
    )
    serialized = json.dumps(report)

    assert len(report["important_failed_queries"]) == 5
    assert len(report["per_query_classifications"]) == 7
    assert report["failure_counts"]["retrieval_failure"] == 7
    assert report["failure_rates"]["retrieval_failure"] == 1.0
    assert "SECRET_REFERENCE" not in serialized
    assert "SECRET_EVIDENCE" not in serialized
    assert "SECRET_CONTEXT" not in serialized
    assert "SECRET_JUDGE_INTERNALS" not in serialized


def test_report_building_has_no_provider_or_api_dependency(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Day 10 attempted to construct an LLM provider")

    monkeypatch.setattr(
        "backend.app.llm.openai_provider.OpenAIProvider",
        forbidden,
    )

    winner, _, report = reports.build_evaluation_report([make_summary("hybrid")])
    summary = reports.build_response_summary(report)

    assert winner["experiment_name"] == "hybrid"
    assert report["analysis_version"] == "day10-v1"
    assert summary["recommended_strategy"] == "hybrid"


def test_response_summary_is_concise_percentage_friendly_and_non_mutating():
    experiment = make_summary(
        "semantic",
        faithfulness=0.722,
        hallucination=0.278,
        correctness=0.779,
        relevance=1.0,
        mrr=0.95,
        recall=0.9,
        hit=1.0,
        precision=0.6,
    )
    _, _, report = reports.build_evaluation_report([experiment])
    original_report = json.dumps(report, sort_keys=True)

    summary = reports.build_response_summary(report)

    assert set(summary) == {
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
    assert summary["recommended_strategy"] == "semantic"
    assert summary["recommended_experiment"] == "semantic"
    assert summary["recommendation_score"].endswith("%")
    assert summary["configuration"] == experiment["configuration"]
    assert summary["key_metrics"] == {
        "faithfulness": "72.2%",
        "relevance": "100.0%",
        "correctness": "77.9%",
        "hallucination": "27.8%",
        "mrr": "95.0%",
        "recall_at_k": "90.0%",
    }
    assert "Answers remained highly relevant." in summary["strengths"]
    assert "Retrieval quality was strong." in summary["strengths"]
    assert "Faithfulness was below the 80% target." in summary["weaknesses"]
    assert "Hallucination was above the 20% limit." in summary["weaknesses"]
    assert json.dumps(report, sort_keys=True) == original_report


def test_report_is_persisted_on_recommended_experiment_run():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        project = Project(id=7, owner_id="owner", name="Day 10")
        db.add(project)
        db.commit()
        summary = make_summary("hybrid")
        recommended, _, report = reports.build_evaluation_report([summary])

        run = save_experiment_run(
            db,
            project.id,
            recommended,
            analysis_report=report,
        )

        assert run.analysis_report["recommended_experiment"] == "hybrid"
        assert run.analysis_report["analysis_version"] == "day10-v1"


def test_day10_migration_upgrade_and_downgrade_preserves_existing_row():
    path = Path("alembic/versions/b20d10000001_add_day10_analysis_report.py")
    spec = importlib.util.spec_from_file_location("day10_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE experiment_runs (id INTEGER PRIMARY KEY, mrr FLOAT)"
        )
        connection.exec_driver_sql("INSERT INTO experiment_runs VALUES (1, 0.75)")
        operations = Operations(MigrationContext.configure(connection))
        original_op = migration.op
        migration.op = operations
        try:
            migration.upgrade()
            assert "analysis_report" in {
                column["name"] for column in inspect(connection).get_columns("experiment_runs")
            }
            assert connection.exec_driver_sql(
                "SELECT mrr, analysis_report FROM experiment_runs"
            ).one() == (0.75, None)
            migration.downgrade()
            assert "analysis_report" not in {
                column["name"] for column in inspect(connection).get_columns("experiment_runs")
            }
            assert connection.exec_driver_sql(
                "SELECT mrr FROM experiment_runs"
            ).scalar() == 0.75
        finally:
            migration.op = original_op
