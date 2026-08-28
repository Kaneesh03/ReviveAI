from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


@dataclass
class ToolCall:
    call_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class NVIDIAProvider:

    def __init__(self) -> None:

        api_key = os.getenv("NVIDIA_API_KEY")
        base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )
        model = os.getenv("NVIDIA_MODEL")

        if not api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not configured."
            )

        if not model:
            raise ValueError(
                "NVIDIA_MODEL is not configured."
            )

        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    # --------------------------------------------------------
    # LLM generation
    # --------------------------------------------------------

    def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:

        request: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        max_attempts = 3

        response = None

        for attempt in range(max_attempts):

            try:

                response = (
                    self.client.chat.completions.create(
                        **request
                    )
                )

                break

            except Exception as exc:

                status_code = getattr(
                    exc,
                    "status_code",
                    None,
                )

                # NVIDIA temporary rate limit.
                if (
                    status_code == 429
                    and attempt < max_attempts - 1
                ):

                    wait_seconds = 2 ** attempt

                    print(
                        f"NVIDIA rate limit encountered. "
                        f"Retrying in {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)

                    continue

                raise

        if response is None:
            raise RuntimeError(
                "NVIDIA provider failed to return a response."
            )

        message = response.choices[0].message

        tool_calls: list[ToolCall] = []

        if message.tool_calls:

            for call in message.tool_calls:

                try:

                    arguments = json.loads(
                        call.function.arguments
                    )

                except json.JSONDecodeError as exc:

                    raise ValueError(
                        "NVIDIA returned invalid tool arguments."
                    ) from exc

                tool_calls.append(
                    ToolCall(
                        call_id=call.id,
                        tool_name=call.function.name,
                        arguments=arguments,
                    )
                )

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
        )