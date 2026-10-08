from collections.abc import Hashable

from backend.app.rag.embeddings.embedder import embed_query
from backend.app.rag.retrieval.similarity import cosine_similarity


# -----------------------------
# Top-K Semantic Retrieval
# -----------------------------

def retrieve_top_k(
    query: str,
    chunks: list[str],
    chunk_embeddings: list[list[float]],
    top_k: int = 3,
    chunk_ids: list[Hashable] | None = None,
    chunk_metadata: list[dict] | None = None,
) -> list[dict]:
    """
    Return the most relevant chunks for a user query.
    """

    if len(chunks) != len(chunk_embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    if chunk_ids is not None and len(chunks) != len(chunk_ids):
        raise ValueError("Each chunk must have a corresponding chunk ID.")

    if chunk_metadata is not None and len(chunks) != len(chunk_metadata):
        raise ValueError("Each chunk must have corresponding metadata.")

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

        result = {
            "chunk_index": index,
            "text": chunk,
            "score": round(score, 4),
        }

        if chunk_ids is not None:
            result["chunk_id"] = chunk_ids[index]

        if chunk_metadata is not None:
            result.update(chunk_metadata[index])

        scored_chunks.append(result)

    # Highest similarity scores should appear first.
    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_chunks[:top_k]
