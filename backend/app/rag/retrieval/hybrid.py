from collections.abc import Hashable


# -----------------------------
# Reciprocal Rank Fusion
# -----------------------------

def reciprocal_rank_fusion(
    semantic_results: list[dict],
    bm25_results: list[dict],
    top_k: int = 3,
    rank_constant: int = 60,
) -> list[dict]:
    """
    Combine semantic and BM25 rankings using Reciprocal Rank Fusion.
    """

    fused_results: dict[Hashable, dict] = {}

    ranked_sources = [
        ("semantic", semantic_results),
        ("bm25", bm25_results),
    ]

    for source_name, results in ranked_sources:
        for rank, result in enumerate(results, start=1):
            chunk_id = result.get(
                "chunk_id",
                result["chunk_index"],
            )

            if chunk_id not in fused_results:
                fused_result = {
                    "chunk_index": result["chunk_index"],
                    "text": result["text"],
                    "hybrid_score": 0.0,
                    "matched_by": [],
                }

                if "chunk_id" in result:
                    fused_result["chunk_id"] = result["chunk_id"]

                if "document_id" in result:
                    fused_result["document_id"] = result["document_id"]

                fused_results[chunk_id] = fused_result

            fused_results[chunk_id]["hybrid_score"] += (
                1 / (rank_constant + rank)
            )

            fused_results[chunk_id]["matched_by"].append(
                source_name
            )

    combined_results = list(fused_results.values())

    combined_results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    for result in combined_results:
        result["hybrid_score"] = round(
            result["hybrid_score"],
            6,
        )

    return combined_results[:top_k]
