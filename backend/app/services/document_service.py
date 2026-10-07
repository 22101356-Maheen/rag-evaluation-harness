from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.document import Document


# -----------------------------
# Document Creation
# -----------------------------

def create_document(
    db: Session,
    project_id: int,
    filename: str,
) -> Document:
    """
    Create a document record before RAG processing starts.
    """

    # this saves the document information in PostgreSQL.
    document = Document(
        project_id=project_id,
        filename=filename,
        status="processing",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


# -----------------------------
# Document Status Update
# -----------------------------

def update_document_status(
    db: Session,
    document: Document,
    status: str,
) -> Document:
    """
    Update the processing state of a document.
    """

    # this changes the document status after processing.
    document.status = status

    db.commit()
    db.refresh(document)

    return document


# -----------------------------
# Project Document Listing
# -----------------------------

def get_project_documents(
    db: Session,
    project_id: int,
) -> list[Document]:
    """
    Return all documents that belong to one project.
    """

    # this selects only documents connected to the given project.
    statement = select(Document).where(
        Document.project_id == project_id
    )

    documents = db.scalars(statement).all()

    return list(documents)


# -----------------------------
# Duplicate Document Check
# -----------------------------

def get_document_by_filename(
    db: Session,
    project_id: int,
    filename: str,
) -> Document | None:
    """
    Find a document with the same filename inside one project.
    """

    # this checks whether the same filename already exists in the project.
    statement = select(Document).where(
        Document.project_id == project_id,
        Document.filename == filename,
    )

    return db.scalars(statement).first()