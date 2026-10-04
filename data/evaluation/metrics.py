# -----------------------------
# Retrieval Evaluation Helpers
# -----------------------------

def get_retrieved_chunk_ids(
    results: list[dict],
) -> list[int]:
    """
    Extract chunk indexes from retriever results.
    """

    return [
        result["chunk_index"]
        for result in results
    ]


# -----------------------------
# Hit Rate
# -----------------------------

def hit_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
    k: int,
) -> float:
    """
    Return 1.0 if at least one relevant chunk appears
    in the first K results, otherwise 0.0.
    """

    top_k = retrieved_ids[:k]

    return float(
        any(
            chunk_id in relevant_ids
            for chunk_id in top_k
        )
    )


# -----------------------------
# Precision
# -----------------------------

def precision_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
    k: int,
) -> float:
    """
    Measure how many of the first K retrieved chunks are relevant.
    """

    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        chunk_id in relevant_ids
        for chunk_id in top_k
    )

    return relevant_count / len(top_k)


# -----------------------------
# Recall
# -----------------------------

def recall_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
    k: int,
) -> float:
    """
    Measure how many known relevant chunks appear
    in the first K retrieved results.
    """

    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]

    relevant_found = sum(
        chunk_id in relevant_ids
        for chunk_id in top_k
    )

    return relevant_found / len(relevant_ids)


# -----------------------------
# Reciprocal Rank
# -----------------------------

def reciprocal_rank(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:
    """
    Score how early the first relevant chunk appears.
    """

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant_ids:
            return 1 / rank

    return 0.0