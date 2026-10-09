import re
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.qdrant import get_project_chunks, store_chunks
from backend.app.llm.openai_provider import OpenAIProvider
from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.rag.embeddings.embedder import embed_texts
from backend.app.schemas.evaluation import EvaluationRunRequest
from backend.app.schemas.experiment import (
    ExperimentConfig,
    ProjectEvaluationQuery,
)
from backend.app.services.answer_evaluation_service import evaluate_answer
from backend.app.services.document_service import get_project_documents
from backend.app.services.evaluation_service import (
    EvaluationDatasetError,
    evaluate_project_retrieval,
    evaluate_retrieval,
)
from backend.app.services.experiment_run_service import save_experiment_run
from backend.app.services.synthetic_dataset_service import (
    get_or_create_dataset,
    normalized,
    quote_spans,
)

CORPUS_PATH = Path(
    "data/evaluation/rag_retrieval_corpus.txt"
)


class ProjectCorpusEmptyError(ValueError):
    """Raised when a project has no stored chunks to benchmark."""


def load_experiment_corpus() -> str:
    """Load the fixed source corpus used for controlled experiments."""

    return CORPUS_PATH.read_text(
        encoding="utf-8",
    )


def run_experiment(
    config: ExperimentConfig,
) -> dict:
    """Run one controlled experiment using the fixed source corpus."""

    corpus = load_experiment_corpus()
    chunks = chunk_text(
        text=corpus,
        chunk_size=config.chunk_size,
        overlap=config.chunk_overlap,
    )
    embeddings = embed_texts(chunks)

    store_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    evaluation = evaluate_retrieval(
        top_k=config.top_k,
    )

    return {
        "experiment_name": config.name,
        "configuration": {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "strategy": config.strategy,
        },
        "chunk_count": len(chunks),
        "evaluation": evaluation,
    }


def get_strategy_summary(
    experiment_result: dict,
    strategy: str,
) -> dict:
    """Extract the selected strategy's main evaluation metrics."""

    strategy_metrics = experiment_result[
        "evaluation"
    ][
        "strategies"
    ][
        strategy
    ]

    return {
        "hit_at_k": strategy_metrics["average_hit_at_k"],
        "precision_at_k": strategy_metrics["average_precision_at_k"],
        "recall_at_k": strategy_metrics["average_recall_at_k"],
        "mrr": strategy_metrics["mean_reciprocal_rank"],
    }


def _rank_experiments(summaries: list[dict]) -> dict:
    ranked_results = sorted(
        summaries,
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "experiment_count": len(ranked_results),
        "best_experiment": ranked_results[0],
        "ranking": ranked_results,
    }


def run_experiment_batch(
    configs: list[ExperimentConfig],
) -> dict:
    """Run controlled configurations and return a ranked summary."""

    summaries = []

    for config in configs:
        result = run_experiment(config)
        metrics = get_strategy_summary(
            experiment_result=result,
            strategy=config.strategy,
        )

        summaries.append(
            {
                "experiment_name": config.name,
                "configuration": result["configuration"],
                "chunk_count": result["chunk_count"],
                "metrics": metrics,
                "score": metrics["mrr"],
            }
        )

    return _rank_experiments(summaries)


def _merge_overlapping_chunks(chunks: list[str]) -> str:
    """Rebuild one document's word stream from stored upload chunks."""

    merged_words: list[str] = []

    for chunk in chunks:
        chunk_words = chunk.split()

        if not merged_words:
            merged_words.extend(chunk_words)
            continue

        maximum_overlap = min(len(merged_words), len(chunk_words))
        overlap = maximum_overlap

        while overlap > 0:
            if merged_words[-overlap:] == chunk_words[:overlap]:
                break
            overlap -= 1

        merged_words.extend(chunk_words[overlap:])

    return " ".join(merged_words)


def load_project_corpus(project_id: int) -> list[dict]:
    """Load and reconstruct only documents for the selected project."""

    stored_chunks = get_project_chunks(project_id=project_id)

    if not stored_chunks:
        raise ProjectCorpusEmptyError(
            "The project has no uploaded document chunks to benchmark."
        )

    chunks_by_document: dict[int, list[dict]] = defaultdict(list)

    for chunk in stored_chunks:
        chunks_by_document[chunk["document_id"]].append(chunk)

    documents = []

    for document_id, document_chunks in sorted(
        chunks_by_document.items()
    ):
        ordered_chunks = sorted(
            document_chunks,
            key=lambda chunk: chunk["chunk_index"],
        )
        text = _merge_overlapping_chunks(
            [chunk["text"] for chunk in ordered_chunks]
        )

        if text:
            documents.append(
                {
                    "document_id": document_id,
                    "text": text,
                }
            )

    if not documents:
        raise ProjectCorpusEmptyError(
            "The project has no non-empty document text to benchmark."
        )

    return documents


def build_project_experiment_chunks(
    documents: list[dict],
    config: ExperimentConfig,
) -> list[dict]:
    """Rechunk project documents without combining document boundaries."""

    experiment_chunks = []

    for document in documents:
        chunks = chunk_text(
            text=document["text"],
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap,
        )

        for chunk_index, text in enumerate(chunks):
            document_id = document["document_id"]
            experiment_chunks.append(
                {
                    "chunk_id": f"{document_id}:{chunk_index}",
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "text": text,
                }
            )

    return experiment_chunks


def run_project_experiment(
    documents: list[dict],
    config: ExperimentConfig,
    evaluation_queries: list[dict],
) -> dict:
    """Run one configuration against reconstructed project documents."""

    chunks = build_project_experiment_chunks(
        documents=documents,
        config=config,
    )
    embeddings = embed_texts(
        [chunk["text"] for chunk in chunks]
    )
    evaluation = evaluate_project_retrieval(
        project_chunks=chunks,
        chunk_embeddings=embeddings,
        evaluation_queries=evaluation_queries,
        top_k=config.top_k,
        strategy=config.strategy,
    )

    return {
        "experiment_name": config.name,
        "configuration": {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "strategy": config.strategy,
        },
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "evaluation": evaluation,
    }


def run_project_experiment_batch(
    project_id: int,
    configs: list[ExperimentConfig],
    evaluation_queries: list[ProjectEvaluationQuery],
) -> dict:
    """Benchmark configurations using only one project's documents."""

    documents = load_project_corpus(project_id=project_id)
    query_data = [
        query.model_dump()
        for query in evaluation_queries
    ]
    summaries = []

    for config in configs:
        result = run_project_experiment(
            documents=documents,
            config=config,
            evaluation_queries=query_data,
        )
        metrics = get_strategy_summary(
            experiment_result=result,
            strategy=config.strategy,
        )

        summaries.append(
            {
                "experiment_name": config.name,
                "configuration": result["configuration"],
                "document_count": result["document_count"],
                "chunk_count": result["chunk_count"],
                "metrics": metrics,
                "score": metrics["mrr"],
            }
        )

    comparison = _rank_experiments(summaries)
    comparison["evaluation_query_count"] = len(query_data)
    return comparison


def _snapshot_documents(chunks: list[dict]) -> list[dict]:
    """Recover word streams using the existing uploader's fixed 120/20 layout."""
    grouped = defaultdict(list)
    for chunk in chunks:
        grouped[chunk["document_id"]].append(chunk)
    documents = []
    for document_id, stored in sorted(grouped.items()):
        stored.sort(key=lambda item: item["chunk_index"])
        if [c["chunk_index"] for c in stored] != list(range(len(stored))):
            raise EvaluationDatasetError("Project source chunks are incomplete or duplicated.")
        # Use known overlap, not longest matching suffix: repeated text must survive.
        words = stored[0]["text"].split()
        for chunk in stored[1:]:
            words.extend(chunk["text"].split()[20:])
        text = " ".join(words)
        if chunk_text(text, 120, 20) != [c["text"] for c in stored]:
            raise EvaluationDatasetError("Project source chunks do not match the upload layout.")
        documents.append({"document_id": document_id, "text": text})
    return documents


def _case_queries(cases, documents: list[dict], config: ExperimentConfig) -> list[dict]:
    """Map verified evidence word spans into this configuration's chunk boundaries."""
    texts = {d["document_id"]: normalized(d["text"]) for d in documents}
    queries = []
    for case in cases:
        relevant = set()
        for evidence in case.source_evidence:
            text = texts[evidence["document_id"]]
            words = list(re.finditer(r"\S+", text))
            spans = quote_spans(evidence["quote"], text)
            for start, end in spans:
                stride = config.chunk_size - config.chunk_overlap
                for index, chunk_start in enumerate(range(0, len(words), stride)):
                    chunk_end = min(chunk_start + config.chunk_size, len(words))
                    if words[chunk_start].start() < end and words[chunk_end - 1].end() > start:
                        relevant.add(f"{evidence['document_id']}:{index}")
                    if chunk_end == len(words):
                        break
            if not spans:
                raise EvaluationDatasetError("Stored source evidence no longer matches project text.")
        queries.append({"query": case.question, "relevant_ids": relevant})
    return queries


def run_project_evaluation(
    db: Session, project_id: int, request: EvaluationRunRequest,
) -> dict:
    """Orchestrate Day 9 after the route has checked project ownership."""
    ready_ids = {
        document.id for document in get_project_documents(db, project_id)
        if document.status == "ready"
    }
    chunks = [c for c in get_project_chunks(project_id) if c["document_id"] in ready_ids]
    if not chunks:
        raise ProjectCorpusEmptyError("Upload at least one ready document before evaluation.")
    if {c["document_id"] for c in chunks} != ready_ids:
        raise EvaluationDatasetError("Some ready documents are missing their source chunks.")
    documents = _snapshot_documents(chunks)
    configs = request.experiments or [
        ExperimentConfig(name=strategy, strategy=strategy)
        for strategy in ("semantic", "bm25", "hybrid")
    ]
    provider = OpenAIProvider()
    try:
        dataset, cases, reused = get_or_create_dataset(db, project_id, chunks, request, provider)
        # Resolve all labels before spending tokens on answer generation.
        queries_by_config = [_case_queries(cases, documents, config) for config in configs]
        summaries = []
        for config, queries in zip(configs, queries_by_config):
            scratch = build_project_experiment_chunks(documents, config)
            embeddings = [] if config.strategy == "bm25" else embed_texts([c["text"] for c in scratch])
            evaluation = evaluate_project_retrieval(
                scratch, embeddings, queries, config.top_k, config.strategy,
                include_results=True,
            )
            retrieval_queries = evaluation["strategies"][config.strategy]["queries"]
            answers = []
            for case, retrieved in zip(cases, retrieval_queries):
                result = evaluate_answer(case, retrieved["results"], config.top_k, provider)
                result["retrieval_metrics"] = {
                    key: retrieved[key] for key in (
                        "hit_at_k", "precision_at_k", "recall_at_k", "reciprocal_rank"
                    )
                }
                answers.append(result)
            metrics = get_strategy_summary({"evaluation": evaluation}, config.strategy)
            summaries.append({
                "experiment_name": config.name,
                "configuration": config.model_dump(exclude={"name"}),
                "chunk_count": len(scratch),
                "document_count": len(documents),
                "metrics": metrics,
                "score": metrics["mrr"],
                "answer_metrics": {
                    metric: round(sum(a["answer_metrics"][metric] for a in answers) / len(answers), 4)
                    for metric in ("faithfulness", "relevance", "correctness", "hallucination")
                },
                "queries": answers,
            })
        comparison = _rank_experiments(summaries)
        run = save_experiment_run(
            db, project_id, comparison["best_experiment"],
            evaluation_dataset_id=dataset.id,
            generation_model=settings.generation_model,
            evaluator_model=settings.evaluation_model,
        )
        return {
            "project_id": project_id,
            "evaluation_dataset_id": dataset.id,
            "dataset_reused": reused,
            "dataset_mode": dataset.mode,
            "case_count": len(cases),
            "experiment_run_id": run.id,
            "best_experiment": comparison["best_experiment"],
            "ranking": comparison["ranking"],
        }
    finally:
        provider.close()
