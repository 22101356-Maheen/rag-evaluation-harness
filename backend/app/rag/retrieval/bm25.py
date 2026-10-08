import re
from collections.abc import Hashable

from rank_bm25 import BM25Okapi


# -----------------------------
# Tokenization Configuration
# -----------------------------

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


# -----------------------------
# Text Tokenization
# -----------------------------

def tokenize_text(text: str) -> list[str]:
    """
    Normalize text into useful lowercase tokens for BM25 retrieval.
    """

    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return [
        token
        for token in tokens
        if token not in STOP_WORDS
    ]


# -----------------------------
# BM25 Retrieval
# -----------------------------

def retrieve_bm25(
    query: str,
    chunks: list[str],
    top_k: int = 3,
    chunk_ids: list[Hashable] | None = None,
    chunk_metadata: list[dict] | None = None,
) -> list[dict]:
    """
    Rank document chunks using BM25 keyword relevance.
    """

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if not chunks:
        return []

    if chunk_ids is not None and len(chunks) != len(chunk_ids):
        raise ValueError("Each chunk must have a corresponding chunk ID.")

    if chunk_metadata is not None and len(chunks) != len(chunk_metadata):
        raise ValueError("Each chunk must have corresponding metadata.")

    tokenized_chunks = [
        tokenize_text(chunk)
        for chunk in chunks
    ]

    bm25 = BM25Okapi(tokenized_chunks)

    tokenized_query = tokenize_text(query)
    scores = bm25.get_scores(tokenized_query)

    results = []

    for index, chunk in enumerate(chunks):
        result = {
            "chunk_index": index,
            "text": chunk,
            "score": round(float(scores[index]), 4),
        }

        if chunk_ids is not None:
            result["chunk_id"] = chunk_ids[index]

        if chunk_metadata is not None:
            result.update(chunk_metadata[index])

        results.append(result)

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]
