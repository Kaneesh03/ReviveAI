from app.domain.recovery.eligibility import (
    evaluate_recovery_eligibility,
)

from app.domain.recovery.revenue_risk import (
    calculate_revenue_risk,
)


def test_failed_payment_is_eligible():

    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=2500,
        retry_count=0,
        subscription_status="active",
    )

    assert result.eligible is True


def test_successful_payment_is_not_eligible():

    result = evaluate_recovery_eligibility(
        payment_status="success",
        failure_reason=None,
        amount=2500,
        retry_count=0,
        subscription_status="active",
    )

    assert result.eligible is False


def test_permanent_failure_is_not_eligible():

    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="repeated_failure",
        amount=2500,
        retry_count=0,
        subscription_status="active",
    )

    assert result.eligible is False


def test_halted_subscription_is_not_eligible():

    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="network_error",
        amount=2500,
        retry_count=0,
        subscription_status="halted",
    )

    assert result.eligible is False


def test_revenue_risk_calculation():

    result = calculate_revenue_risk(
        amount=2000,
        recovery_probability=0.80,
    )

    assert result.revenue_at_risk == 2000

    assert result.recovery_probability == 0.80

    assert result.expected_recovery_value == 1600