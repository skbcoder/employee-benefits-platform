"""Client for invoking MCP tools on the MCP Server."""

import json
import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

# Tool definitions in Ollama tool format (derived from MCP tool schemas)
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "submit_enrollment",
            "description": (
                "Submit a new employee benefits enrollment. Requires employeeId, "
                "employeeName, employeeEmail, and a list of benefit selections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeId": {"type": "string", "description": "Employee ID (e.g. E12345)"},
                    "employeeName": {"type": "string", "description": "Full name of the employee"},
                    "employeeEmail": {"type": "string", "description": "Employee email address"},
                    "selections": {
                        "type": "array",
                        "description": "Benefit selections",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["medical", "dental", "vision", "life"]},
                                "plan": {"type": "string"},
                            },
                            "required": ["type", "plan"],
                        },
                    },
                },
                "required": ["employeeId", "employeeName", "employeeEmail", "selections"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enrollment",
            "description": "Retrieve an enrollment record by its enrollment ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enrollmentId": {"type": "string", "description": "The enrollment UUID"},
                },
                "required": ["enrollmentId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enrollment_by_employee",
            "description": "Retrieve the most recent enrollment for an employee by their employee ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeId": {"type": "string", "description": "Employee ID (e.g. E12345)"},
                },
                "required": ["employeeId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enrollment_by_name",
            "description": "Retrieve the most recent enrollment for an employee by their name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeName": {"type": "string", "description": "Full name of the employee"},
                },
                "required": ["employeeName"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_enrollments_by_status",
            "description": "List all enrollments with a given status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["SUBMITTED", "PROCESSING", "COMPLETED", "DISPATCH_FAILED"],
                    },
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_processing_details",
            "description": "Get the processing record for an enrollment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enrollmentId": {"type": "string", "description": "The enrollment UUID"},
                },
                "required": ["enrollmentId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_enrollment_status",
            "description": "Get full enrollment status including enrollment and processing details with effective status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enrollmentId": {"type": "string", "description": "The enrollment UUID"},
                },
                "required": ["enrollmentId"],
            },
        },
    },
]


_UUID_FIELDS = {"enrollmentId", "id", "processedEnrollmentId"}


def _strip_internal_ids(data: Any) -> Any:
    """Remove internal UUID fields from tool results so the LLM doesn't display them."""
    if isinstance(data, dict):
        return {k: _strip_internal_ids(v) for k, v in data.items() if k not in _UUID_FIELDS}
    if isinstance(data, list):
        return [_strip_internal_ids(item) for item in data]
    return data


class MCPClient:
    """Executes MCP tools by calling the benefits platform APIs directly.

    Rather than going through the MCP SSE transport for server-to-server calls,
    this client calls the benefits APIs directly (same logic as the MCP Server).
    This avoids the overhead of SSE for internal gateway-to-API communication.
    """

    def __init__(self) -> None:
        self._enrollment_url = settings.mcp_server_url.rstrip("/")
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute an MCP tool and return the result as a JSON string."""
        from src.services._benefits_proxy import execute_benefits_tool

        try:
            result = await execute_benefits_tool(name, arguments)
            result = _strip_internal_ids(result)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Tool execution failed: {name} - {e}")
            return json.dumps({"error": str(e)})

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in Ollama-compatible format."""
        return TOOL_DEFINITIONS


mcp_client = MCPClient()
