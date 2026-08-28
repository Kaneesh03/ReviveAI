from dataclasses import dataclass


@dataclass
class RevenueRisk:
    revenue_at_risk: float
    recovery_probability: float
    expected_recovery_value: float


def calculate_revenue_risk(
    *,
    amount: float,
    recovery_probability: float,
) -> RevenueRisk:

    # Keep probability between 0 and 1.
    probability = max(
        0.0,
        min(
            recovery_probability,
            1.0,
        ),
    )

    # Expected value = payment amount × probability
    expected_recovery_value = (
        amount * probability
    )

    return RevenueRisk(
        revenue_at_risk=round(
            amount,
            2,
        ),
        recovery_probability=round(
            probability,
            4,
        ),
        expected_recovery_value=round(
            expected_recovery_value,
            2,
        ),
    )