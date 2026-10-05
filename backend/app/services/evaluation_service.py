import json
import re
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

# -----------------------------
# Evaluation Configuration
# -----------------------------

EVALUATION_DATASET_PATH = Path(
    "data/evaluation/evaluation_queries.json"
)

STRATEGIES = (
    "semantic",
    "bm25",
    "hybrid",
)


# -----------------------------
# Dataset Loading
# -----------------------------

def load_evaluation_queries() -> list[dict]:
    """
    Load evaluation questions and expected evidence.
    """

    with EVALUATION_DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# -----------------------------
# Text Normalization
# -----------------------------

def normalize_text(text: str) -> str:
    """
    Normalize text before matching evidence against chunks.
    """

    tokens = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower(),
    )

    return " ".join(tokens)


# -----------------------------
# Ground Truth Resolution
# -----------------------------

def resolve_relevant_chunk_ids(
    chunks: list[str],
    expected_evidence: list[str],
) -> set[int]:
    """
    Find which current chunks contain the expected evidence.

    Chunk IDs are resolved again for every experiment so
    ground truth remains valid when chunk size changes.
    """

    normalized_chunks = [
        normalize_text(chunk)
        for chunk in chunks
    ]

    relevant_ids: set[int] = set()

    for evidence in expected_evidence:
        normalized_evidence = normalize_text(evidence)

        exact_matches = [
            index
            for index, chunk in enumerate(normalized_chunks)
            if normalized_evidence in chunk
        ]

        if exact_matches:
            relevant_ids.update(exact_matches)
            continue

        evidence_tokens = set(
            normalized_evidence.split()
        )

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
            relevant_ids.add(best_chunk_index)

    return relevant_ids


# -----------------------------
# Strategy Execution
# -----------------------------

def run_strategy(
    strategy: str,
    query: str,
    chunks: list[str],
    top_k: int,
) -> list[dict]:
    """
    Run one retrieval strategy for a single query.
    """

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

    candidate_count = max(
        top_k * 3,
        top_k,
    )

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


# -----------------------------
# Retrieval Evaluation
# -----------------------------

def evaluate_retrieval(
    top_k: int = 3,
) -> dict:
    """
    Evaluate all retrieval strategies across the evaluation dataset.
    """

    evaluation_queries = load_evaluation_queries()
    chunks = get_all_chunks()

    strategy_results = {}

    for strategy in STRATEGIES:
        query_results = []

        total_hit = 0.0
        total_precision = 0.0
        total_recall = 0.0
        total_reciprocal_rank = 0.0

        for item in evaluation_queries:
            query = item["query"]

            relevant_ids = resolve_relevant_chunk_ids(
                chunks=chunks,
                expected_evidence=item["expected_evidence"],
            )

            if not relevant_ids:
                raise ValueError(
                    f"No relevant chunks could be resolved "
                    f"for evaluation query: {query}"
                )

            results = run_strategy(
                strategy=strategy,
                query=query,
                chunks=chunks,
                top_k=top_k,
            )

            retrieved_ids = get_retrieved_chunk_ids(
                results
            )

            hit = hit_at_k(
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
                k=top_k,
            )

            precision = precision_at_k(
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
                k=top_k,
            )

            recall = recall_at_k(
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
                k=top_k,
            )

            rr = reciprocal_rank(
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
            )

            total_hit += hit
            total_precision += precision
            total_recall += recall
            total_reciprocal_rank += rr

            query_results.append(
                {
                    "query": query,
                    "relevant_chunk_ids": sorted(
                        relevant_ids
                    ),
                    "retrieved_chunk_ids": retrieved_ids,
                    "hit_at_k": round(hit, 4),
                    "precision_at_k": round(
                        precision,
                        4,
                    ),
                    "recall_at_k": round(
                        recall,
                        4,
                    ),
                    "reciprocal_rank": round(
                        rr,
                        4,
                    ),
                }
            )

        query_count = len(evaluation_queries)

        strategy_results[strategy] = {
            "average_hit_at_k": round(
                total_hit / query_count,
                4,
            ),
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