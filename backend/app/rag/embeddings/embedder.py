from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
    )

    return embeddings.tolist()