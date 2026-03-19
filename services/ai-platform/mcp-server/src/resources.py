"""MCP resource definitions for benefits enrollment data."""

import json

from mcp.server import Server
from mcp.types import Resource, TextResourceContents

from src.benefits_client import benefits_client


def register_resources(server: Server) -> None:
    """Register all MCP resources on the server instance."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri="benefits://status-summary",
                name="Enrollment Status Summary",
                description="Aggregate counts of enrollments by status (SUBMITTED, PROCESSING, COMPLETED).",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> list[TextResourceContents]:
        if uri == "benefits://status-summary":
            summary = {}
            for status in ["SUBMITTED", "PROCESSING", "COMPLETED", "DISPATCH_FAILED"]:
                try:
                    items = await benefits_client.list_enrollments_by_status(status)
                    summary[status] = len(items)
                except Exception:
                    summary[status] = 0

            summary["total"] = sum(summary.values())
            return [
                TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=json.dumps(summary, indent=2),
                )
            ]

        raise ValueError(f"Unknown resource: {uri}")
