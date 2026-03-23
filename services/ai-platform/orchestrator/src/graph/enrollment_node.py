"""Enrollment agent node — handles enrollment CRUD operations via MCP tools."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from config.settings import settings
from src.models.state import AgentResult, AgentType, ToolCall
from src.graph.state import AgentState
from src.providers.provider_factory import get_provider

logger = logging.getLogger(__name__)

_ENROLLMENT_SYSTEM_PROMPT = (
    "You are the enrollment specialist agent. You handle all enrollment "
    "operations: submitting new enrollments, checking status, listing "
    "enrollments by employee or status.\n\n"
    "RULES:\n"
    "1. Never fabricate enrollment IDs or employee IDs. Ask the user if not provided.\n"
    "2. Use check_enrollment_status for the most complete status picture.\n"
    "3. Available benefit types: medical, dental, vision, life\n"
    "4. Enrollment statuses: SUBMITTED, PROCESSING, COMPLETED, DISPATCH_FAILED\n"
    "5. Be concise and present results in Markdown tables when listing multiple items.\n"
    "6. Never display enrollment UUIDs — show Employee Name, ID, Status, and Plan."
)

# MCP tools available to this agent (fetched from MCP server or hardcoded)
_ENROLLMENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "submit_enrollment",
            "description": "Submit a new benefits enrollment for an employee",
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeId": {"type": "string", "description": "Employee ID"},
                    "employeeName": {"type": "string", "description": "Employee full name"},
                    "employeeEmail": {"type": "string", "description": "Employee email"},
                    "selections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["medical", "dental", "vision", "life"]},
                                "plan": {"type": "string"},
                            },
                        },
                        "description": "Benefit selections",
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
            "description": "Get enrollment details by enrollment ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "enrollmentId": {"type": "string", "description": "Enrollment UUID"},
                },
                "required": ["enrollmentId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_enrollments_by_employee_id",
            "description": "List all enrollments for an employee by their employee ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeId": {"type": "string", "description": "Employee ID"},
                },
                "required": ["employeeId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_enrollments_by_employee_name",
            "description": "Search enrollments by employee name (partial match supported)",
            "parameters": {
                "type": "object",
                "properties": {
                    "employeeName": {"type": "string", "description": "Employee name to search"},
                },
                "required": ["employeeName"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_enrollments_by_status",
            "description": "List all enrollments with a specific status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["SUBMITTED", "PROCESSING", "COMPLETED", "DISPATCH_FAILED"],
                        "description": "Enrollment status to filter by",
                    },
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_enrollment_status",
            "description": "Get comprehensive enrollment status including processing details",
            "parameters": {
                "type": "object",
                "properties": {
                    "enrollmentId": {"type": "string", "description": "Enrollment UUID"},
                },
                "required": ["enrollmentId"],
            },
        },
    },
]

# Map tool names to API endpoints
_TOOL_ENDPOINTS: dict[str, tuple[str, str]] = {
    "submit_enrollment": ("POST", "/api/enrollments"),
    "get_enrollment": ("GET", "/api/enrollments/{enrollmentId}"),
    "list_enrollments_by_employee_id": ("GET", "/api/enrollments/employee/{employeeId}"),
    "list_enrollments_by_employee_name": ("GET", "/api/enrollments/search?name={employeeName}"),
    "list_enrollments_by_status": ("GET", "/api/enrollments/status/{status}"),
    "check_enrollment_status": ("GET", "/api/enrollments/{enrollmentId}/status"),
}


async def _execute_tool(name: str, args: dict[str, Any]) -> str:
    """Execute a tool by calling the enrollment/processing API directly."""
    endpoint = _TOOL_ENDPOINTS.get(name)
    if not endpoint:
        return json.dumps({"error": f"Unknown tool: {name}"})

    method, path_template = endpoint
    base_url = settings.enrollment_service_url

    # Build the URL — substitute path params
    path = path_template
    for key, value in args.items():
        path = path.replace(f"{{{key}}}", str(value))

    url = f"{base_url}{path}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if method == "POST":
                resp = await client.post(url, json=args)
            else:
                resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"API error: {e.response.status_code}", "detail": e.response.text[:500]})
        except httpx.RequestError as e:
            return json.dumps({"error": f"Connection error: {str(e)}"})


async def enrollment_node(state: AgentState) -> dict[str, Any]:
    """Run the enrollment agent — LLM with tool calling for enrollment operations."""
    user_message = state["user_message"]
    logger.info(f"Enrollment agent: processing '{user_message[:80]}'")

    provider = get_provider()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _ENROLLMENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    tool_calls_made: list[ToolCall] = []
    max_iterations = settings.max_agent_iterations

    for iteration in range(max_iterations):
        response = await provider.chat(messages=messages, tools=_ENROLLMENT_TOOLS)

        if not response.tool_calls:
            # No more tool calls — return the response
            result = AgentResult(
                agent=AgentType.ENROLLMENT,
                response=response.content,
                confidence=0.8,
                tool_calls=tool_calls_made,
            )
            return {"agent_results": [result]}

        # Process tool calls
        messages.append({"role": "assistant", "content": response.content, "tool_calls": response.tool_calls})

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["arguments"]
            logger.info(f"Enrollment agent: calling {tool_name}({json.dumps(tool_args)})")

            result_text = await _execute_tool(tool_name, tool_args)
            tool_calls_made.append(ToolCall(
                tool_name=tool_name,
                tool_args=tool_args,
                result=result_text[:1000],
                success="error" not in result_text.lower()[:50],
            ))

            messages.append({"role": "tool", "content": result_text})

    # Max iterations
    result = AgentResult(
        agent=AgentType.ENROLLMENT,
        response="I reached the maximum number of steps for this request.",
        confidence=0.3,
        tool_calls=tool_calls_made,
        error="Max iterations reached",
    )
    return {"agent_results": [result]}
