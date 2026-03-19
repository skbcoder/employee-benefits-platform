"""pgvector CRUD operations for document storage and semantic search."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document, DocumentChunk
from src.services.chunker import chunk_document
from src.services.embedder import embedder

logger = logging.getLogger(__name__)


async def ingest_document(
    session: AsyncSession,
    title: str,
    content: str,
    category: str,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[Document, int]:
    """Ingest a document: chunk it, generate embeddings, and store in pgvector.

    Returns the created Document and the number of chunks.
    """
    # Create the document record
    doc = Document(
        title=title,
        source=source,
        category=category,
        content=content,
        metadata_=metadata or {},
    )
    session.add(doc)
    await session.flush()  # Get the document_id

    # Chunk the document
    chunks = chunk_document(content)
    logger.info(f"Document '{title}' split into {len(chunks)} chunks")

    # Generate embeddings and create chunk records
    for chunk in chunks:
        try:
            embedding = await embedder.embed(chunk.content)
        except Exception as e:
            logger.warning(f"Embedding failed for chunk {chunk.index}: {e}")
            embedding = None

        chunk_entity = DocumentChunk(
            document_id=doc.document_id,
            chunk_index=chunk.index,
            content=chunk.content,
            token_count=chunk.token_count,
            embedding=embedding,
        )
        session.add(chunk_entity)

    await session.commit()
    await session.refresh(doc)

    return doc, len(chunks)


async def search_similar(
    session: AsyncSession,
    query: str,
    category: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Perform semantic search using cosine similarity.

    Returns a list of matching chunks with metadata.
    """
    # Generate query embedding
    query_embedding = await embedder.embed(query)

    # Build the query using pgvector cosine distance operator
    # cosine_distance = 1 - cosine_similarity, so we order ascending
    distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)

    stmt = (
        select(
            DocumentChunk.chunk_id,
            DocumentChunk.document_id,
            DocumentChunk.content,
            Document.title.label("document_title"),
            Document.category,
            (1 - distance_expr).label("similarity"),
        )
        .join(Document, DocumentChunk.document_id == Document.document_id)
        .where(DocumentChunk.embedding.isnot(None))
    )

    if category:
        stmt = stmt.where(Document.category == category)

    stmt = stmt.order_by(distance_expr).limit(top_k)

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "chunk_id": str(row.chunk_id),
            "document_id": str(row.document_id),
            "document_title": row.document_title,
            "category": row.category,
            "content": row.content,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]


async def list_documents(session: AsyncSession) -> list[dict[str, Any]]:
    """List all documents with chunk counts."""
    stmt = (
        select(
            Document,
            func.count(DocumentChunk.chunk_id).label("chunk_count"),
        )
        .outerjoin(DocumentChunk, Document.document_id == DocumentChunk.document_id)
        .group_by(Document.document_id)
        .order_by(Document.created_at.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "document_id": str(row.Document.document_id),
            "title": row.Document.title,
            "source": row.Document.source,
            "category": row.Document.category,
            "chunk_count": row.chunk_count,
            "metadata": row.Document.metadata_,
            "created_at": row.Document.created_at,
            "updated_at": row.Document.updated_at,
        }
        for row in rows
    ]


async def get_document(session: AsyncSession, document_id: UUID) -> dict[str, Any] | None:
    """Get a document by ID with chunk count."""
    stmt = (
        select(
            Document,
            func.count(DocumentChunk.chunk_id).label("chunk_count"),
        )
        .outerjoin(DocumentChunk, Document.document_id == DocumentChunk.document_id)
        .where(Document.document_id == document_id)
        .group_by(Document.document_id)
    )

    result = await session.execute(stmt)
    row = result.first()

    if not row:
        return None

    return {
        "document_id": str(row.Document.document_id),
        "title": row.Document.title,
        "source": row.Document.source,
        "category": row.Document.category,
        "content": row.Document.content,
        "chunk_count": row.chunk_count,
        "metadata": row.Document.metadata_,
        "created_at": row.Document.created_at,
        "updated_at": row.Document.updated_at,
    }


async def delete_document(session: AsyncSession, document_id: UUID) -> bool:
    """Delete a document and all its chunks (cascading)."""
    stmt = delete(Document).where(Document.document_id == document_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def list_categories(session: AsyncSession) -> list[str]:
    """List all distinct knowledge categories."""
    stmt = select(Document.category).distinct().order_by(Document.category)
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]
