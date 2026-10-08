from functools import lru_cache
from typing import Any


# -----------------------------
# Embedding Model Configuration
# -----------------------------

MODEL_NAME = "all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    """Load the embedding model only when an embedding is requested."""

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


# -----------------------------
# Document Embeddings
# -----------------------------

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple text chunks into vector embeddings.
    """

    embeddings = get_embedding_model().encode(
        texts,
        convert_to_numpy=True,
    )

    return embeddings.tolist()


# -----------------------------
# Query Embedding
# -----------------------------

def embed_query(query: str) -> list[float]:
    """
    Convert a user query into a vector using the same embedding model.
    """

    embedding = get_embedding_model().encode(
        query,
        convert_to_numpy=True,
    )

    return embedding.tolist()
