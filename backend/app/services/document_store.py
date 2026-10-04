# -----------------------------
# Temporary In-Memory Storage
# -----------------------------

_document_chunks: list[str] = []
_document_embeddings: list[list[float]] = []


# -----------------------------
# Save Processed Document
# -----------------------------

def save_document(
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Store document chunks and embeddings in memory.
    """

    _document_chunks.clear()
    _document_chunks.extend(chunks)

    _document_embeddings.clear()
    _document_embeddings.extend(embeddings)


# -----------------------------
# Read Stored Document
# -----------------------------

def get_document() -> tuple[list[str], list[list[float]]]:
    """
    Return the currently stored chunks and embeddings.
    """

    return _document_chunks, _document_embeddings


# -----------------------------
# Storage Status
# -----------------------------

def has_document() -> bool:
    """
    Check whether a processed document is currently available.
    """

    return bool(_document_chunks and _document_embeddings)