def chunk_text(
    text: str,
    chunk_size: int = 120,
    overlap: int = 20,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks