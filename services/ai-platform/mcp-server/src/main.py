"""MCP Server — wraps Employee Benefits Platform APIs as MCP tools."""

import sys
import os

# Add the mcp-server directory to the path so config/ and src/ are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from config.settings import settings
from src.benefits_client import benefits_client
from src.tools import register_tools
from src.resources import register_resources
from src.prompts import register_prompts

# ── MCP Server Setup ────────────────────────────────────────────────

mcp_server = Server("benefits-mcp-server")

register_tools(mcp_server)
register_resources(mcp_server)
register_prompts(mcp_server)

# ── SSE Transport ───────────────────────────────────────────────────

sse_transport = SseServerTransport("/mcp/messages/")


async def handle_sse(request):
    """Handle SSE connection for MCP clients."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


# ── FastAPI Application ─────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    yield
    await benefits_client.close()


app = FastAPI(
    title="Benefits MCP Server",
    description="MCP Server exposing Employee Benefits Platform APIs as tools for AI agents.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-server"}


# Mount SSE transport routes
app.routes.append(Route("/mcp/sse", endpoint=handle_sse))
app.routes.append(Mount("/mcp/messages/", app=sse_transport.handle_post_message))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=True,
    )
