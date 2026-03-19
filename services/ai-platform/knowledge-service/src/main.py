"""Knowledge Service — RAG document ingestion, embedding, and semantic search."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.settings import settings
from src.routes import documents, search, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    yield


app = FastAPI(
    title="Benefits Knowledge Service",
    description=(
        "RAG pipeline for benefits knowledge management. Ingests documents, "
        "generates embeddings via Ollama, and provides semantic search over "
        "pgvector for context-aware AI responses."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.knowledge_service_host,
        port=settings.knowledge_service_port,
        reload=True,
    )
