from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.postgres import get_db
from backend.app.db.qdrant import (
    COLLECTION_NAME,
    client,
    get_all_chunks,
    search_chunks,
    search_project_chunks,
)
from backend.app.rag.embeddings.embedder import embed_query
from backend.app.rag.retrieval.bm25 import retrieve_bm25
from backend.app.rag.retrieval.hybrid import reciprocal_rank_fusion
from backend.app.schemas.project_search import ProjectSearchRequest
from backend.app.schemas.search import SearchRequest
from backend.app.services.project_service import get_project_by_id


router = APIRouter()


# -----------------------------
# Search Endpoint
# -----------------------------

@router.post("/search")
def search_document(request: SearchRequest):
    """
    Search controlled experiment chunks.
    """

    if not client.collection_exists(COLLECTION_NAME):
        raise HTTPException(
            status_code=400,
            detail="No Qdrant collection found. Upload a document first.",
        )

    chunks = get_all_chunks()

    if request.strategy == "bm25":
        results = retrieve_bm25(
            query=request.query,
            chunks=chunks,
            top_k=request.top_k,
        )

    elif request.strategy == "hybrid":
        candidate_count = max(
            request.top_k * 3,
            request.top_k,
        )

        query_embedding = embed_query(request.query)

        semantic_results = search_chunks(
            query_embedding=query_embedding,
            top_k=candidate_count,
        )

        bm25_results = retrieve_bm25(
            query=request.query,
            chunks=chunks,
            top_k=candidate_count,
        )

        results = reciprocal_rank_fusion(
            semantic_results=semantic_results,
            bm25_results=bm25_results,
            top_k=request.top_k,
        )

    else:
        query_embedding = embed_query(request.query)

        results = search_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )

    return {
        "query": request.query,
        "strategy": request.strategy,
        "results": results,
    }


# -----------------------------
# Project Search
# -----------------------------

@router.post("/projects/{project_id}/search")
def search_project(
    project_id: int,
    request: ProjectSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Search only the uploaded chunks that belong to one project.
    """

    # this makes sure the requested project exists.
    project = get_project_by_id(
        db=db,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # this converts the user's question into a vector.
    query_embedding = embed_query(
        request.query
    )

    # this searches only the current project's chunks in Qdrant.
    results = search_project_chunks(
        project_id=project_id,
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    return {
        "project_id": project_id,
        "project_name": project.name,
        "query": request.query,
        "results": results,
    }