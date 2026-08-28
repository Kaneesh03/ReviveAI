from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    Runtime state maintained during a ReviveAI investigation.

    The state contains only information discovered during
    the current investigation.
    """

    payment_id: str

    payment: dict[str, Any] | None = None

    eligibility: dict[str, Any] | None = None

    prediction: dict[str, Any] | None = None

    revenue_risk: dict[str, Any] | None = None

    decision: dict[str, Any] | None = None

    actions_taken: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    status: str = "initialized"