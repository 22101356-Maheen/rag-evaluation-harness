from collections import defaultdict
from pathlib import Path

from backend.app.db.qdrant import get_project_chunks, store_chunks
from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.rag.embeddings.embedder import embed_texts
from backend.app.schemas.experiment import (
    ExperimentConfig,
    ProjectEvaluationQuery,
)
from backend.app.services.evaluation_service import (
    evaluate_project_retrieval,
    evaluate_retrieval,
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
