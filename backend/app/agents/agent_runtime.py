from typing import Any

from app.agents.recovery_agent import (
    RecoveryAgent,
)


class AgentRuntime:
    """
    Runtime entry point for ReviveAI.

    This class will eventually connect the LLM to the
    recovery tool ecosystem.

    For now it provides a deterministic recovery analysis
    interface that can later be wrapped by an LLM.
    """

    def __init__(self) -> None:

        self.recovery_agent = (
            RecoveryAgent()
        )

    def analyze_payment(
        self,
        payment_id: str,
    ) -> dict[str, Any]:

        return (
            self.recovery_agent
            .investigate(
                payment_id
            )
        )