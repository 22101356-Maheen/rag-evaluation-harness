import json
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
    Load evaluation questions and their known relevant chunk IDs.
    """

    with EVALUATION_DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


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

            relevant_ids = set(
                item["relevant_chunk_ids"]
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