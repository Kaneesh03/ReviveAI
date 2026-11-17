"""
tests/test_scenarios.py

Multi-scenario eligibility and guardrail tests for ReviveAI.

These tests exercise the deterministic policy layer (eligibility.py
and decision_engine.py) across every scenario identified in the
validate_scenarios.py script.

Tests verify behavior, not implementation details.
"""
from __future__ import annotations

from app.domain.recovery.eligibility import (
    evaluate_recovery_eligibility,
    PERMANENT_FAILURE_REASONS,
    MAX_RETRY_COUNT,
    MAX_RECOVERY_AMOUNT,
)
from app.domain.recovery.decision_engine import make_recovery_decision
from app.domain.recovery.revenue_risk import calculate_revenue_risk


# ============================================================
# Eligibility — eligible cases
# ============================================================

def test_temporary_bank_failure_is_eligible():
    """
    Scenario: temporary_bank_failure with active subscription
    and retry count within limit.
    Expected: ELIGIBLE
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=4274.20,
        retry_count=0,
        subscription_status="active",
    )
    assert result.eligible is True
    assert result.reason == "eligible_for_recovery"


def test_network_error_is_eligible():
    """
    Scenario: network_error with active subscription.
    Expected: ELIGIBLE
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="network_error",
        amount=2580.63,
        retry_count=1,
        subscription_status="active",
    )
    assert result.eligible is True


def test_insufficient_funds_is_eligible():
    """
    Scenario: insufficient_funds — potentially recoverable.
    Expected: ELIGIBLE
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="insufficient_funds",
        amount=2004.43,
        retry_count=0,
        subscription_status="active",
    )
    assert result.eligible is True


def test_retry_count_at_limit_is_still_eligible():
    """
    retry_count == MAX_RETRY_COUNT (2) is still eligible.
    Only retry_count > MAX_RETRY_COUNT is blocked.
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=1000.00,
        retry_count=MAX_RETRY_COUNT,   # exactly at limit
        subscription_status="active",
    )
    assert result.eligible is True


# ============================================================
# Eligibility — ineligible cases
# ============================================================

def test_successful_payment_policy_is_not_eligible():
    """
    POLICY TEST: payment_status='success' is never eligible for recovery.

    This test calls evaluate_recovery_eligibility() directly against
    the deterministic eligibility policy.

    NOTE: This is intentionally NOT tested via the recovery API because
    the recovery dataset (recovery_training.csv) contains failed payments
    only.  A successful payment ID will return 404 from the API, which
    is correct API-scope behaviour — but it does not exercise the policy
    rule that rejects successful payments.  This unit test does.

    Expected: eligible=False, reason='payment_not_failed'
    """
    result = evaluate_recovery_eligibility(
        payment_status="success",
        failure_reason=None,
        amount=2000,
        retry_count=0,
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "payment_not_failed"


def test_payment_method_issue_is_not_eligible():
    """
    Permanent failure: payment_method_issue.
    Expected: NOT ELIGIBLE, reason=permanent_failure_reason
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="payment_method_issue",
        amount=2942.43,
        retry_count=1,
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "permanent_failure_reason"


def test_repeated_failure_is_not_eligible():
    """
    Permanent failure: repeated_failure.
    Expected: NOT ELIGIBLE
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="repeated_failure",
        amount=976.73,
        retry_count=2,
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "permanent_failure_reason"


def test_unknown_failure_is_not_eligible():
    """
    Permanent failure: unknown_failure.
    Expected: NOT ELIGIBLE
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="unknown_failure",
        amount=3861.83,
        retry_count=1,
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "permanent_failure_reason"


def test_all_permanent_failure_reasons_are_blocked():
    """
    All permanent failure reasons must be blocked.
    """
    for reason in PERMANENT_FAILURE_REASONS:
        result = evaluate_recovery_eligibility(
            payment_status="failed",
            failure_reason=reason,
            amount=1000.00,
            retry_count=0,
            subscription_status="active",
        )
        assert result.eligible is False, (
            f"Expected {reason} to be ineligible but got eligible=True"
        )
        assert result.reason == "permanent_failure_reason"


def test_halted_subscription_is_not_eligible():
    """
    Halted subscription.
    Expected: NOT ELIGIBLE, reason=subscription_halted
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="network_error",
        amount=2741.75,
        retry_count=1,
        subscription_status="halted",
    )
    assert result.eligible is False
    assert result.reason == "subscription_halted"


def test_retry_limit_exceeded_is_not_eligible():
    """
    retry_count > MAX_RETRY_COUNT (2) is NOT eligible.
    Dataset has retry=3 cases.
    Expected: NOT ELIGIBLE, reason=retry_limit_exceeded
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=1000.00,
        retry_count=MAX_RETRY_COUNT + 1,   # e.g. 3
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "retry_limit_exceeded"


def test_amount_above_recovery_limit_is_not_eligible():
    """
    Amount > MAX_RECOVERY_AMOUNT (50_000) is NOT eligible.
    Expected: NOT ELIGIBLE, reason=amount_above_recovery_limit
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=MAX_RECOVERY_AMOUNT + 0.01,
        retry_count=0,
        subscription_status="active",
    )
    assert result.eligible is False
    assert result.reason == "amount_above_recovery_limit"


def test_amount_at_recovery_limit_is_eligible():
    """
    Amount == MAX_RECOVERY_AMOUNT (50_000) is still eligible.
    """
    result = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="temporary_bank_failure",
        amount=MAX_RECOVERY_AMOUNT,
        retry_count=0,
        subscription_status="active",
    )
    assert result.eligible is True


# ============================================================
# GUARDRAIL: ineligible payments must NEVER get RETRY_PAYMENT
# ============================================================

def test_guardrail_ineligible_never_gets_retry_action():
    """
    CRITICAL: The decision engine must NEVER recommend RETRY_PAYMENT
    for an ineligible payment, regardless of other inputs.

    This is the core financial safety requirement.
    """
    decision = make_recovery_decision(
        eligible=False,
        amount=5000.00,
        recovery_probability=0.99,   # even with very high probability
        failure_reason="payment_method_issue",
        retry_count=0,
        subscription_status="active",
        lifetime_value=99999.00,
    )
    assert decision.eligible is False
    assert decision.recommended_action not in (
        "RETRY_PAYMENT",
        "RETRY_WITH_CAUTION",
    ), (
        f"GUARDRAIL VIOLATION: ineligible payment got action={decision.recommended_action}"
    )
    assert decision.recommended_action == "DO_NOT_RETRY"
    assert decision.recovery_probability == 0.0
    assert decision.expected_recovery_value == 0.0


def test_guardrail_halted_subscription_never_gets_retry():
    """
    Halted subscription ineligible -> never RETRY_PAYMENT.
    """
    from app.domain.recovery.eligibility import evaluate_recovery_eligibility

    eligibility = evaluate_recovery_eligibility(
        payment_status="failed",
        failure_reason="network_error",
        amount=2741.75,
        retry_count=1,
        subscription_status="halted",
    )
    assert eligibility.eligible is False

    decision = make_recovery_decision(
        eligible=eligibility.eligible,
        amount=2741.75,
        recovery_probability=0.85,
        failure_reason="network_error",
        retry_count=1,
        subscription_status="halted",
        lifetime_value=5000.00,
    )
    assert decision.recommended_action not in ("RETRY_PAYMENT", "RETRY_WITH_CAUTION")


# ============================================================
# Revenue calculation correctness
# ============================================================

def test_revenue_expected_recovery_value_formula():
    """
    expected_recovery_value must equal amount * recovery_probability.
    """
    amount = 28100.45
    prob   = 0.8876
    result = calculate_revenue_risk(amount=amount, recovery_probability=prob)

    expected = round(amount * prob, 2)
    assert abs(result.expected_recovery_value - expected) < 0.02, (
        f"Expected {expected}, got {result.expected_recovery_value}"
    )
    assert result.revenue_at_risk == amount


def test_revenue_risk_at_risk_equals_amount():
    """
    revenue_at_risk must always equal the payment amount.
    """
    for amount in [1000.00, 2580.63, 4274.20, 28100.45]:
        result = calculate_revenue_risk(
            amount=amount,
            recovery_probability=0.75,
        )
        assert result.revenue_at_risk == amount


# ============================================================
# Decision engine — action mapping
# ============================================================

def test_high_priority_eligible_gets_retry_payment():
    """
    Eligible + high expected value + high probability -> RETRY_PAYMENT.
    """
    decision = make_recovery_decision(
        eligible=True,
        amount=28100.45,
        recovery_probability=0.8876,
        failure_reason="temporary_bank_failure",
        retry_count=1,
        subscription_status="active",
        lifetime_value=3074.54,
    )
    assert decision.eligible is True
    assert decision.recommended_action == "RETRY_PAYMENT"
    assert decision.priority == "HIGH"
    assert decision.expected_recovery_value > 0


def test_ineligible_payment_gets_none_priority():
    """
    Ineligible payment must have NONE priority.
    """
    decision = make_recovery_decision(
        eligible=False,
        amount=1000.00,
        recovery_probability=0.0,
        failure_reason="payment_method_issue",
        retry_count=0,
        subscription_status="active",
        lifetime_value=1000.00,
    )
    assert decision.priority == "NONE"
