from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a tool call requested by the LLM."""

    call_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Normalized response returned by an LLM provider."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(
        default_factory=list
    )

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """
        Generate an LLM response.

        The response may contain either normal text,
        tool calls, or both.
        """

        raise NotImplementedError