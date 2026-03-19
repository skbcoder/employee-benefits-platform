"""AI Gateway — orchestrates Ollama, MCP tools, and RAG for benefits AI."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.settings import settings
from src.services.mcp_client import mcp_client
from src.services.rag_client import rag_client
from src.routes import chat, agents, health, tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    yield
    await mcp_client.close()
    await rag_client.close()


app = FastAPI(
    title="Benefits AI Gateway",
    description=(
        "AI Gateway that orchestrates Ollama (local LLM), MCP tools, and RAG "
        "knowledge base for intelligent benefits enrollment management."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(health.router)
app.include_router(tools.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.ai_gateway_host,
        port=settings.ai_gateway_port,
        reload=True,
    )
