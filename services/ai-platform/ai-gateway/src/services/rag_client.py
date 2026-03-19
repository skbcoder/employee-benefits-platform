"""Client for the Knowledge Service (RAG context retrieval)."""

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class RAGClient:
    """Queries the Knowledge Service for relevant context."""

    def __init__(self) -> None:
        self._base_url = settings.knowledge_service_url.rstrip("/")
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def search(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Perform semantic search and return relevant document chunks."""
        client = await self._client()
        payload: dict[str, Any] = {"query": query, "top_k": top_k}
        if category:
            payload["category"] = category

        try:
            resp = await client.post(
                f"{self._base_url}/api/knowledge/search",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"Knowledge Service search failed: {e}")
            return []

    async def is_healthy(self) -> bool:
        """Check if the Knowledge Service is reachable."""
        client = await self._client()
        try:
            resp = await client.get(f"{self._base_url}/api/knowledge/health")
            return resp.status_code == 200
        except Exception:
            return False


rag_client = RAGClient()
