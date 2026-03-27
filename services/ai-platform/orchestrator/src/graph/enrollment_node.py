"""Enrollment agent node — handles enrollment CRUD operations via MCP tools."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from config.settings import settings

from src.graph.state import AgentState
from src.models.state import AgentResult, AgentType, TokenUsage, ToolCall
from src.providers.provider_factory import get_provider

try:
    import importlib.util
    import sys as _sys
    from pathlib import Path as _Path
    if "obs_metrics" in _sys.modules:
        _mod = _sys.modules["obs_metrics"]
    else:
        _spec = importlib.util.spec_from_file_location(
            "obs_metrics",
            _Path(__file__).parent.parent.parent.parent / "observability" / "src" / "metrics" / "collector.py",
        )
        _mod = importlib.util.module_from_spec(_spec)
        _sys.modules["obs_metrics"] = _mod
        _spec.loader.exec_module(_mod)
    _record_tool_call = _mod.record_tool_call
except Exception:
    def _record_tool_call(name: str) -> None:
        pass

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
    "3. Available benefit types and their plan tiers:\n"
    "   - Medical: basic, silver, gold, platinum\n"
    "   - Dental: basic, premium\n"
    "   - Vision: basic, premium\n"
    "   - Life: basic (employer-paid), supplemental\n"
    "4. Enrollment statuses: SUBMITTED, PROCESSING, COMPLETED, DISPATCH_FAILED\n"
    "5. Be concise and present results in Markdown tables when listing multiple items.\n"
    "6. Never display enrollment UUIDs — show Employee Name, ID, Status, and Plan.\n\n"
    "INTERPRETING TOOL RESULTS:\n"
    "- When submit_enrollment returns data with a status of SUBMITTED, the enrollment "
    "was SUCCESSFUL. Confirm this to the user: 'Your enrollment has been submitted "
    "successfully!' Show their name, employee ID, plan, and status.\n"
    "- SUBMITTED means the enrollment is queued for processing — this is the expected "
    "initial state. It is NOT an error.\n"
    "- Only say an enrollment failed if the tool returns an explicit error message.\n\n"
    "CONTEXT AWARENESS:\n"
    "- Pay attention to the conversation history. If a user just enrolled and asks "
    "about 'the enrollment we just did' or 'the new enrollment', use their Employee ID "
    "from the earlier conversation to look it up via list_enrollments_by_employee_id. "
    "Do NOT ask them for information they already provided.\n"
    "- When checking status after a submission, prefer list_enrollments_by_employee_id "
    "over check_enrollment_status (which requires a UUID the user doesn't have).\n\n"
    "RESPONSE RULES — CRITICAL:\n"
    "- NEVER mention API calls, HTTP errors, status codes, or technical failures "
    "to the user. They do not know or care about APIs.\n"
    "- If a tool returns an error or empty result, respond naturally. For example: "
    "'There are currently no enrollments with SUBMITTED status.' NOT 'The API "
    "returned a 404 error.'\n"
    "- If no data is found, just say so briefly. Do NOT fill the response with "
    "unrelated information like plan tier tables or benefit type lists.\n"
    "- Keep responses short and direct. Answer exactly what was asked.\n"
    "- NEVER output raw JSON, function call objects, or tool schemas to the user. "
    "Always use the tool functions to perform actions — never describe the tool call "
    "as text.\n"
    "- You can only look up enrollments by employee ID, employee name, or status. "
    "You CANNOT search by plan type. If the user asks a question you cannot answer "
    "with your available tools (e.g., 'which employees have medical gold'), say: "
    "'I can look up enrollments by employee name, employee ID, or status. "
    "For plan-specific reporting, please contact your HR department.'\n"
    "- NEVER fabricate data or show empty tables. If you have no data, say so in "
    "a plain sentence.\n\n"
    "When a user wants to enroll but hasn't given their details, respond with a "
    "helpful message explaining which plans are available and ask for their "
    "Employee ID, full name, and email to proceed.\n\n"
    "When the user provides their details in a follow-up message (e.g., "
    "'T12345, John Smith, john@company.com'), parse the information and call "
    "the submit_enrollment tool with the extracted data."
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


async def _execute_tool(name: str, args: dict[str, Any]) -> tuple[str, bool]:
    """Execute a tool by calling the enrollment/processing API directly.

    Returns a tuple of (result_text, is_enrollment_success).
    """
    # Special handler: get_enrollment_summary fetches all statuses in one call
    if name == "get_enrollment_summary":
        return await _get_enrollment_summary(), False

    endpoint = _TOOL_ENDPOINTS.get(name)
    if not endpoint:
        return json.dumps({"result": "This operation is not available."}), False

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
                return json.dumps([]), False

            resp.raise_for_status()
            result_text = resp.text

            # Flag successful enrollment submissions
            is_enrollment_success = (
                name == "submit_enrollment" and resp.status_code in (200, 201, 202)
            )

            return result_text, is_enrollment_success
        except httpx.HTTPStatusError as e:
            logger.warning(f"Tool {name} HTTP {e.response.status_code}: {e.response.text[:200]}")
            # Return user-friendly error — never expose HTTP codes to the LLM
            if e.response.status_code == 404:
                return json.dumps({"result": "No matching records found."}), False
            return json.dumps({"result": "Unable to complete this operation right now. Please try again."}), False
        except httpx.RequestError as e:
            logger.warning(f"Tool {name} connection error: {e}")
            return json.dumps({"result": "The enrollment service is temporarily unavailable. Please try again in a moment."}), False


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
    accumulated_usage = TokenUsage()
    max_iterations = settings.max_agent_iterations

    for iteration in range(max_iterations):
        response = await provider.chat(messages=messages, tools=_ENROLLMENT_TOOLS)

        if hasattr(response, "usage") and response.usage:
            u = response.usage
            accumulated_usage.add(u.prompt_tokens, u.completion_tokens, u.model)

        if not response.tool_calls:
            # Sanitize: if the LLM leaked a raw JSON tool call as text, strip it
            content = response.content or ""
            if '{"name":' in content and '"parameters"' in content:
                # LLM output a tool call as text instead of using function calling
                logger.warning("Enrollment agent: stripped leaked tool call JSON from response")
                content = re.sub(
                    r'\{["\s]*name["\s]*:.*?"parameters".*?\}',
                    "",
                    content,
                    flags=re.DOTALL,
                ).strip()
                if not content:
                    content = "Let me look that up for you."

            result = AgentResult(
                agent=AgentType.ENROLLMENT,
                response=content,
                confidence=0.8,
                tool_calls=tool_calls_made,
            )
            return {"agent_results": [result], "token_usage": accumulated_usage}

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

            # Fix: LLMs sometimes pass selections as a JSON string instead of array
            if tool_name == "submit_enrollment" and isinstance(tool_args.get("selections"), str):
                try:
                    tool_args["selections"] = json.loads(tool_args["selections"])
                except (json.JSONDecodeError, TypeError):
                    pass

            result_text, is_enrollment_success = await _execute_tool(tool_name, tool_args)
            _record_tool_call(tool_name)

            # Short-circuit: if enrollment succeeded, format the response
            # directly instead of letting the LLM interpret it
            if is_enrollment_success:
                try:
                    data = json.loads(result_text)
                except Exception:
                    data = {}
                selections = tool_args.get("selections", [])
                plan_lines = "\n".join(
                    f"- **{s.get('type', '').title()}**: {s.get('plan', '').title()}"
                    for s in selections
                )
                success_msg = (
                    f"Your enrollment has been submitted successfully!\n\n"
                    f"| Detail | Value |\n"
                    f"|--------|-------|\n"
                    f"| **Name** | {data.get('employeeName', tool_args.get('employeeName', ''))} |\n"
                    f"| **Employee ID** | {data.get('employeeId', tool_args.get('employeeId', ''))} |\n"
                    f"| **Status** | {data.get('status', 'SUBMITTED')} |\n\n"
                    f"**Plans enrolled:**\n{plan_lines}\n\n"
                    f"Your enrollment is now queued for processing."
                )
                tool_calls_made.append(ToolCall(
                    tool_name=tool_name, tool_args=tool_args,
                    result="Enrollment submitted successfully", success=True,
                ))
                result = AgentResult(
                    agent=AgentType.ENROLLMENT,
                    response=success_msg,
                    confidence=0.9,
                    tool_calls=tool_calls_made,
                )
                return {"agent_results": [result], "token_usage": accumulated_usage}

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
    return {"agent_results": [result], "token_usage": accumulated_usage}
