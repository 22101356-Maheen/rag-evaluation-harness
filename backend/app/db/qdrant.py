from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from backend.app.core.config import settings


# -----------------------------
# Qdrant Configuration
# -----------------------------

COLLECTION_NAME = "rag_documents"
VECTOR_SIZE = 384


# -----------------------------
# Qdrant Client
# -----------------------------

client = QdrantClient(url=settings.qdrant_url)


# -----------------------------
# Collection Management
# -----------------------------

def reset_collection() -> None:
    """
    Create a fresh Qdrant collection for the uploaded corpus.
    """

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


# -----------------------------
# Vector Storage
# -----------------------------

def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Store document chunks and embeddings in Qdrant.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    reset_collection()

    points = [
        PointStruct(
            id=index,
            vector=embedding,
            payload={
                "chunk_index": index,
                "text": chunk,
            },
        )
        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        )
    ]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )


# -----------------------------
# Vector Search
# -----------------------------

def search_chunks(
    query_embedding: list[float],
    top_k: int,
) -> list[dict]:
    """
    Search Qdrant for chunks closest to the query vector.
    """

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "chunk_index": point.payload.get("chunk_index"),
            "text": point.payload.get("text"),
            "score": round(point.score, 4),
        }
        for point in response.points
    ]