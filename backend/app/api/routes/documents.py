from fastapi import APIRouter, HTTPException, UploadFile

from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.rag.embeddings.embedder import embed_texts
from backend.app.rag.ingestion.text_loader import load_text_file

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(file: UploadFile):
    if not file.filename or not file.filename.endswith(".txt"):
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

    return {
        "filename": file.filename,
        "characters": len(text),
        "chunk_count": len(chunks),
        "embedding_count": len(embeddings),
        "embedding_dimensions": len(embeddings[0]) if embeddings else 0,
        "first_chunk": chunks[0] if chunks else "",
    }