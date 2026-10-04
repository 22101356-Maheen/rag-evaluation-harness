from sentence_transformers import SentenceTransformer  # noqa: I001


# -----------------------------
# Embedding Model Configuration
# -----------------------------

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


# -----------------------------
# Document Embeddings
# -----------------------------

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple text chunks into vector embeddings.
    """

    embeddings = model.encode(
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

    embedding = model.encode(
        query,
        convert_to_numpy=True,
    )

    return embedding.tolist()