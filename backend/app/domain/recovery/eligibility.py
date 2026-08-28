from dataclasses import dataclass


@dataclass
class EligibilityResult:
    eligible: bool
    reason: str


MAX_RECOVERY_AMOUNT = 50_000
MAX_RETRY_COUNT = 2


PERMANENT_FAILURE_REASONS = {
    "payment_method_issue",
    "repeated_failure",
    "unknown_failure",
}


def evaluate_recovery_eligibility(
    *,
    payment_status: str,
    failure_reason: str | None,
    amount: float,
    retry_count: int,
    subscription_status: str,
) -> EligibilityResult:

    # Payment must actually have failed.
    if payment_status != "failed":
        return EligibilityResult(
            eligible=False,
            reason="payment_not_failed",
        )

    # We need a failure reason for a recovery decision.
    if not failure_reason:
        return EligibilityResult(
            eligible=False,
            reason="missing_failure_reason",
        )

    # Don't attempt recovery on known permanent failures.
    if failure_reason in PERMANENT_FAILURE_REASONS:
        return EligibilityResult(
            eligible=False,
            reason="permanent_failure_reason",
        )

    # Halted subscriptions should not be retried.
    if subscription_status == "halted":
        return EligibilityResult(
            eligible=False,
            reason="subscription_halted",
        )

    # Excessive retries indicate diminishing recovery value.
    if retry_count > MAX_RETRY_COUNT:
        return EligibilityResult(
            eligible=False,
            reason="retry_limit_exceeded",
        )

    # Avoid attempting recovery on unusually large transactions
    # in this initial MVP policy.
    if amount > MAX_RECOVERY_AMOUNT:
        return EligibilityResult(
            eligible=False,
            reason="amount_above_recovery_limit",
        )

    return EligibilityResult(
        eligible=True,
        reason="eligible_for_recovery",
    )