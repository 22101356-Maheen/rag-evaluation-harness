import json
import re
from collections.abc import Callable, Hashable
from pathlib import Path

from backend.app.db.qdrant import get_all_chunks, search_chunks
from backend.app.rag.embeddings.embedder import embed_query
from backend.app.rag.evaluation.metrics import (
    get_retrieved_chunk_ids,
    hit_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from backend.app.rag.retrieval.bm25 import retrieve_bm25
from backend.app.rag.retrieval.hybrid import reciprocal_rank_fusion
from backend.app.rag.retrieval.retriever import retrieve_top_k

EVALUATION_DATASET_PATH = Path(
    "data/evaluation/evaluation_queries.json"
)

STRATEGIES = (
    "semantic",
    "bm25",
    "hybrid",
)


class EvaluationDatasetError(ValueError):
    """Raised when evaluation labels do not match the evaluated corpus."""


def load_evaluation_queries() -> list[dict]:
    """Load controlled evaluation questions and expected evidence."""

    with EVALUATION_DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    """Normalize text before matching evidence against chunks."""

    tokens = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower(),
    )

    return " ".join(tokens)


def resolve_relevant_chunk_ids(
    chunks: list[str],
    expected_evidence: list[str],
    chunk_ids: list[Hashable] | None = None,
) -> set[Hashable]:
    """Resolve evidence to stable IDs for the current chunk configuration."""

    if chunk_ids is None:
        chunk_ids = list(range(len(chunks)))

    if len(chunks) != len(chunk_ids):
        raise ValueError("Each chunk must have a corresponding chunk ID.")

    normalized_chunks = [
        normalize_text(chunk)
        for chunk in chunks
    ]

    relevant_ids: set[Hashable] = set()

    for evidence in expected_evidence:
        normalized_evidence = normalize_text(evidence)

        if not normalized_evidence:
            continue

        exact_matches = [
            index
            for index, chunk in enumerate(normalized_chunks)
            if normalized_evidence in chunk
        ]

        if exact_matches:
            relevant_ids.update(
                chunk_ids[index]
                for index in exact_matches
            )
            continue

        evidence_tokens = set(normalized_evidence.split())
        best_chunk_index = None
        best_overlap = 0.0

        for index, chunk in enumerate(normalized_chunks):
            chunk_tokens = set(chunk.split())

            overlap = len(
                evidence_tokens & chunk_tokens
            ) / len(evidence_tokens)

            if overlap > best_overlap:
                best_overlap = overlap
                best_chunk_index = index

        if best_chunk_index is not None and best_overlap >= 0.6:
            relevant_ids.add(chunk_ids[best_chunk_index])

    return relevant_ids


def run_strategy(
    strategy: str,
    query: str,
    chunks: list[str],
    top_k: int,
) -> list[dict]:
    """Run one strategy against the resettable controlled collection."""

    if strategy == "bm25":
        return retrieve_bm25(
            query=query,
            chunks=chunks,
            top_k=top_k,
        )

    query_embedding = embed_query(query)

    if strategy == "semantic":
        return search_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
        )

    candidate_count = max(top_k * 3, top_k)

    semantic_results = search_chunks(
        query_embedding=query_embedding,
        top_k=candidate_count,
    )

    bm25_results = retrieve_bm25(
        query=query,
        chunks=chunks,
        top_k=candidate_count,
    )

    return reciprocal_rank_fusion(
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        top_k=top_k,
    )


def run_project_strategy(
    strategy: str,
    query: str,
    chunks: list[str],
    chunk_embeddings: list[list[float]],
    chunk_ids: list[Hashable],
    chunk_metadata: list[dict],
    top_k: int,
) -> list[dict]:
    """Run one strategy on project-derived scratch chunks in memory."""

    if strategy == "bm25":
        return retrieve_bm25(
            query=query,
            chunks=chunks,
            top_k=top_k,
            chunk_ids=chunk_ids,
            chunk_metadata=chunk_metadata,
        )

    if strategy == "semantic":
        return retrieve_top_k(
            query=query,
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            top_k=top_k,
            chunk_ids=chunk_ids,
            chunk_metadata=chunk_metadata,
        )

    candidate_count = max(top_k * 3, top_k)

    semantic_results = retrieve_top_k(
        query=query,
        chunks=chunks,
        chunk_embeddings=chunk_embeddings,
        top_k=candidate_count,
        chunk_ids=chunk_ids,
        chunk_metadata=chunk_metadata,
    )

    bm25_results = retrieve_bm25(
        query=query,
        chunks=chunks,
        top_k=candidate_count,
        chunk_ids=chunk_ids,
        chunk_metadata=chunk_metadata,
    )

    return reciprocal_rank_fusion(
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        top_k=top_k,
    )


def _evaluate_queries(
    evaluation_queries: list[dict],
    chunks: list[str],
    chunk_ids: list[Hashable],
    top_k: int,
    strategies: tuple[str, ...],
    strategy_runner: Callable[[str, str, int], list[dict]],
    include_results: bool = False,
) -> dict:
    if not evaluation_queries:
        raise EvaluationDatasetError(
            "At least one evaluation query is required."
        )

    strategy_results = {}

    for strategy in strategies:
        query_results = []
        total_hit = 0.0
        total_precision = 0.0
        total_recall = 0.0
        total_reciprocal_rank = 0.0

        for item in evaluation_queries:
            query = item["query"]
            relevant_ids = item.get("relevant_ids")
            if relevant_ids is None:
                relevant_ids = resolve_relevant_chunk_ids(
                    chunks=chunks,
                    expected_evidence=item["expected_evidence"],
                    chunk_ids=chunk_ids,
                )

            if not relevant_ids:
                raise EvaluationDatasetError(
                    "Expected evidence was not found in the evaluated "
                    f"corpus for query: {query}"
                )

            results = strategy_runner(strategy, query, top_k)
            retrieved_ids = get_retrieved_chunk_ids(results)

            hit = hit_at_k(retrieved_ids, relevant_ids, top_k)
            precision = precision_at_k(
                retrieved_ids,
                relevant_ids,
                top_k,
            )
            recall = recall_at_k(
                retrieved_ids,
                relevant_ids,
                top_k,
            )
            rr = reciprocal_rank(retrieved_ids, relevant_ids)

            total_hit += hit
            total_precision += precision
            total_recall += recall
            total_reciprocal_rank += rr

            query_results.append(
                {
                    "query": query,
                    "relevant_chunk_ids": sorted(
                        relevant_ids,
                        key=str,
                    ),
                    "retrieved_chunk_ids": retrieved_ids,
                    "hit_at_k": round(hit, 4),
                    "precision_at_k": round(precision, 4),
                    "recall_at_k": round(recall, 4),
                    "reciprocal_rank": round(rr, 4),
                }
            )
            if include_results:
                query_results[-1]["results"] = results

        query_count = len(evaluation_queries)
        strategy_results[strategy] = {
            "average_hit_at_k": round(total_hit / query_count, 4),
            "average_precision_at_k": round(
                total_precision / query_count,
                4,
            ),
            "average_recall_at_k": round(
                total_recall / query_count,
                4,
            ),
            "mean_reciprocal_rank": round(
                total_reciprocal_rank / query_count,
                4,
            ),
            "queries": query_results,
        }

    return {
        "top_k": top_k,
        "query_count": len(evaluation_queries),
        "strategies": strategy_results,
    }


def evaluate_retrieval(
    top_k: int = 3,
) -> dict:
    """Evaluate all strategies using the fixed controlled dataset."""

    evaluation_queries = load_evaluation_queries()
    chunks = get_all_chunks()

    return _evaluate_queries(
        evaluation_queries=evaluation_queries,
        chunks=chunks,
        chunk_ids=list(range(len(chunks))),
        top_k=top_k,
        strategies=STRATEGIES,
        strategy_runner=lambda strategy, query, limit: run_strategy(
            strategy=strategy,
            query=query,
            chunks=chunks,
            top_k=limit,
        ),
    )


def evaluate_project_retrieval(
    project_chunks: list[dict],
    chunk_embeddings: list[list[float]],
    evaluation_queries: list[dict],
    top_k: int,
    strategy: str,
    include_results: bool = False,
) -> dict:
    """Evaluate one configuration using explicit project-specific labels."""

    chunks = [chunk["text"] for chunk in project_chunks]
    chunk_ids = [chunk["chunk_id"] for chunk in project_chunks]
    chunk_metadata = [
        {
            "document_id": chunk["document_id"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in project_chunks
    ]

    return _evaluate_queries(
        evaluation_queries=evaluation_queries,
        chunks=chunks,
        chunk_ids=chunk_ids,
        top_k=top_k,
        strategies=(strategy,),
        include_results=include_results,
        strategy_runner=lambda selected, query, limit: (
            run_project_strategy(
                strategy=selected,
                query=query,
                chunks=chunks,
                chunk_embeddings=chunk_embeddings,
                chunk_ids=chunk_ids,
                chunk_metadata=chunk_metadata,
                top_k=limit,
            )
        ),
    )
