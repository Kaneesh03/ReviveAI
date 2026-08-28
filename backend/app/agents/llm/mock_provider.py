from __future__ import annotations

from typing import Any

from app.agents.llm.provider import (
    LLMProvider,
    LLMResponse,
    ToolCall,
)


class MockProvider(LLMProvider):
    """
    Deterministic local LLM provider for development and testing.

    This provider does not contact an external API.

    It simulates the tool-calling behavior that we expect
    from the real NVIDIA LLM.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:

        self.call_count += 1

        # ----------------------------------------------------
        # First call:
        # Ask for payment information.
        # ----------------------------------------------------

        if self.call_count == 1:

            payment_id = self._extract_payment_id(
                messages
            )

            if payment_id is None:

                return LLMResponse(
                    content=(
                        "Please provide a valid payment ID."
                    )
                )

            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        call_id="mock_call_1",
                        tool_name="get_payment",
                        arguments={
                            "payment_id": payment_id
                        },
                    )
                ],
            )

        # ----------------------------------------------------
        # Second call:
        # After payment information is available,
        # request the deterministic recovery decision.
        # ----------------------------------------------------

        if self.call_count == 2:

            payment_id = self._extract_payment_id(
                messages
            )

            if payment_id is None:

                return LLMResponse(
                    content=(
                        "I could not determine the payment ID."
                    )
                )

            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        call_id="mock_call_2",
                        tool_name=(
                            "make_payment_recovery_decision"
                        ),
                        arguments={
                            "payment_id": payment_id
                        },
                    )
                ],
            )

        # ----------------------------------------------------
        # Third call:
        # Produce the final operational explanation.
        # ----------------------------------------------------

        decision = self._find_latest_decision(
            messages
        )

        if decision is None:

            return LLMResponse(
                content=(
                    "The recovery investigation could "
                    "not produce a decision."
                )
            )

        return LLMResponse(
            content=self._build_final_answer(
                decision
            )
        )

    # ========================================================
    # Helpers
    # ========================================================

    @staticmethod
    def _extract_payment_id(
        messages: list[dict[str, Any]],
    ) -> str | None:

        # Search all message contents for a payment ID.
        for message in messages:

            content = message.get(
                "content"
            )

            if not isinstance(
                content,
                str,
            ):
                continue

            words = content.replace(
                '"',
                " ",
            ).replace(
                "'",
                " ",
            ).split()

            for word in words:

                cleaned = word.strip(
                    ".,:;!?()[]{}"
                )

                if cleaned.startswith(
                    "pay_"
                ):

                    return cleaned

        # Also inspect tool results.
        for message in messages:

            if message.get("role") != "tool":
                continue

            content = message.get(
                "content"
            )

            if not isinstance(
                content,
                str,
            ):
                continue

            marker = '"payment_id":'

            if marker in content:

                value = content.split(
                    marker,
                    1,
                )[1].split(
                    ",",
                    1,
                )[0]

                return value.strip(
                    ' "{}'
                )

        return None

    @staticmethod
    def _find_latest_decision(
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        for message in reversed(messages):

            if message.get("role") != "tool":
                continue

            content = message.get(
                "content"
            )

            if not isinstance(
                content,
                str,
            ):
                continue

            if (
                "priority" in content
                and "recommended_action" in content
            ):

                try:

                    import json

                    return json.loads(
                        content
                    )

                except json.JSONDecodeError:

                    return None

        return None

    @staticmethod
    def _build_final_answer(
        decision: dict[str, Any],
    ) -> str:

        # The decision tool currently returns a wrapper
        # containing the actual decision.
        actual_decision = decision.get(
            "decision",
            decision,
        )

        probability = actual_decision.get(
            "recovery_probability"
        )

        revenue_at_risk = actual_decision.get(
            "revenue_at_risk"
        )

        expected_recovery_value = actual_decision.get(
            "expected_recovery_value"
        )

        priority = actual_decision.get(
            "priority"
        )

        recommended_action = actual_decision.get(
            "recommended_action"
        )

        eligible = actual_decision.get(
            "eligible"
        )

        reasons = actual_decision.get(
            "reasons",
            [],
        )

        probability_text = (
            f"{probability * 100:.2f}%"
            if isinstance(
                probability,
                (int, float),
            )
            else "N/A"
        )

        revenue_text = (
            f"₹{revenue_at_risk:,.2f}"
            if isinstance(
                revenue_at_risk,
                (int, float),
            )
            else "N/A"
        )

        expected_text = (
            f"₹{expected_recovery_value:,.2f}"
            if isinstance(
                expected_recovery_value,
                (int, float),
            )
            else "N/A"
        )

        eligibility_text = (
            "eligible"
            if eligible
            else "not eligible"
        )

        reasons_text = " ".join(
            reasons
        )

        return (
            "Recovery investigation complete.\n\n"
            f"Eligibility: {eligibility_text}\n"
            f"Recovery probability: {probability_text}\n"
            f"Revenue at risk: {revenue_text}\n"
            f"Expected recovery value: {expected_text}\n"
            f"Priority: {priority}\n"
            f"Recommended action: "
            f"{recommended_action}\n\n"
            f"Reasons: {reasons_text}"
        )