"""MCP prompt templates for benefits enrollment agents."""

from mcp.server import Server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent


def register_prompts(server: Server) -> None:
    """Register all MCP prompts on the server instance."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="enrollment-assistant",
                description=(
                    "System prompt for an AI assistant that helps employees with benefits "
                    "enrollment. Knows how to submit enrollments, check status, and explain "
                    "the enrollment lifecycle."
                ),
                arguments=[],
            ),
            Prompt(
                name="status-checker",
                description=(
                    "Check and explain the status of an enrollment. Provide an enrollment ID, "
                    "employee ID, or employee name."
                ),
                arguments=[
                    PromptArgument(
                        name="identifier",
                        description="Enrollment ID, employee ID (e.g. E12345), or employee name",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="benefits-advisor",
                description=(
                    "Get personalized benefit plan recommendations. Provide employee context "
                    "for tailored advice."
                ),
                arguments=[
                    PromptArgument(
                        name="employee_context",
                        description="Any context about the employee (role, family size, preferences, etc.)",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> list[PromptMessage]:
        arguments = arguments or {}

        match name:
            case "enrollment-assistant":
                return [
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=(
                                "You are a helpful employee benefits enrollment assistant. "
                                "You help employees submit new benefits enrollments, check "
                                "the status of existing enrollments, and understand the "
                                "enrollment lifecycle.\n\n"
                                "Enrollment lifecycle: SUBMITTED -> PROCESSING -> COMPLETED\n"
                                "- SUBMITTED: Enrollment accepted, queued for processing\n"
                                "- PROCESSING: Enrollment dispatched, being processed\n"
                                "- COMPLETED: Processing finished successfully\n"
                                "- DISPATCH_FAILED: Delivery failed, will retry automatically\n\n"
                                "Available benefit types: medical, dental, vision, life\n"
                                "Plan tiers vary by type (e.g. basic, silver, gold, platinum for medical).\n\n"
                                "Use the available tools to look up enrollments, submit new ones, "
                                "and check processing status. Always confirm details with the user "
                                "before submitting."
                            ),
                        ),
                    ),
                ]

            case "status-checker":
                identifier = arguments.get("identifier", "")
                return [
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=(
                                f"Check the enrollment status for: {identifier}\n\n"
                                "Steps:\n"
                                "1. Look up the enrollment using the appropriate tool "
                                "(by enrollment ID, employee ID, or employee name).\n"
                                "2. Get the processing details if available.\n"
                                "3. Explain the current status clearly, including:\n"
                                "   - Where the enrollment is in the lifecycle\n"
                                "   - When it was last updated\n"
                                "   - Any relevant messages\n"
                                "   - What to expect next"
                            ),
                        ),
                    ),
                ]

            case "benefits-advisor":
                context = arguments.get("employee_context", "No specific context provided.")
                return [
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=(
                                "Provide personalized benefit plan recommendations based on "
                                "the following employee context:\n\n"
                                f"{context}\n\n"
                                "Consider:\n"
                                "- Available benefit types: medical, dental, vision, life\n"
                                "- Plan tiers and coverage levels\n"
                                "- Cost vs. coverage tradeoffs\n"
                                "- Common recommendations for similar profiles\n\n"
                                "Provide clear, actionable recommendations with reasoning."
                            ),
                        ),
                    ),
                ]

            case _:
                raise ValueError(f"Unknown prompt: {name}")
