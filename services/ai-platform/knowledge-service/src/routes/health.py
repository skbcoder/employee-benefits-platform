"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.services.embedder import embedder

router = APIRouter(prefix="/api/knowledge", tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    """Health check including pgvector and Ollama embedding model status."""
    # Check database + pgvector
    db_ok = False
    pgvector_ok = False
    try:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar() == 1

        result = await session.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        row = result.first()
        pgvector_ok = row is not None
    except Exception:
        pass

    # Check embedding model
    embedder_ok = await embedder.is_healthy()

    all_ok = db_ok and pgvector_ok and embedder_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "service": "knowledge-service",
        "dependencies": {
            "database": "ok" if db_ok else "unavailable",
            "pgvector": "ok" if pgvector_ok else "unavailable",
            "ollama_embedder": "ok" if embedder_ok else "unavailable",
        },
    }


@router.get("/categories")
async def categories(session: AsyncSession = Depends(get_session)):
    """List all knowledge categories."""
    from src.services.vector_store import list_categories

    cats = await list_categories(session)
    return {"categories": cats}
