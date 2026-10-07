from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,  # noqa: F401, RUF100
    Filter,  # noqa: F401, RUF100
    MatchValue,  # noqa: F401, RUF100
    PointStruct,
    VectorParams,
)

from backend.app.core.config import settings

# -----------------------------
# Qdrant Configuration
# -----------------------------

COLLECTION_NAME = "rag_documents"
PROJECT_COLLECTION_NAME = "project_documents"
VECTOR_SIZE = 384


# -----------------------------
# Qdrant Client
# -----------------------------

client = QdrantClient(
    url=settings.qdrant_url,
)


# -----------------------------
# Experiment Collection
# -----------------------------

def reset_collection() -> None:
    """
    Create a fresh collection for controlled experiments.
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
# Experiment Vector Storage
# -----------------------------

def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Store controlled experiment chunks in Qdrant.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    # experiments need a fresh collection for every configuration.
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
# Experiment Chunk Retrieval
# -----------------------------

def get_all_chunks() -> list[str]:
    """
    Read all controlled experiment chunks from Qdrant.
    """

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )

    sorted_points = sorted(
        points,
        key=lambda point: point.payload.get(
            "chunk_index",
            0,
        ),
    )

    return [
        point.payload.get("text", "")
        for point in sorted_points
    ]


# -----------------------------
# Experiment Vector Search
# -----------------------------

def search_chunks(
    query_embedding: list[float],
    top_k: int,
) -> list[dict]:
    """
    Search controlled experiment chunks.
    """

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "chunk_index": point.payload.get(
                "chunk_index"
            ),
            "text": point.payload.get("text"),
            "score": round(point.score, 4),
        }
        for point in response.points
    ]


# -----------------------------
# Project Collection Setup
# -----------------------------

def ensure_project_collection() -> None:
    """
    Create the real project document collection if it does not exist.
    """

    if client.collection_exists(
        PROJECT_COLLECTION_NAME
    ):
        return

    client.create_collection(
        collection_name=PROJECT_COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


# -----------------------------
# Project Document Storage
# -----------------------------

def store_project_document_chunks(
    project_id: int,
    document_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Store real uploaded document chunks without deleting older documents.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Each chunk must have a corresponding embedding."
        )

    ensure_project_collection()

    points = [
        PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "project_id": project_id,
                "document_id": document_id,
                "chunk_index": index,
                "text": chunk,
            },
        )
        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        )
    ]

    client.upsert(
        collection_name=PROJECT_COLLECTION_NAME,
        points=points,
    )
    
    # -----------------------------
# Project Vector Search
# -----------------------------

def search_project_chunks(
    project_id: int,
    query_embedding: list[float],
    top_k: int,
) -> list[dict]:
    """
    Search only the chunks that belong to one project.
    """

    ensure_project_collection()

    # this filter tells Qdrant to search only inside the selected project.
    project_filter = Filter(
        must=[
            FieldCondition(
                key="project_id",
                match=MatchValue(
                    value=project_id,
                ),
            )
        ]
    )

    response = client.query_points(
        collection_name=PROJECT_COLLECTION_NAME,
        query=query_embedding,
        query_filter=project_filter,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "document_id": point.payload.get(
                "document_id"
            ),
            "chunk_index": point.payload.get(
                "chunk_index"
            ),
            "text": point.payload.get("text"),
            "score": round(point.score, 4),
        }
        for point in response.points
    ]