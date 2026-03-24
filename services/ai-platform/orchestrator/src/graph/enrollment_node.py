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

try:
    import importlib.util
    from pathlib import Path as _Path
    _spec = importlib.util.spec_from_file_location(
        "obs_metrics",
        _Path(__file__).parent.parent.parent.parent / "observability" / "src" / "metrics" / "collector.py",
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _record_tool_call = _mod.record_tool_call
except Exception:
    def _record_tool_call(name: str) -> None: pass

logger = logging.getLogger(__name__)

_ENROLLMENT_SYSTEM_PROMPT = (
    "You are the enrollment specialist agent. You handle all enrollment "
    "operations: submitting new enrollments, checking status, listing "
    "enrollments by employee or status.\n\n"
    "CRITICAL RULES:\n"
    "1. NEVER fabricate or guess employee IDs, names, or emails. If the user has "
    "not provided their Employee ID, full name, and email address, you MUST ask "
    "for this information BEFORE calling any submit tool. Do NOT make up values.\n"
    "2. For enrollment submissions, you need ALL of: employeeId, employeeName, "
    "employeeEmail, and at least one benefit selection (type + plan). Ask for "
    "any missing fields before proceeding.\n"
    "3. Use check_enrollment_status for the most complete status picture.\n"
    "4. Available benefit types and their plan tiers:\n"
    "   - Medical: basic, silver, gold, platinum\n"
    "   - Dental: basic, premium\n"
    "   - Vision: basic, premium\n"
    "   - Life: basic (employer-paid), supplemental\n"
    "6. Enrollment statuses: SUBMITTED, PROCESSING, COMPLETED, DISPATCH_FAILED\n"
    "7. Be concise and present results in Markdown tables when listing multiple items.\n"
    "8. Never display enrollment UUIDs — show Employee Name, ID, Status, and Plan.\n\n"
    "RESPONSE RULES — CRITICAL:\n"
    "- NEVER mention API calls, HTTP errors, status codes, or technical failures "
    "to the user. They do not know or care about APIs.\n"
    "- If a tool returns an error or empty result, respond naturally. For example: "
    "'There are currently no enrollments with SUBMITTED status.' NOT 'The API "
    "returned a 404 error.'\n"
    "- If no data is found, just say so briefly. Do NOT fill the response with "
    "unrelated information like plan tier tables or benefit type lists.\n"
    "- Keep responses short and direct. Answer exactly what was asked.\n"
    "- When listing enrollment counts, present a simple summary like: "
    "'Here are the current enrollment counts:\\n\\n| Status | Count |\\n"
    "| SUBMITTED | 3 |\\n| PROCESSING | 1 |\\n| COMPLETED | 5 |'\n\n"
    "When a user wants to enroll but hasn't given their details, respond with a "
    "helpful message explaining which plans are available and ask for their "
    "Employee ID, full name, and email to proceed.\n\n"
    "When the user provides their details in a follow-up message (e.g., "
    "'T12345, John Smith, john@company.com'), parse the information and call "
    "the submit_enrollment tool with the extracted data. NEVER print raw JSON "
    "to the user — always use the tool functions to perform actions."
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
                                "plan": {"type": "string", "description": "Plan tier. Medical: basic/silver/gold/platinum. Dental: basic/premium. Vision: basic/premium. Life: basic/supplemental."},
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
    {
        "type": "function",
        "function": {
            "name": "get_enrollment_summary",
            "description": "Get a summary of enrollment counts grouped by status. Use this when the user asks for overall counts, totals, or a status overview.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

# Map tool names to API endpoints
_TOOL_ENDPOINTS: dict[str, tuple[str, str]] = {
    "submit_enrollment": ("POST", "/api/enrollments"),
    "get_enrollment": ("GET", "/api/enrollments/{enrollmentId}"),
    "list_enrollments_by_employee_id": ("GET", "/api/enrollments/by-employee/{employeeId}"),
    "list_enrollments_by_employee_name": ("GET", "/api/enrollments/by-name/{employeeName}"),
    "list_enrollments_by_status": ("GET", "/api/enrollments/by-status?status={status}"),
    "check_enrollment_status": ("GET", "/api/enrollments/{enrollmentId}"),
}


async def _get_enrollment_summary() -> str:
    """Fetch enrollment counts for all statuses in one call."""
    base_url = settings.enrollment_service_url
    statuses = ["SUBMITTED", "PROCESSING", "COMPLETED", "DISPATCH_FAILED"]
    summary = []

    async with httpx.AsyncClient(timeout=15) as client:
        for status in statuses:
            try:
                resp = await client.get(f"{base_url}/api/enrollments/by-status?status={status}")
                if resp.status_code == 200:
                    data = resp.json()
                    count = len(data) if isinstance(data, list) else 0
                else:
                    count = 0
            except Exception:
                count = 0
            summary.append({"status": status, "count": count})

    total = sum(s["count"] for s in summary)
    return json.dumps({"summary": summary, "total": total})


async def _execute_tool(name: str, args: dict[str, Any]) -> str:
    """Execute a tool by calling the enrollment/processing API directly."""
    # Special handler: get_enrollment_summary fetches all statuses in one call
    if name == "get_enrollment_summary":
        return await _get_enrollment_summary()

    endpoint = _TOOL_ENDPOINTS.get(name)
    if not endpoint:
        return json.dumps({"result": "This operation is not available."})

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

            # Return empty list for 404 on list/search endpoints
            if resp.status_code == 404 and name.startswith("list_"):
                return json.dumps([])

            resp.raise_for_status()
            return resp.text
        except httpx.HTTPStatusError as e:
            logger.warning(f"Tool {name} HTTP {e.response.status_code}: {e.response.text[:200]}")
            # Return user-friendly error — never expose HTTP codes to the LLM
            if e.response.status_code == 404:
                return json.dumps({"result": "No matching records found."})
            return json.dumps({"result": "Unable to complete this operation right now. Please try again."})
        except httpx.RequestError as e:
            logger.warning(f"Tool {name} connection error: {e}")
            return json.dumps({"result": "The enrollment service is temporarily unavailable. Please try again in a moment."})


async def enrollment_node(state: AgentState) -> dict[str, Any]:
    """Run the enrollment agent — LLM with tool calling for enrollment operations."""
    user_message = state["user_message"]
    logger.info(f"Enrollment agent: processing '{user_message[:80]}'")

    provider = get_provider()

    # Build messages with conversation history so the LLM has full context
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _ENROLLMENT_SYSTEM_PROMPT},
    ]

    # Include recent conversation history (last 10 messages) for context
    history = state.get("messages", [])
    for msg in history[-10:]:
        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", "")
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

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

        # Process tool calls — format for Ollama's expected message structure
        ollama_tool_calls = [
            {"function": {"name": tc["name"], "arguments": tc["arguments"]}}
            for tc in response.tool_calls
        ]
        messages.append({"role": "assistant", "content": response.content or "", "tool_calls": ollama_tool_calls})

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["arguments"]
            logger.info(f"Enrollment agent: calling {tool_name}({json.dumps(tool_args)})")

            # Guard: block submit_enrollment if required fields are missing or fabricated
            if tool_name == "submit_enrollment":
                employee_id = tool_args.get("employeeId", "")
                employee_email = tool_args.get("employeeEmail", "")
                employee_name = tool_args.get("employeeName", "")
                missing = []
                if not employee_id:
                    missing.append("Employee ID")
                if not employee_email or "@example.com" in employee_email:
                    missing.append("email address")
                if not employee_name or employee_name.lower() in ("john doe", "jane doe", "unknown"):
                    missing.append("full name")
                if missing:
                    missing_str = ", ".join(missing)
                    result_text = (
                        f"The user needs to provide their {missing_str} before enrollment can proceed. "
                        f"Ask them for these details politely. Do not mention any errors or technical issues."
                    )
                    tool_calls_made.append(ToolCall(
                        tool_name=tool_name, tool_args=tool_args,
                        result=result_text, success=True,
                    ))
                    messages.append({"role": "tool", "content": result_text})
                    continue

            result_text = await _execute_tool(tool_name, tool_args)
            _record_tool_call(tool_name)
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
