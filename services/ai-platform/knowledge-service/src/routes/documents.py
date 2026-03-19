"""Document CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models.schemas import (
    DocumentCreate,
    DocumentDetailResponse,
    DocumentResponse,
)
from src.services.vector_store import (
    delete_document,
    get_document,
    ingest_document,
    list_documents,
)

router = APIRouter(prefix="/api/knowledge/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    request: DocumentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Ingest a new document into the knowledge base.

    The document will be chunked, embedded, and stored for semantic search.
    """
    doc, chunk_count = await ingest_document(
        session=session,
        title=request.title,
        content=request.content,
        category=request.category,
        source=request.source,
        metadata=request.metadata,
    )

    return DocumentResponse(
        document_id=str(doc.document_id),
        title=doc.title,
        source=doc.source,
        category=doc.category,
        chunk_count=chunk_count,
        metadata=doc.metadata_ or {},
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("", response_model=list[DocumentResponse])
async def get_documents(session: AsyncSession = Depends(get_session)):
    """List all documents in the knowledge base."""
    docs = await list_documents(session)
    return [DocumentResponse(**doc) for doc in docs]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get document details including content."""
    doc = await get_document(session, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetailResponse(**doc)


@router.delete("/{document_id}")
async def remove_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a document and all its chunks."""
    deleted = await delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "document_id": str(document_id)}
