"""MCP tool listing and execution endpoints."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.mcp_client import mcp_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["tools"])


@router.get("/tools")
async def list_tools():
    """Return all available MCP tool definitions."""
    definitions = mcp_client.get_tool_definitions()
    tools = []
    for defn in definitions:
        fn = defn.get("function", {})
        tools.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters", {}),
        })
    return {"tools": tools}


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict


@router.post("/tools/execute")
async def execute_tool(request: ToolExecuteRequest):
    """Execute an MCP tool with the given arguments and return the result."""
    logger.info(f"Tool execute request: {request.name}")
    result = await mcp_client.execute_tool(request.name, request.arguments)
    return {"tool": request.name, "result": result}
