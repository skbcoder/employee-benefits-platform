"""Direct benefits API proxy for internal tool execution.

This module calls the benefits platform REST APIs directly rather than
going through the MCP SSE transport, which is more efficient for
server-to-server communication within the AI Gateway.
"""

from typing import Any

import httpx

from config.settings import settings

_ENROLLMENT_URL = settings.enrollment_service_url
_PROCESSING_URL = settings.processing_service_url

_http_client: httpx.AsyncClient | None = None


async def _client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def execute_benefits_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Execute a benefits API tool call and return the parsed response."""
    client = await _client()

    match name:
        case "submit_enrollment":
            resp = await client.post(f"{_ENROLLMENT_URL}/api/enrollments", json=arguments)
            resp.raise_for_status()
            return resp.json()

        case "get_enrollment":
            eid = arguments["enrollmentId"]
            resp = await client.get(f"{_ENROLLMENT_URL}/api/enrollments/{eid}")
            resp.raise_for_status()
            return resp.json()

        case "get_enrollment_by_employee":
            emp_id = arguments["employeeId"]
            resp = await client.get(f"{_ENROLLMENT_URL}/api/enrollments/by-employee/{emp_id}")
            resp.raise_for_status()
            return resp.json()

        case "get_enrollment_by_name":
            name_val = arguments["employeeName"]
            resp = await client.get(f"{_ENROLLMENT_URL}/api/enrollments/by-name/{name_val}")
            resp.raise_for_status()
            return resp.json()

        case "list_enrollments_by_status":
            status = arguments["status"]
            resp = await client.get(
                f"{_ENROLLMENT_URL}/api/enrollments/by-status",
                params={"status": status},
            )
            resp.raise_for_status()
            return resp.json()

        case "get_processing_details":
            eid = arguments["enrollmentId"]
            resp = await client.get(f"{_PROCESSING_URL}/api/processed-enrollments/{eid}")
            resp.raise_for_status()
            return resp.json()

        case "get_processing_by_employee":
            emp_id = arguments["employeeId"]
            resp = await client.get(
                f"{_PROCESSING_URL}/api/processed-enrollments/by-employee/{emp_id}"
            )
            resp.raise_for_status()
            return resp.json()

        case "check_enrollment_status":
            eid = arguments["enrollmentId"]
            enrollment = (await client.get(f"{_ENROLLMENT_URL}/api/enrollments/{eid}")).json()

            processing = None
            try:
                proc_resp = await client.get(f"{_PROCESSING_URL}/api/processed-enrollments/{eid}")
                if proc_resp.status_code == 200:
                    processing = proc_resp.json()
            except Exception:
                pass

            status_order = {"SUBMITTED": 0, "DISPATCH_FAILED": 0, "PROCESSING": 1, "COMPLETED": 2}
            enroll_order = status_order.get(enrollment.get("status", ""), 0)
            proc_order = status_order.get(processing.get("status", "") if processing else "", -1)

            effective_status = (
                processing["status"] if processing and proc_order > enroll_order
                else enrollment["status"]
            )

            return {
                "enrollmentId": enrollment.get("enrollmentId"),
                "employeeId": enrollment.get("employeeId"),
                "employeeName": enrollment.get("employeeName"),
                "enrollmentStatus": enrollment.get("status"),
                "processingStatus": processing.get("status") if processing else None,
                "effectiveStatus": effective_status,
                "enrollmentUpdatedAt": enrollment.get("updatedAt"),
                "processingUpdatedAt": processing.get("updatedAt") if processing else None,
                "message": enrollment.get("message"),
            }

        case _:
            raise ValueError(f"Unknown tool: {name}")
