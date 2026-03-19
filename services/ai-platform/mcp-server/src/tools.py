"""MCP tool definitions wrapping the Benefits Platform APIs."""

import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.benefits_client import benefits_client


def register_tools(server: Server) -> None:
    """Register all MCP tools on the server instance."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="submit_enrollment",
                description=(
                    "Submit a new employee benefits enrollment. Requires employeeId, "
                    "employeeName, employeeEmail, and a list of benefit selections "
                    "(each with type and plan)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employeeId": {
                            "type": "string",
                            "description": "Employee ID (e.g. E12345)",
                        },
                        "employeeName": {
                            "type": "string",
                            "description": "Full name of the employee",
                        },
                        "employeeEmail": {
                            "type": "string",
                            "description": "Employee email address",
                        },
                        "selections": {
                            "type": "array",
                            "description": "Benefit selections",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["medical", "dental", "vision", "life"],
                                        "description": "Benefit type",
                                    },
                                    "plan": {
                                        "type": "string",
                                        "description": "Plan tier (e.g. basic, silver, gold, platinum)",
                                    },
                                },
                                "required": ["type", "plan"],
                            },
                        },
                    },
                    "required": [
                        "employeeId",
                        "employeeName",
                        "employeeEmail",
                        "selections",
                    ],
                },
            ),
            Tool(
                name="get_enrollment",
                description="Retrieve an enrollment record by its enrollment ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "enrollmentId": {
                            "type": "string",
                            "description": "The enrollment UUID",
                        },
                    },
                    "required": ["enrollmentId"],
                },
            ),
            Tool(
                name="get_enrollment_by_employee",
                description="Retrieve the most recent enrollment for an employee by their employee ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employeeId": {
                            "type": "string",
                            "description": "Employee ID (e.g. E12345)",
                        },
                    },
                    "required": ["employeeId"],
                },
            ),
            Tool(
                name="get_enrollment_by_name",
                description="Retrieve the most recent enrollment for an employee by their name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employeeName": {
                            "type": "string",
                            "description": "Full name of the employee",
                        },
                    },
                    "required": ["employeeName"],
                },
            ),
            Tool(
                name="list_enrollments_by_status",
                description=(
                    "List all enrollments with a given status. "
                    "Valid statuses: SUBMITTED, PROCESSING, COMPLETED, DISPATCH_FAILED."
                ),
                inputSchema={
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
            ),
            Tool(
                name="get_processing_details",
                description="Get the processing record for an enrollment (downstream execution state).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "enrollmentId": {
                            "type": "string",
                            "description": "The enrollment UUID",
                        },
                    },
                    "required": ["enrollmentId"],
                },
            ),
            Tool(
                name="get_processing_by_employee",
                description="Get the processing record for an employee's most recent enrollment.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employeeId": {
                            "type": "string",
                            "description": "Employee ID (e.g. E12345)",
                        },
                    },
                    "required": ["employeeId"],
                },
            ),
            Tool(
                name="check_enrollment_status",
                description=(
                    "Get the full enrollment status including both enrollment and processing "
                    "details with the effective (most advanced) status. Use this when you need "
                    "a complete picture of where an enrollment stands."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "enrollmentId": {
                            "type": "string",
                            "description": "The enrollment UUID",
                        },
                    },
                    "required": ["enrollmentId"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            result = await _execute_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Route tool call to the appropriate benefits client method."""
    match name:
        case "submit_enrollment":
            return await benefits_client.submit_enrollment(arguments)
        case "get_enrollment":
            return await benefits_client.get_enrollment(arguments["enrollmentId"])
        case "get_enrollment_by_employee":
            return await benefits_client.get_enrollment_by_employee(arguments["employeeId"])
        case "get_enrollment_by_name":
            return await benefits_client.get_enrollment_by_name(arguments["employeeName"])
        case "list_enrollments_by_status":
            return await benefits_client.list_enrollments_by_status(arguments["status"])
        case "get_processing_details":
            return await benefits_client.get_processing_details(arguments["enrollmentId"])
        case "get_processing_by_employee":
            return await benefits_client.get_processing_by_employee(arguments["employeeId"])
        case "check_enrollment_status":
            return await benefits_client.check_enrollment_status(arguments["enrollmentId"])
        case _:
            raise ValueError(f"Unknown tool: {name}")
