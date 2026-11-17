from __future__ import annotations

import json
from typing import Any

from app.agents.llm.provider import (
    LLMProvider,
    LLMResponse,
    ToolCall,
)


class MockProvider(LLMProvider):
    """
    Deterministic local LLM provider used for development
    and integration testing.

    It simulates an LLM that:
        1. Retrieves payment information.
        2. Requests the recovery decision.
        3. Produces a final explanation.

    No external API is contacted.
    """

    def __init__(self) -> None:
        self.call_count = 0

    # ========================================================
    # Main LLM interface
    # ========================================================

    def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:

        self.call_count += 1

        # ----------------------------------------------------
        # STEP 1
        # Retrieve payment
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
                tool_calls=[
                    ToolCall(
                        call_id="mock_call_1",
                        tool_name="get_payment",
                        arguments={
                            "payment_id": payment_id
                        },
                    )
                ]
            )

        # ----------------------------------------------------
        # STEP 2
        # Ask the deterministic recovery tool
        # ----------------------------------------------------

        if self.call_count == 2:

            payment_id = self._extract_payment_id(
                messages
            )

            if payment_id is None:

                return LLMResponse(
                    content=(
                        "I could not determine "
                        "the payment ID."
                    )
                )

            return LLMResponse(
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
                ]
            )

        # ----------------------------------------------------
        # STEP 3
        # Produce final explanation
        # ----------------------------------------------------

        decision = self._find_decision(
            messages
        )

        if decision is None:

            return LLMResponse(
                content=(
                    "The recovery investigation "
                    "could not produce a decision."
                )
            )

        return LLMResponse(
            content=self._build_final_answer(
                decision
            )
        )

    # ========================================================
    # Payment ID extraction
    # ========================================================

    @staticmethod
    def _extract_payment_id(
        messages: list[dict[str, Any]],
    ) -> str | None:

        # First search normal user/assistant content.
        for message in messages:

            content = message.get(
                "content"
            )

            if not isinstance(
                content,
                str,
            ):
                continue

            words = (
                content
                .replace('"', " ")
                .replace("'", " ")
                .split()
            )

            for word in words:

                cleaned = word.strip(
                    ".,:;!?()[]{}"
                )

                if cleaned.startswith("pay_"):
                    return cleaned

        # Then inspect tool responses.
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

            try:

                data = json.loads(
                    content
                )

            except json.JSONDecodeError:
                continue

            payment_id = (
                MockProvider._find_payment_id_recursive(
                    data
                )
            )

            if payment_id:
                return payment_id

        return None

    @staticmethod
    def _find_payment_id_recursive(
        value: Any,
    ) -> str | None:

        if isinstance(
            value,
            dict,
        ):

            payment_id = value.get(
                "payment_id"
            )

            if (
                isinstance(
                    payment_id,
                    str,
                )
                and payment_id.startswith(
                    "pay_"
                )
            ):
                return payment_id

            for child in value.values():

                result = (
                    MockProvider._find_payment_id_recursive(
                        child
                    )
                )

                if result:
                    return result

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                result = (
                    MockProvider._find_payment_id_recursive(
                        child
                    )
                )

                if result:
                    return result

        return None

    # ========================================================
    # Find decision tool response
    # ========================================================

    @staticmethod
    def _find_decision(
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        # Search backwards so the newest tool response
        # is considered first.
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

            try:

                data = json.loads(
                    content
                )

            except json.JSONDecodeError:

                continue

            decision = (
                MockProvider._find_decision_recursive(
                    data
                )
            )

            if decision is not None:
                return decision

        return None

    @staticmethod
    def _find_decision_recursive(
        value: Any,
    ) -> dict[str, Any] | None:

        if isinstance(
            value,
            dict,
        ):

            # The recovery decision object has these
            # deterministic decision fields.
            if (
                "priority" in value
                and "recommended_action" in value
                and "recovery_probability" in value
            ):

                return value

            # The actual tool response is usually:
            #
            # {
            #     "payment_id": "...",
            #     "success": true,
            #     "decision": {
            #         ...
            #     }
            # }
            #
            # Therefore recursively search nested values.

            for child in value.values():

                result = (
                    MockProvider._find_decision_recursive(
                        child
                    )
                )

                if result is not None:
                    return result

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                result = (
                    MockProvider._find_decision_recursive(
                        child
                    )
                )

                if result is not None:
                    return result

        return None

    # ========================================================
    # Final answer
    # ========================================================

    @staticmethod
    def _build_final_answer(
        decision: dict[str, Any],
    ) -> str:

        eligible = decision.get(
            "eligible"
        )

        probability = decision.get(
            "recovery_probability"
        )

        revenue_at_risk = decision.get(
            "revenue_at_risk"
        )

        expected_recovery_value = decision.get(
            "expected_recovery_value"
        )

        priority = decision.get(
            "priority"
        )

        recommended_action = decision.get(
            "recommended_action"
        )

        reasons = decision.get(
            "reasons",
            [],
        )

        eligibility_text = (
            "eligible"
            if eligible
            else "not eligible"
        )

        if isinstance(
            probability,
            (int, float),
        ):
            probability_text = f"{probability * 100:.2f}%"
        else:
            probability_text = "N/A"

        if isinstance(
            revenue_at_risk,
            (int, float),
        ):
            revenue_text = f"₹{revenue_at_risk:,.2f}"
        else:
            revenue_text = "N/A"

        if isinstance(
            expected_recovery_value,
            (int, float),
        ):
            expected_text = f"₹{expected_recovery_value:,.2f}"
        else:
            expected_text = "N/A"

        # Filter out reasons that just repeat the probability or expected value
        filtered_reasons = [r for r in reasons if "probability" not in r.lower() and "value" not in r.lower()]
        if filtered_reasons:
            reasons_text = " ".join(filtered_reasons)
        elif reasons:
            reasons_text = " ".join(reasons)
        else:
            reasons_text = ""

        action_map = {
            "RETRY_PAYMENT": "payment retry",
            "RETRY_WITH_CAUTION": "cautious retry",
            "DO_NOT_RETRY": "do not retry",
            "DEFER_RECOVERY": "defer recovery",
            "ESCALATE_TO_HUMAN": "human escalation",
            "WAIT_FOR_COOLDOWN": "wait for cooldown",
        }
        readable_action = action_map.get(recommended_action, recommended_action).lower()

        final_sentence = f"{reasons_text} Making a {readable_action} the recommended action." if reasons_text else f"Making a {readable_action} the recommended action."

        recommendation_prefix = "Recovery recommended." if eligible else "Recovery not recommended."

        if eligible:
            return (
                f"{recommendation_prefix}\n\n"
                f"This payment is eligible for recovery with an estimated "
                f"{probability_text} probability of success. The failed transaction represents "
                f"{revenue_text} in at-risk revenue, with an expected recovery value of "
                f"{expected_text}.\n\n"
                f"{final_sentence}"
            )
        else:
            return (
                f"{recommendation_prefix}\n\n"
                f"This payment is not eligible for recovery. "
                f"Recovery probability was not calculated because this payment is not eligible for recovery. "
                f"The failed transaction represents {revenue_text} in at-risk revenue. "
                f"Expected recovery value was not calculated because recovery is blocked by policy.\n\n"
                f"{final_sentence}"
            )