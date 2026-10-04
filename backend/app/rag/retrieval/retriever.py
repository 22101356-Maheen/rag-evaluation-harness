from backend.app.rag.retrieval.similarity import cosine_similarity
from backend.app.rag.embeddings.embedder import embed_query


# -----------------------------
# Top-K Semantic Retrieval
# -----------------------------

def retrieve_top_k(
    query: str,
    chunks: list[str],
    chunk_embeddings: list[list[float]],
    top_k: int = 3,
) -> list[dict]:
    """
    Return the most relevant chunks for a user query.
    """

    if len(chunks) != len(chunk_embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    # Convert the user's question into the same vector space.
    query_embedding = embed_query(query)

    scored_chunks = []

    # Compare the query with every available chunk.
    for index, (chunk, chunk_embedding) in enumerate(
        zip(chunks, chunk_embeddings)
    ):
        score = cosine_similarity(
            query_embedding,
            chunk_embedding,
        )

        scored_chunks.append(
            {
                "chunk_index": index,
                "text": chunk,
                "score": round(score, 4),
            }
        )

    # Highest similarity scores should appear first.
    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_chunks[:top_k]