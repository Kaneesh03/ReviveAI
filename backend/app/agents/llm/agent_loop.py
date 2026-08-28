import json
from typing import Any

from app.agents.llm.provider import (
    LLMProvider,
    LLMResponse,
)
from app.agents.tools.executor import (
    ToolExecutor,
)
from app.agents.tools.schemas import (
    TOOL_SCHEMAS,
)


class AgentLoop:
    """
    Runs the ReviveAI LLM tool-calling loop.

    Responsibilities:
    - Send the conversation to the LLM.
    - Allow the LLM to select registered tools.
    - Execute tools only through ToolExecutor.
    - Return tool results to the LLM.
    - Stop when the LLM produces a final answer.

    The LLM is responsible for reasoning and tool selection.

    Deterministic business rules remain inside the
    domain/decision layer and are never delegated to the LLM.
    """

    MAX_ITERATIONS = 5

    def __init__(
        self,
        provider: LLMProvider,
        executor: ToolExecutor | None = None,
    ) -> None:

        self.provider = provider

        self.executor = (
            executor
            or ToolExecutor()
        )

    def run(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        actions: list[dict[str, Any]] = []
        errors: list[str] = []

        # Track repeated tool calls so the agent cannot
        # get stuck repeatedly requesting the same operation.
        tool_call_history: list[str] = []

        for iteration in range(
            self.MAX_ITERATIONS
        ):

            try:

                response: LLMResponse = (
                    self.provider.generate(
                        messages=messages,
                        tools=TOOL_SCHEMAS,
                    )
                )

            except Exception as exc:

                error_message = str(exc)

                errors.append(
                    error_message
                )

                return {
                    "status": "provider_error",
                    "answer": (
                        "The AI provider could not "
                        "complete the investigation."
                    ),
                    "iterations": iteration + 1,
                    "actions": actions,
                    "errors": errors,
                }

            # ------------------------------------------------
            # Final answer
            # ------------------------------------------------

            if not response.has_tool_calls:

                answer = (
                    response.content
                    or ""
                ).strip()

                if not answer:

                    answer = (
                        "The agent completed its "
                        "investigation but did not "
                        "produce a final explanation."
                    )

                return {
                    "status": "complete",
                    "answer": answer,
                    "iterations": iteration + 1,
                    "actions": actions,
                    "errors": errors,
                }

            # ------------------------------------------------
            # Preserve assistant tool-call message
            # ------------------------------------------------

            assistant_tool_calls: list[
                dict[str, Any]
            ] = []

            for tool_call in (
                response.tool_calls
            ):

                assistant_tool_calls.append(
                    {
                        "id": tool_call.call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.tool_name,
                            "arguments": json.dumps(
                                tool_call.arguments
                            ),
                        },
                    }
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": assistant_tool_calls,
                }
            )

            # ------------------------------------------------
            # Execute requested tools
            # ------------------------------------------------

            for tool_call in (
                response.tool_calls
            ):

                tool_name = (
                    tool_call.tool_name
                )

                arguments = (
                    tool_call.arguments
                )

                # Create a stable representation of the
                # requested operation for loop detection.
                call_signature = (
                    f"{tool_name}:"
                    f"{json.dumps(arguments, sort_keys=True)}"
                )

                # ------------------------------------------------
                # Repeated-call protection
                # ------------------------------------------------

                if (
                    call_signature
                    in tool_call_history
                ):

                    error_message = (
                        "Repeated tool call detected. "
                        "The agent already executed this "
                        "exact operation."
                    )

                    errors.append(
                        error_message
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.call_id
                            ),
                            "content": json.dumps(
                                {
                                    "success": False,
                                    "error": (
                                        error_message
                                    ),
                                }
                            ),
                        }
                    )

                    continue

                tool_call_history.append(
                    call_signature
                )

                actions.append(
                    {
                        "iteration": (
                            iteration + 1
                        ),
                        "tool": tool_name,
                        "arguments": arguments,
                    }
                )

                try:

                    result = (
                        self.executor.execute(
                            tool_name,
                            arguments,
                        )
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.call_id
                            ),
                            "content": json.dumps(
                                result,
                                default=str,
                            ),
                        }
                    )

                except Exception as exc:

                    error_message = str(exc)

                    errors.append(
                        error_message
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.call_id
                            ),
                            "content": json.dumps(
                                {
                                    "success": False,
                                    "error": (
                                        error_message
                                    ),
                                }
                            ),
                        }
                    )

        # ----------------------------------------------------
        # Maximum iterations reached
        # ----------------------------------------------------

        return {
            "status": "max_iterations_reached",
            "answer": (
                "The agent could not complete "
                "the investigation within the "
                "allowed number of steps."
            ),
            "iterations": self.MAX_ITERATIONS,
            "actions": actions,
            "errors": errors,
        }