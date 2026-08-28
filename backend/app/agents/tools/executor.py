import json
from typing import Any

from app.agents.tools.registry import get_tool


class ToolExecutionError(Exception):
    """Raised when a tool call cannot be safely executed."""

    pass


class ToolExecutor:
    """
    Safely executes tools exposed to the AI agent.

    The LLM can only execute tools that are explicitly
    registered in the ReviveAI tool registry.
    """

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | str,
    ) -> dict[str, Any]:
        """
        Execute an allowlisted tool with validated arguments.
        """

        # ----------------------------------------------------
        # Validate tool name
        # ----------------------------------------------------

        tool = get_tool(tool_name)

        if tool is None:
            raise ToolExecutionError(
                f"Unknown or unauthorized tool: {tool_name}"
            )

        # ----------------------------------------------------
        # Normalize arguments
        # ----------------------------------------------------

        if isinstance(arguments, str):

            try:
                arguments = json.loads(
                    arguments
                )

            except json.JSONDecodeError as exc:

                raise ToolExecutionError(
                    "Tool arguments must be valid JSON."
                ) from exc

        if not isinstance(arguments, dict):

            raise ToolExecutionError(
                "Tool arguments must be a JSON object."
            )

        # ----------------------------------------------------
        # Basic payment_id validation
        # ----------------------------------------------------

        if "payment_id" in arguments:

            payment_id = arguments[
                "payment_id"
            ]

            if not isinstance(
                payment_id,
                str,
            ):

                raise ToolExecutionError(
                    "payment_id must be a string."
                )

            if not payment_id.startswith(
                "pay_"
            ):

                raise ToolExecutionError(
                    "Invalid payment_id format."
                )

        # ----------------------------------------------------
        # Execute allowlisted function
        # ----------------------------------------------------

        try:

            result = tool(
                **arguments
            )

        except TypeError as exc:

            raise ToolExecutionError(
                f"Invalid arguments for tool "
                f"'{tool_name}': {exc}"
            ) from exc

        except Exception as exc:

            raise ToolExecutionError(
                f"Tool '{tool_name}' failed: {exc}"
            ) from exc

        # ----------------------------------------------------
        # Normalize response
        # ----------------------------------------------------

        return {
            "tool": tool_name,
            "success": True,
            "result": result,
        }