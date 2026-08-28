from dataclasses import dataclass
from typing import List


@dataclass
class RecoveryDecision:
    eligible: bool
    recovery_probability: float
    revenue_at_risk: float
    expected_recovery_value: float
    priority: str
    recommended_action: str
    reasons: List[str]


def calculate_priority(
    expected_recovery_value: float,
    recovery_probability: float,
) -> str:

    if (
        expected_recovery_value >= 10000
        and recovery_probability >= 0.75
    ):
        return "HIGH"

    if (
        expected_recovery_value >= 3000
        and recovery_probability >= 0.60
    ):
        return "MEDIUM"

    return "LOW"


def make_recovery_decision(
    *,
    eligible: bool,
    amount: float,
    recovery_probability: float,
    failure_reason: str,
    retry_count: int,
    subscription_status: str,
    lifetime_value: float,
) -> RecoveryDecision:

    # --------------------------------------------------------
    # Ineligible case
    # --------------------------------------------------------

    if not eligible:

        return RecoveryDecision(
            eligible=False,
            recovery_probability=0.0,
            revenue_at_risk=amount,
            expected_recovery_value=0.0,
            priority="NONE",
            recommended_action="DO_NOT_RETRY",
            reasons=[
                "Payment is not recovery eligible."
            ],
        )

    # --------------------------------------------------------
    # Expected recovery value
    # --------------------------------------------------------

    expected_recovery_value = (
        amount
        * recovery_probability
    )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    priority = calculate_priority(
        expected_recovery_value,
        recovery_probability,
    )

    # --------------------------------------------------------
    # Reasons
    # --------------------------------------------------------

    reasons = []

    if recovery_probability >= 0.80:
        reasons.append(
            "High predicted recovery probability."
        )

    elif recovery_probability >= 0.60:
        reasons.append(
            "Moderate predicted recovery probability."
        )

    else:
        reasons.append(
            "Low predicted recovery probability."
        )

    if expected_recovery_value >= 10000:
        reasons.append(
            "High expected recovery value."
        )

    elif expected_recovery_value >= 3000:
        reasons.append(
            "Meaningful expected recovery value."
        )

    if failure_reason == "temporary_bank_failure":
        reasons.append(
            "Failure appears temporary."
        )

    elif failure_reason == "network_error":
        reasons.append(
            "Failure is consistent with a transient network issue."
        )

    elif failure_reason == "insufficient_funds":
        reasons.append(
            "Failure may be recoverable after funds become available."
        )

    if subscription_status == "active":
        reasons.append(
            "Subscription is currently active."
        )

    if lifetime_value >= 15000:
        reasons.append(
            "Customer has high lifetime value."
        )

    if retry_count == 0:
        reasons.append(
            "No previous retry has been attempted."
        )

    elif retry_count >= 2:
        reasons.append(
            "Multiple retries have already occurred."
        )

    # --------------------------------------------------------
    # Recommended action
    # --------------------------------------------------------

    if priority == "HIGH":

        action = "RETRY_PAYMENT"

    elif priority == "MEDIUM":

        action = "RETRY_WITH_CAUTION"

    else:

        action = "DEFER_RECOVERY"

    return RecoveryDecision(
        eligible=True,
        recovery_probability=round(
            recovery_probability,
            4,
        ),
        revenue_at_risk=round(
            amount,
            2,
        ),
        expected_recovery_value=round(
            expected_recovery_value,
            2,
        ),
        priority=priority,
        recommended_action=action,
        reasons=reasons,
    )