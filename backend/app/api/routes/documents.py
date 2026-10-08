from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_user_id
from backend.app.db.postgres import get_db
from backend.app.db.qdrant import (
    store_chunks,
    store_project_document_chunks,
)
from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.rag.embeddings.embedder import embed_texts
from backend.app.rag.ingestion.text_loader import load_text_file
from backend.app.schemas.document import DocumentResponse
from backend.app.services.document_service import (
    create_document,
    get_document_by_filename,
    get_project_documents,
    update_document_status,
)
from backend.app.services.project_service import get_owned_project_by_id

router = APIRouter()


# -----------------------------
# Legacy Test Upload
# -----------------------------

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
):
    """
    Process a text document using the original test flow.
    """

    if not file.filename or not file.filename.endswith(
        ".txt"
    ):
        raise HTTPException(
            status_code=400,
            detail="For now, only .txt files are supported",
        )

    content = await file.read()
    text = load_text_file(content)

    chunks = chunk_text(
        text=text,
        chunk_size=120,
        overlap=20,
    )

    embeddings = embed_texts(chunks)

    store_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    return {
        "filename": file.filename,
        "characters": len(text),
        "chunk_count": len(chunks),
        "embedding_count": len(embeddings),
        "embedding_dimensions": (
            len(embeddings[0])
            if embeddings
            else 0
        ),
        "storage": "qdrant",
    }


# -----------------------------
# Project Document Upload
# -----------------------------

@router.post(
    "/projects/{project_id}/documents/upload",
    response_model=DocumentResponse,
)
async def upload_project_document(
    project_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),  # noqa: B008
    owner_id: str = Depends(get_current_user_id),
):
    """
    Upload a document only to a project owned by the current user.
    """

    # this checks project ownership.
    project = get_owned_project_by_id(
        db=db,
        project_id=project_id,
        owner_id=owner_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if not file.filename or not file.filename.endswith(
        ".txt"
    ):
        raise HTTPException(
            status_code=400,
            detail="For now, only .txt files are supported",
        )

    existing_document = get_document_by_filename(
        db=db,
        project_id=project_id,
        filename=file.filename,
    )

    if existing_document is not None:
        raise HTTPException(
            status_code=409,
            detail="Document already exists in this project",
        )

    document = create_document(
        db=db,
        project_id=project_id,
        filename=file.filename,
    )

    try:
        content = await file.read()
        text = load_text_file(content)

        chunks = chunk_text(
            text=text,
            chunk_size=120,
            overlap=20,
        )

        embeddings = embed_texts(chunks)

        store_project_document_chunks(
            project_id=project_id,
            document_id=document.id,
            chunks=chunks,
            embeddings=embeddings,
        )

        update_document_status(
            db=db,
            document=document,
            status="ready",
        )

    except Exception:
        update_document_status(
            db=db,
            document=document,
            status="failed",
        )

        raise

    return document


# -----------------------------
# Project Document Listing
# -----------------------------

@router.get(
    "/projects/{project_id}/documents",
    response_model=list[DocumentResponse],
)
def list_project_documents(
    project_id: int,
    db: Session = Depends(get_db),  # noqa: B008
    owner_id: str = Depends(get_current_user_id),
):
    """
    Return documents only from a project owned by the current user.
    """

    # this checks project ownership first.
    project = get_owned_project_by_id(
        db=db,
        project_id=project_id,
        owner_id=owner_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return get_project_documents(
        db=db,
        project_id=project_id,
    )