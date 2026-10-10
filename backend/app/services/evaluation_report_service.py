"""Deterministic Day 10 failure analysis and recommendation reporting."""

from backend.app.schemas.evaluation import (
    ConfigurationFailureAnalysis,
    EvaluationReport,
    QueryFailureAnalysis,
)

ANALYSIS_VERSION = "day10-v1"

FAILURE_LABELS = (
    "retrieval_failure",
    "low_faithfulness",
    "hallucination",
    "low_correctness",
    "low_relevance",
)

PRIMARY_PRIORITY = (*FAILURE_LABELS, "good_result")

GUARDRAILS = {
    "faithfulness": (">=", 0.80),
    "hallucination": ("<=", 0.20),
    "correctness": (">=", 0.70),
    "relevance": (">=", 0.75),
}

SCORE_WEIGHTS = {
    "correctness": 0.30,
    "faithfulness": 0.20,
    "relevance": 0.15,
    "mrr": 0.15,
    "recall_at_k": 0.10,
    "hit_at_k": 0.05,
    "precision_at_k": 0.05,
}


def _percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_response_summary(report: dict) -> dict:
    """Create a concise user-facing view without changing report calculations."""

    metrics = report["percentage_metrics"]
    numeric_metrics = next(
        analysis["metrics"]
        for analysis in report["configuration_analyses"]
        if (
            analysis["experiment_name"] == report["recommended_experiment"]
            and analysis["configuration"] == report["configuration"]
        )
    )

    strengths = []
    if numeric_metrics["faithfulness"] >= 0.90:
        strengths.append("Answers were highly faithful to the retrieved context.")
    if numeric_metrics["hallucination"] <= 0.10:
        strengths.append("The hallucination rate was low.")
    if numeric_metrics["correctness"] >= 0.80:
        strengths.append("Answer correctness was strong.")
    if numeric_metrics["relevance"] >= 0.80:
        strengths.append("Answers remained highly relevant.")
    if numeric_metrics["mrr"] >= 0.80 or numeric_metrics["recall_at_k"] >= 0.80:
        strengths.append("Retrieval quality was strong.")
    if not strengths:
        strengths.append("It provided the best balance among the tested configurations.")

    weaknesses = []
    if numeric_metrics["faithfulness"] < 0.80:
        weaknesses.append("Faithfulness was below the 80% target.")
    if numeric_metrics["hallucination"] > 0.20:
        weaknesses.append("Hallucination was above the 20% limit.")
    if numeric_metrics["correctness"] < 0.70:
        weaknesses.append("Correctness was below the 70% target.")
    if numeric_metrics["relevance"] < 0.75:
        weaknesses.append("Relevance was below the 75% target.")
    if report["failure_rates"]["retrieval_failure"] >= 0.20:
        weaknesses.append("Retrieval failed for a meaningful share of the questions.")
    if not weaknesses:
        weaknesses.append("No major weakness crossed the configured quality limits.")

    if report["passes_guardrails"]:
        why_recommended = [
            "It passed all quality guardrails.",
            "It had the highest recommendation score among eligible configurations.",
        ]
    else:
        why_recommended = [
            "No tested configuration passed all quality guardrails.",
            "It had the highest recommendation score overall.",
        ]

    configuration = report["configuration"]
    return {
        "recommended_strategy": report["strategy"],
        "recommended_experiment": report["recommended_experiment"],
        "recommendation_score": _percentage(report["recommendation_score"]),
        "configuration": {
            "chunk_size": configuration["chunk_size"],
            "chunk_overlap": configuration["chunk_overlap"],
            "top_k": configuration["top_k"],
            "strategy": configuration["strategy"],
        },
        "key_metrics": {
            "faithfulness": metrics["faithfulness"],
            "relevance": metrics["relevance"],
            "correctness": metrics["correctness"],
            "hallucination": metrics["hallucination"],
            "mrr": metrics["mrr"],
            "recall_at_k": metrics["recall_at_k"],
        },
        "guardrail_status": report["guardrail_status"],
        "why_recommended": why_recommended,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "next_step": report["practical_next_recommendation"],
    }


def _combined_metrics(summary: dict) -> dict[str, float]:
    retrieval = summary["metrics"]
    answer = summary["answer_metrics"]
    return {
        "hit_at_k": retrieval["hit_at_k"],
        "precision_at_k": retrieval["precision_at_k"],
        "recall_at_k": retrieval["recall_at_k"],
        "mrr": retrieval["mrr"],
        "faithfulness": answer["faithfulness"],
        "relevance": answer["relevance"],
        "correctness": answer["correctness"],
        "hallucination": answer["hallucination"],
    }


def classify_query(query: dict) -> QueryFailureAnalysis:
    """Classify one existing Day 9 query result without external calls."""

    retrieval = query["retrieval_metrics"]
    answer = query["answer_metrics"]
    metrics = {
        "hit_at_k": retrieval["hit_at_k"],
        "precision_at_k": retrieval["precision_at_k"],
        "recall_at_k": retrieval["recall_at_k"],
        "mrr": retrieval["reciprocal_rank"],
        "faithfulness": answer["faithfulness"],
        "relevance": answer["relevance"],
        "correctness": answer["correctness"],
        "hallucination": answer["hallucination"],
    }
    labels: list[str] = []
    reasons: list[str] = []

    if metrics["hit_at_k"] == 0:
        labels.append("retrieval_failure")
        reasons.append(
            "No expected evidence chunk appeared in the retrieved top-k results."
        )
    if metrics["faithfulness"] < 0.80:
        labels.append("low_faithfulness")
        reasons.append(
            f"Faithfulness {_percentage(metrics['faithfulness'])} is below 80.0%."
        )
    if metrics["hallucination"] > 0:
        labels.append("hallucination")
        reasons.append(
            f"Unsupported claims produced a {_percentage(metrics['hallucination'])} "
            "hallucination rate."
        )
    if metrics["correctness"] < 0.70:
        labels.append("low_correctness")
        reasons.append(
            f"Correctness {_percentage(metrics['correctness'])} is below 70.0%."
        )
    if metrics["relevance"] < 0.75:
        labels.append("low_relevance")
        reasons.append(
            f"Relevance {_percentage(metrics['relevance'])} is below 75.0%."
        )
    if not labels:
        labels.append("good_result")
        reasons.append("The query passed every configured failure threshold.")

    primary = next(label for label in PRIMARY_PRIORITY if label in labels)
    return QueryFailureAnalysis(
        evaluation_case_id=query["evaluation_case_id"],
        question=query["question"],
        labels=labels,
        primary_classification=primary,
        metrics=metrics,
        percentage_metrics={key: _percentage(value) for key, value in metrics.items()},
        reasons=reasons,
    )


def recommendation_score(summary: dict) -> float:
    metrics = _combined_metrics(summary)
    return round(
        sum(metrics[name] * weight for name, weight in SCORE_WEIGHTS.items()),
        4,
    )


def _failed_guardrails(metrics: dict[str, float]) -> list[str]:
    failures = []
    for name, (operator, threshold) in GUARDRAILS.items():
        value = metrics[name]
        failed = value < threshold if operator == ">=" else value > threshold
        if failed:
            failures.append(
                f"{name} {_percentage(value)} does not meet "
                f"{operator} {_percentage(threshold)}"
            )
    return failures


def _analyze_configuration(summary: dict) -> ConfigurationFailureAnalysis:
    metrics = _combined_metrics(summary)
    query_analyses = [classify_query(query) for query in summary["queries"]]
    counts = {
        label: sum(label in query.labels for query in query_analyses)
        for label in (*FAILURE_LABELS, "good_result")
    }
    query_count = len(query_analyses)
    rates = {
        label: round(count / query_count, 4)
        for label, count in counts.items()
    }
    failed_guardrails = _failed_guardrails(metrics)
    return ConfigurationFailureAnalysis(
        experiment_name=summary["experiment_name"],
        strategy=summary["configuration"]["strategy"],
        configuration=summary["configuration"],
        recommendation_score=recommendation_score(summary),
        metrics=metrics,
        percentage_metrics={key: _percentage(value) for key, value in metrics.items()},
        passes_guardrails=not failed_guardrails,
        failed_guardrails=failed_guardrails,
        failure_counts=counts,
        failure_rates=rates,
        per_query_classifications=query_analyses,
    )


def _selection_key(summary: dict, analysis: ConfigurationFailureAnalysis, index: int):
    metrics = _combined_metrics(summary)
    return (
        analysis.recommendation_score,
        metrics["correctness"],
        metrics["faithfulness"],
        metrics["mrr"],
        metrics["recall_at_k"],
        metrics["relevance"],
        metrics["precision_at_k"],
        -index,
    )


def _why_it_won(
    winner: ConfigurationFailureAnalysis,
    alternatives: list[ConfigurationFailureAnalysis],
    any_passed: bool,
) -> str:
    if any_passed:
        opening = (
            f"{winner.experiment_name} passed every quality guardrail and had the "
            f"highest eligible recommendation score ({_percentage(winner.recommendation_score)})."
        )
    else:
        opening = (
            "No configuration passed every quality guardrail. "
            f"{winner.experiment_name} is the fallback recommendation because it had "
            f"the highest overall recommendation score ({_percentage(winner.recommendation_score)})."
        )
    if not alternatives:
        return opening

    comparisons = []
    for alternative in alternatives:
        comparisons.append(
            f"versus {alternative.experiment_name}: score "
            f"{_percentage(winner.recommendation_score)} vs "
            f"{_percentage(alternative.recommendation_score)}, correctness "
            f"{winner.percentage_metrics['correctness']} vs "
            f"{alternative.percentage_metrics['correctness']}, and MRR "
            f"{winner.percentage_metrics['mrr']} vs "
            f"{alternative.percentage_metrics['mrr']}"
        )
    return f"{opening} " + "; ".join(comparisons) + "."


def _strengths(analysis: ConfigurationFailureAnalysis) -> list[str]:
    metrics = analysis.percentage_metrics
    values = analysis.per_query_classifications
    strengths = []
    aggregate = analysis.metrics
    if aggregate["faithfulness"] >= 0.90:
        strengths.append(f"High answer faithfulness ({metrics['faithfulness']}).")
    if aggregate["hallucination"] <= 0.10:
        strengths.append(f"Low hallucination rate ({metrics['hallucination']}).")
    if aggregate["correctness"] >= 0.80:
        strengths.append(f"Strong answer correctness ({metrics['correctness']}).")
    if aggregate["relevance"] >= 0.80:
        strengths.append(f"Answers stayed relevant ({metrics['relevance']}).")
    if aggregate["mrr"] >= 0.80 or aggregate["recall_at_k"] >= 0.80:
        strengths.append(
            f"Strong retrieval quality (MRR {metrics['mrr']}, recall {metrics['recall_at_k']})."
        )
    good_count = sum(q.primary_classification == "good_result" for q in values)
    if good_count:
        strengths.append(f"{good_count} of {len(values)} queries passed every failure threshold.")
    return strengths or ["It achieved the strongest balanced result among the evaluated configurations."]


def _weaknesses(analysis: ConfigurationFailureAnalysis) -> list[str]:
    weaknesses = list(analysis.failed_guardrails)
    count = len(analysis.per_query_classifications)
    for label in FAILURE_LABELS:
        failures = analysis.failure_counts[label]
        if failures:
            display = label.replace("_", " ")
            weaknesses.append(
                f"{failures} of {count} queries ({_percentage(failures / count)}) "
                f"were classified as {display}."
            )
    return weaknesses or ["No material weakness crossed the configured thresholds."]


def _important_failures(
    analysis: ConfigurationFailureAnalysis,
) -> list[QueryFailureAnalysis]:
    priority = {label: index for index, label in enumerate(PRIMARY_PRIORITY)}
    failed = [
        (index, query)
        for index, query in enumerate(analysis.per_query_classifications)
        if query.primary_classification != "good_result"
    ]
    failed.sort(
        key=lambda item: (
            priority[item[1].primary_classification],
            item[1].metrics["correctness"],
            item[1].metrics["faithfulness"],
            item[1].metrics["relevance"],
            item[0],
        )
    )
    return [query for _, query in failed[:5]]


def _next_recommendation(
    winner: ConfigurationFailureAnalysis,
    alternatives: list[ConfigurationFailureAnalysis],
) -> str:
    rates = winner.failure_rates
    if rates["retrieval_failure"] >= 0.20:
        better_recall = [
            alternative
            for alternative in alternatives
            if alternative.metrics["recall_at_k"]
            >= winner.metrics["recall_at_k"] + 0.10
        ]
        if better_recall:
            candidate = max(
                better_recall,
                key=lambda item: item.metrics["recall_at_k"],
            )
            return (
                "Prioritize retrieval tuning. Test the recommended configuration against "
                f"{candidate.experiment_name}, which achieved materially higher recall."
            )
        return (
            "Prioritize retrieval tuning by testing a higher top-k value or adjusted chunk "
            "size and overlap, then rerun the same evaluation dataset."
        )
    if rates["low_faithfulness"] >= 0.10 or rates["hallucination"] >= 0.10:
        return (
            "Keep this retrieval configuration, but tighten abstention and citation "
            "requirements before deployment and recheck the flagged queries."
        )
    if rates["low_correctness"] >= 0.20:
        return (
            "Review the flagged source sections and answer instructions: retrieval is "
            "reaching evidence, but answer correctness needs improvement."
        )
    if rates["low_relevance"] >= 0.20:
        return (
            "Tighten answer instructions so responses address the question directly and "
            "omit retrieved details that do not answer it."
        )
    return (
        "Use this configuration as the current default and validate it with a larger, "
        "representative evaluation dataset before production rollout."
    )


def build_evaluation_report(summaries: list[dict]) -> tuple[dict, list[dict], dict]:
    """Return recommended result, deterministic ranking, and report snapshot."""

    if not summaries:
        raise ValueError("At least one experiment summary is required.")

    analyses = [_analyze_configuration(summary) for summary in summaries]
    passing_indexes = [
        index for index, analysis in enumerate(analyses) if analysis.passes_guardrails
    ]
    candidate_indexes = passing_indexes or list(range(len(summaries)))
    winner_index = max(
        candidate_indexes,
        key=lambda index: _selection_key(summaries[index], analyses[index], index),
    )

    ranked_indexes = sorted(
        range(len(summaries)),
        key=lambda index: (
            analyses[index].passes_guardrails,
            *_selection_key(summaries[index], analyses[index], index),
        ),
        reverse=True,
    )
    ranked = []
    for index in ranked_indexes:
        item = {**summaries[index]}
        item["recommendation_score"] = analyses[index].recommendation_score
        item["passes_guardrails"] = analyses[index].passes_guardrails
        item["failed_guardrails"] = analyses[index].failed_guardrails
        ranked.append(item)

    winner = analyses[winner_index]
    alternatives = [analysis for index, analysis in enumerate(analyses) if index != winner_index]
    report = EvaluationReport(
        analysis_version=ANALYSIS_VERSION,
        recommended_experiment=winner.experiment_name,
        strategy=winner.strategy,
        configuration=winner.configuration,
        recommendation_score=winner.recommendation_score,
        percentage_metrics=winner.percentage_metrics,
        passes_guardrails=winner.passes_guardrails,
        guardrail_status=(
            "All quality guardrails passed."
            if winner.passes_guardrails
            else "No configuration passed all quality guardrails; this is the best fallback."
        ),
        why_it_won=_why_it_won(winner, alternatives, bool(passing_indexes)),
        key_strengths=_strengths(winner),
        key_weaknesses=_weaknesses(winner),
        failure_counts=winner.failure_counts,
        failure_rates=winner.failure_rates,
        per_query_classifications=winner.per_query_classifications,
        important_failed_queries=_important_failures(winner),
        practical_next_recommendation=_next_recommendation(winner, alternatives),
        configuration_analyses=analyses,
    ).model_dump()
    recommended = {**summaries[winner_index]}
    recommended["recommendation_score"] = analyses[winner_index].recommendation_score
    recommended["passes_guardrails"] = analyses[winner_index].passes_guardrails
    recommended["failed_guardrails"] = analyses[winner_index].failed_guardrails
    return recommended, ranked, report
