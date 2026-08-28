from typing import Any, Callable

from app.agents.tools.recovery_tools import (
    get_payment,
    check_payment_eligibility,
    predict_recovery,
    calculate_payment_revenue_risk,
    make_payment_recovery_decision,
)


# ============================================================
# Tool Registry
# ============================================================

TOOLS: dict[str, Callable[..., Any]] = {
    "get_payment": get_payment,
    "check_payment_eligibility": check_payment_eligibility,
    "predict_recovery": predict_recovery,
    "calculate_payment_revenue_risk": (
        calculate_payment_revenue_risk
    ),
    "make_payment_recovery_decision": (
        make_payment_recovery_decision
    ),
}


def get_tool(
    name: str,
) -> Callable[..., Any] | None:
    """Return a registered tool by name."""

    return TOOLS.get(name)


def list_tools() -> list[str]:
    """Return all registered tool names."""

    return list(TOOLS.keys())