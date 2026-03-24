"""AI Gateway — orchestrates Ollama, MCP tools, and RAG for benefits AI."""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response

from config.settings import settings
from src.services.mcp_client import mcp_client
from src.services.rag_client import rag_client
from src.routes import chat, agents, health, tools

# Observability — shared module (load via spec to avoid src/ namespace conflict)
_observability_available = False
try:
    import importlib.util
    _obs_base = Path(__file__).parent.parent.parent / "observability"
    _spec = importlib.util.spec_from_file_location(
        "obs_metrics", _obs_base / "src" / "metrics" / "collector.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    MetricsMiddleware = _mod.MetricsMiddleware
    metrics_endpoint = _mod.metrics_endpoint
    _observability_available = True
except Exception:
    import logging
    logging.getLogger(__name__).warning("Observability module not available — metrics disabled")


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

if _observability_available:
    app.add_middleware(MetricsMiddleware, service_name="ai-gateway")

app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(health.router)
app.include_router(tools.router)


@app.get("/metrics")
async def metrics():
    if _observability_available:
        return Response(content=metrics_endpoint(), media_type="text/plain")
    return Response(content="# Observability not available\n", media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.ai_gateway_host,
        port=settings.ai_gateway_port,
        reload=True,
    )
