"""
tests/test_orchestrator.py

Comprehensive tests for the Phase 6 execution layer:
- RecoveryOrchestrator (stopping rules, guardrails, outcomes)
- PaymentRecoveryGateway (simulation outcomes, defence-in-depth)
- RecoveryBatchProcessor (batch processing, metrics, error isolation)
- AuditTrail (event recording)

Tests prove that the LLM cannot override deterministic policy.
"""
from __future__ import annotations

import pytest

from app.domain.recovery.audit import (
    clear_audit_store,
    get_audit_record,
    AuditEventType,
)
from app.domain.recovery.batch import (
    BatchMetrics,
    RecoveryBatchProcessor,
)
from app.domain.recovery.decision_engine import RecoveryDecision
from app.domain.recovery.gateway import (
    PaymentRecoveryGateway,
    NEVER_EXECUTE_REASONS,
    SIMULATION_OUTCOMES,
    EXECUTION_MODE,
)
from app.domain.recovery.orchestrator import (
    RecoveryOrchestrator,
    MAX_RETRIES,
    MAX_WORKFLOW_STEPS,
    WorkflowStatus,
)


# ============================================================
# Helpers
# ============================================================

def _eligible_decision(
    action: str = "RETRY_PAYMENT",
    prob: float = 0.88,
    amount: float = 28100.45,
) -> RecoveryDecision:
    """Build an eligible RecoveryDecision."""
    return RecoveryDecision(
        eligible=True,
        recovery_probability=prob,
        revenue_at_risk=amount,
        expected_recovery_value=round(amount * prob, 2),
        priority="HIGH",
        recommended_action=action,
        reasons=["High probability.", "High value."],
    )


def _ineligible_decision(amount: float = 2942.43) -> RecoveryDecision:
    """Build an ineligible RecoveryDecision."""
    return RecoveryDecision(
        eligible=False,
        recovery_probability=0.0,
        revenue_at_risk=amount,
        expected_recovery_value=0.0,
        priority="NONE",
        recommended_action="DO_NOT_RETRY",
        reasons=["Payment is not recovery eligible."],
    )


@pytest.fixture(autouse=True)
def clear_audit():
    """Reset audit store before each test."""
    clear_audit_store()
    yield
    clear_audit_store()


# ============================================================
# PaymentRecoveryGateway tests
# ============================================================

class TestPaymentRecoveryGateway:

    def test_temporary_bank_failure_succeeds(self):
        """Simulation outcome: temporary_bank_failure → success."""
        gw = PaymentRecoveryGateway()
        outcome = gw.attempt_retry(
            payment_id="pay_test",
            amount=1000.0,
            failure_reason="temporary_bank_failure",
            attempt_number=1,
        )
        assert outcome.success is True
        assert outcome.amount_recovered == 1000.0
        assert outcome.mode == EXECUTION_MODE

    def test_network_error_succeeds(self):
        """Simulation outcome: network_error → success."""
        gw = PaymentRecoveryGateway()
        outcome = gw.attempt_retry(
            payment_id="pay_test",
            amount=500.0,
            failure_reason="network_error",
            attempt_number=1,
        )
        assert outcome.success is True
        assert outcome.amount_recovered == 500.0

    def test_insufficient_funds_fails(self):
        """Simulation outcome: insufficient_funds → failure."""
        gw = PaymentRecoveryGateway()
        outcome = gw.attempt_retry(
            payment_id="pay_test",
            amount=2000.0,
            failure_reason="insufficient_funds",
            attempt_number=1,
        )
        assert outcome.success is False
        assert outcome.amount_recovered == 0.0

    def test_gateway_rejects_permanent_failure_reasons(self):
        """Defence-in-depth: gateway raises ValueError for permanently blocked reasons."""
        gw = PaymentRecoveryGateway()
        for reason in NEVER_EXECUTE_REASONS:
            with pytest.raises(ValueError, match="permanently blocked"):
                gw.attempt_retry(
                    payment_id="pay_test",
                    amount=500.0,
                    failure_reason=reason,
                    attempt_number=1,
                )

    def test_outcome_amount_is_correct(self):
        """Amount recovered equals original amount on success."""
        gw = PaymentRecoveryGateway()
        outcome = gw.attempt_retry(
            payment_id="pay_test",
            amount=28100.45,
            failure_reason="temporary_bank_failure",
            attempt_number=1,
        )
        assert outcome.amount_recovered == 28100.45


# ============================================================
# RecoveryOrchestrator — Stopping rule tests
# ============================================================

class TestRecoveryOrchestratorStoppingRules:

    def _run(
        self,
        decision: RecoveryDecision,
        failure_reason: str = "temporary_bank_failure",
        retry_count: int = 0,
    ):
        orch = RecoveryOrchestrator()
        return orch.execute(
            decision=decision,
            payment_id="pay_test",
            amount=1000.0,
            failure_reason=failure_reason,
            current_retry_count=retry_count,
        )

    def test_ineligible_payment_is_blocked(self):
        """Ineligible payment → BLOCKED, zero attempts."""
        result = self._run(_ineligible_decision())
        assert result.status == WorkflowStatus.BLOCKED
        assert result.attempts == 0
        assert result.amount_recovered == 0.0
        assert result.success is False

    def test_do_not_retry_action_executes_zero_attempts(self):
        """DO_NOT_RETRY action → zero attempts, even if eligible=True."""
        decision = _eligible_decision(action="DO_NOT_RETRY")
        result = self._run(decision)
        assert result.status == WorkflowStatus.BLOCKED
        assert result.attempts == 0

    def test_defer_recovery_executes_zero_immediate_retries(self):
        """DEFER_RECOVERY → zero immediate attempts, deferred status."""
        decision = _eligible_decision(action="DEFER_RECOVERY")
        result = self._run(decision)
        assert result.status == WorkflowStatus.DEFERRED
        assert result.attempts == 0
        assert result.success is False

    def test_escalate_executes_zero_automatic_retries(self):
        """ESCALATE_TO_HUMAN → zero automatic retries, escalated status."""
        decision = _eligible_decision(action="ESCALATE_TO_HUMAN")
        result = self._run(decision)
        assert result.status == WorkflowStatus.ESCALATED
        assert result.attempts == 0
        assert result.escalated is True

    def test_retry_limit_exceeded_triggers_escalation(self):
        """retry_count >= MAX_RETRIES → escalated, zero new attempts."""
        decision = _eligible_decision()
        result = self._run(decision, retry_count=MAX_RETRIES)
        assert result.status == WorkflowStatus.ESCALATED
        assert result.escalated is True
        assert result.attempts == 0

    def test_successful_retry_stops_workflow(self):
        """Successful retry → RECOVERED, workflow stops immediately."""
        decision = _eligible_decision(action="RETRY_PAYMENT")
        result = self._run(decision, failure_reason="temporary_bank_failure")
        assert result.status == WorkflowStatus.RECOVERED
        assert result.success is True
        assert result.stopped is True

    def test_successful_retry_amount_is_correct(self):
        """Amount recovered equals the full payment amount on success."""
        decision = _eligible_decision(action="RETRY_PAYMENT", amount=28100.45)
        orch = RecoveryOrchestrator()
        result = orch.execute(
            decision=decision,
            payment_id="pay_002610",
            amount=28100.45,
            failure_reason="temporary_bank_failure",
            current_retry_count=0,
        )
        assert result.amount_recovered == 28100.45

    def test_failed_retry_reports_zero_recovered(self):
        """Failed retry → zero amount recovered."""
        decision = _eligible_decision(action="RETRY_PAYMENT")
        result = self._run(decision, failure_reason="insufficient_funds")
        assert result.status == WorkflowStatus.FAILED
        assert result.amount_recovered == 0.0
        assert result.success is False

    def test_retry_with_caution_also_succeeds_for_temp_failure(self):
        """RETRY_WITH_CAUTION also routes through gateway for eligible payments."""
        decision = _eligible_decision(action="RETRY_WITH_CAUTION")
        result = self._run(decision, failure_reason="temporary_bank_failure")
        assert result.status == WorkflowStatus.RECOVERED
        assert result.success is True

    def test_permanent_failure_reason_never_reaches_gateway(self):
        """
        Even if eligible=True somehow, a permanent failure reason that
        would pass orchestrator action checks should be blocked by the
        gateway's defence-in-depth check.
        """
        # payment_method_issue is in PERMANENT_FAILURE_REASONS so eligibility
        # engine correctly marks it ineligible. Test confirms even a
        # manually-constructed eligible=True decision cannot bypass gateway.
        decision = RecoveryDecision(
            eligible=True,
            recovery_probability=0.9,
            revenue_at_risk=1000.0,
            expected_recovery_value=900.0,
            priority="HIGH",
            recommended_action="RETRY_PAYMENT",
            reasons=["test"],
        )
        # payment_method_issue would be caught by gateway defence-in-depth
        with pytest.raises(ValueError, match="permanently blocked"):
            orch = RecoveryOrchestrator()
            orch.execute(
                decision=decision,
                payment_id="pay_test",
                amount=1000.0,
                failure_reason="payment_method_issue",
                current_retry_count=0,
            )

    def test_halted_subscription_is_blocked(self):
        """
        Halted subscription payments are blocked by eligibility engine,
        producing an ineligible decision which the orchestrator blocks.
        """
        # Simulate what the eligibility engine would produce
        decision = _ineligible_decision()
        result = self._run(decision, failure_reason="network_error")
        assert result.status == WorkflowStatus.BLOCKED
        assert result.attempts == 0


# ============================================================
# Audit trail tests
# ============================================================

class TestAuditTrail:

    def test_audit_record_created_for_blocked_payment(self):
        """Audit record is saved for every blocked workflow."""
        orch = RecoveryOrchestrator()
        result = orch.execute(
            decision=_ineligible_decision(),
            payment_id="pay_audit_test",
            amount=1000.0,
            failure_reason="payment_method_issue",
            current_retry_count=0,
        )
        record = get_audit_record(result.workflow_id)
        assert record is not None
        assert record.payment_id == "pay_audit_test"
        assert record.stopped is True

    def test_audit_record_created_for_recovered_payment(self):
        """Audit record is saved for successful recovery."""
        orch = RecoveryOrchestrator()
        result = orch.execute(
            decision=_eligible_decision(),
            payment_id="pay_audit_success",
            amount=5000.0,
            failure_reason="temporary_bank_failure",
            current_retry_count=0,
        )
        record = get_audit_record(result.workflow_id)
        assert record is not None
        assert record.amount_recovered == 5000.0

    def test_audit_events_contain_workflow_started(self):
        """Every workflow generates a WORKFLOW_STARTED audit event."""
        orch = RecoveryOrchestrator()
        result = orch.execute(
            decision=_eligible_decision(),
            payment_id="pay_events_test",
            amount=1000.0,
            failure_reason="network_error",
            current_retry_count=0,
        )
        event_types = [e["event_type"] for e in result.audit_events]
        assert AuditEventType.WORKFLOW_STARTED in event_types

    def test_audit_events_contain_workflow_complete_on_success(self):
        """Successful recovery generates WORKFLOW_COMPLETE event."""
        orch = RecoveryOrchestrator()
        result = orch.execute(
            decision=_eligible_decision(),
            payment_id="pay_complete_test",
            amount=1000.0,
            failure_reason="temporary_bank_failure",
            current_retry_count=0,
        )
        event_types = [e["event_type"] for e in result.audit_events]
        assert AuditEventType.WORKFLOW_COMPLETE in event_types


# ============================================================
# Batch processor tests
# ============================================================

class TestRecoveryBatchProcessor:

    DEMO_BATCH = [
        "pay_002610",  # temp bank failure, eligible → recovered
        "pay_000041",  # temp bank failure, eligible → recovered
        "pay_000039",  # network error, eligible → deferred (low priority)
        "pay_000012",  # insufficient funds, eligible → deferred (low priority)
        "pay_000016",  # payment_method_issue, ineligible → blocked
        "pay_000049",  # repeated_failure, ineligible → blocked
        "pay_000116",  # unknown_failure, ineligible → blocked
        "pay_000040",  # halted subscription, ineligible → blocked
        "pay_000062",  # retry limit exceeded, ineligible → blocked
    ]

    def test_batch_processes_all_payments(self):
        """Batch processes all 9 demo payment IDs."""
        processor = RecoveryBatchProcessor()
        result = processor.process(self.DEMO_BATCH)
        assert result.metrics.total_payments == 9
        assert len(result.items) == 9

    def test_batch_metrics_eligible_and_blocked_counts(self):
        """Demo batch has 4 eligible and 5 blocked payments."""
        processor = RecoveryBatchProcessor()
        result = processor.process(self.DEMO_BATCH)
        m = result.metrics
        assert m.eligible_payments == 4
        assert m.blocked_payments == 5

    def test_batch_recovery_attempts_are_nonzero(self):
        """At least one recovery attempt is made for eligible payments."""
        processor = RecoveryBatchProcessor()
        result = processor.process(self.DEMO_BATCH)
        assert result.metrics.recovery_attempts > 0

    def test_batch_total_revenue_recovered_is_positive(self):
        """Batch recovers a positive amount from successful retries."""
        processor = RecoveryBatchProcessor()
        result = processor.process(self.DEMO_BATCH)
        assert result.metrics.total_revenue_recovered > 0.0

    def test_batch_unknown_payment_does_not_crash_batch(self):
        """Unknown payment ID returns not_found item, batch continues."""
        processor = RecoveryBatchProcessor()
        result = processor.process(["pay_002610", "pay_DOES_NOT_EXIST", "pay_000016"])
        assert result.metrics.total_payments == 3
        statuses = [item.execution_status for item in result.items]
        assert "not_found" in statuses
        # Other payments still processed correctly
        assert any(item.payment_id == "pay_002610" for item in result.items)

    def test_batch_recovery_rate_formula(self):
        """recovery_rate = successful_recoveries / recovery_attempts."""
        processor = RecoveryBatchProcessor()
        result = processor.process(self.DEMO_BATCH)
        m = result.metrics
        if m.recovery_attempts > 0:
            expected_rate = round(
                m.successful_recoveries / m.recovery_attempts, 4
            )
            assert m.recovery_rate == expected_rate
        else:
            assert m.recovery_rate == 0.0

    def test_batch_zero_division_safe(self):
        """Metrics compute_rates handles zero division safely."""
        metrics = BatchMetrics()
        metrics.recovery_attempts = 0
        metrics.total_revenue_at_risk = 0.0
        metrics.compute_rates()
        assert metrics.recovery_rate == 0.0
        assert metrics.revenue_recovery_rate == 0.0

    def test_batch_blocked_payments_have_zero_amount_recovered(self):
        """All blocked payments in the batch have amount_recovered = 0."""
        processor = RecoveryBatchProcessor()
        result = processor.process(["pay_000016", "pay_000040", "pay_000049"])
        for item in result.items:
            assert item.amount_recovered == 0.0
            assert item.eligible is False
