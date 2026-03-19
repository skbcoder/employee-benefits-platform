"""Semantic search endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models.schemas import SearchRequest, SearchResponse, SearchResult
from src.services.vector_store import search_similar

router = APIRouter(prefix="/api/knowledge", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """Perform semantic search across the knowledge base.

    Returns the most relevant document chunks ranked by cosine similarity.
    """
    results = await search_similar(
        session=session,
        query=request.query,
        category=request.category,
        top_k=request.top_k,
    )

    return SearchResponse(
        query=request.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )
