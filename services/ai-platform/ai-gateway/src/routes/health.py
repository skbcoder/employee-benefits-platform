"""Health check endpoints."""

from fastapi import APIRouter

from src.services.ollama_client import ollama_client
from src.services.rag_client import rag_client

router = APIRouter(prefix="/api/ai", tags=["health"])


@router.get("/health")
async def health():
    """Health check including Ollama and Knowledge Service connectivity."""
    ollama_ok = await ollama_client.is_healthy()
    knowledge_ok = await rag_client.is_healthy()

    return {
        "status": "ok" if ollama_ok else "degraded",
        "service": "ai-gateway",
        "dependencies": {
            "ollama": "ok" if ollama_ok else "unavailable",
            "knowledge_service": "ok" if knowledge_ok else "unavailable",
        },
    }
