from fastapi import APIRouter, HTTPException

from backend.app.db.qdrant import COLLECTION_NAME, client, search_chunks
from backend.app.rag.embeddings.embedder import embed_query
from backend.app.schemas.search import SearchRequest

router = APIRouter()


# -----------------------------
# Semantic Search
# -----------------------------

@router.post("/search")
def search_document(request: SearchRequest):
    """
    Search stored document vectors using semantic similarity.
    """

    if not client.collection_exists(COLLECTION_NAME):
        raise HTTPException(
            status_code=400,
            detail="Upload a document before searching",
        )

    query_embedding = embed_query(request.query)

    results = search_chunks(
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "results": results,
    }