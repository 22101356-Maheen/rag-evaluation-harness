import re

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
) -> list[dict]:
    """
    Rank document chunks using BM25 keyword relevance.
    """

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if not chunks:
        return []

    tokenized_chunks = [
        tokenize_text(chunk)
        for chunk in chunks
    ]

    bm25 = BM25Okapi(tokenized_chunks)

    tokenized_query = tokenize_text(query)
    scores = bm25.get_scores(tokenized_query)

    results = [
        {
            "chunk_index": index,
            "text": chunk,
            "score": round(float(scores[index]), 4),
        }
        for index, chunk in enumerate(chunks)
    ]

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]