"""
app/domain/recovery/orchestrator.py

Recovery Orchestrator — Bounded Recovery Workflow Engine.

This is the ONLY component that may execute a payment recovery action.

Architecture position:
    RecoveryDecision (from decision_engine)
        ↓
    RecoveryOrchestrator  ← THIS FILE
        ↓ (only if ALL guardrails pass)
    PaymentRecoveryGateway (simulation)
        ↓
    WorkflowAuditRecord

CRITICAL SAFETY RULES:
1. The LLM has NO access to this component.
2. Eligibility is re-verified from the RecoveryDecision object —
   user-supplied data is never trusted.
3. Hard limits are enforced unconditionally.
4. Stopping rules are deterministic — no LLM can override them.
5. MAX_WORKFLOW_STEPS prevents infinite loops.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from app.domain.recovery.audit import (
    AuditEventType,
    WorkflowAuditRecord,
    save_audit_record,
)
from app.domain.recovery.decision_engine import RecoveryDecision
from app.domain.recovery.eligibility import MAX_RETRY_COUNT
from app.domain.recovery.gateway import (
    GatewayOutcome,
    PaymentRecoveryGateway,
    EXECUTION_MODE,
)


# ============================================================
# Hard safety limits
#
# These are defined once here and enforced unconditionally.
# They cannot be changed at runtime or by LLM instruction.
# ============================================================

MAX_RETRIES: int = MAX_RETRY_COUNT
MAX_WORKFLOW_STEPS: int = 3


# ============================================================
# Workflow status values
# ============================================================

class WorkflowStatus:
    PENDING     = "pending"
    ANALYZING   = "analyzing"
    BLOCKED     = "blocked"
    DEFERRED    = "deferred"
    ESCALATED   = "escalated"
    OUTREACH_REQUIRED = "outreach_required"
    ATTEMPTING  = "attempting"
    RECOVERED   = "recovered"
    FAILED      = "failed"
    STOPPED     = "stopped"


# ============================================================
# Orchestrator result
# ============================================================

@dataclass
class OrchestrationResult:
    """
    Structured result of a recovery workflow execution.

    Fields
    ------
    payment_id : str
    workflow_id : str
    action : str
        The action that was permitted (from decision.recommended_action).
    attempts : int
        How many execution attempts were made.
    status : str
        Final workflow status (see WorkflowStatus).
    success : bool
        Whether recovery was successful.
    amount_recovered : float
        Amount recovered (0.0 if not recovered).
    stopping_reason : str
        Human-readable reason the workflow stopped.
    escalated : bool
    stopped : bool
    mode : str
        Always "SIMULATION" during development.
    audit_events : list[dict]
        Serialized audit events for this workflow.
    """
    payment_id:       str
    workflow_id:      str
    action:           str
    attempts:         int
    status:           str
    success:          bool
    amount_recovered: float
    stopping_reason:  str
    escalated:        bool
    stopped:          bool
    mode:             str = EXECUTION_MODE
    audit_events:     list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Orchestrator
# ============================================================

class RecoveryOrchestrator:
    """
    Deterministic recovery workflow engine.

    Responsibilities:
    1. Receive an already-evaluated RecoveryDecision.
    2. Enforce all hard safety limits — no exceptions.
    3. Execute ONLY a bounded simulated retry if permitted.
    4. Record every event in the audit trail.
    5. Stop cleanly when a terminal condition is reached.

    The LLM is never involved in this workflow.
    """

    def __init__(
        self,
        gateway: PaymentRecoveryGateway | None = None,
    ) -> None:
        self._gateway = gateway or PaymentRecoveryGateway()

    def execute(
        self,
        *,
        decision: RecoveryDecision,
        payment_id: str,
        amount: float,
        failure_reason: str,
        current_retry_count: int,
    ) -> OrchestrationResult:
        """
        Execute the bounded recovery workflow for one payment.

        Parameters
        ----------
        decision : RecoveryDecision
            The pre-computed deterministic decision.
            This object's `eligible` field is authoritative.
        payment_id : str
        amount : float
        failure_reason : str
        current_retry_count : int
            The retry count already present on the payment record.

        Returns
        -------
        OrchestrationResult
        """

        workflow_id = _new_workflow_id()
        now = datetime.now(timezone.utc).isoformat()

        audit = WorkflowAuditRecord(
            workflow_id=workflow_id,
            payment_id=payment_id,
            created_at=now,
            eligible=decision.eligible,
            eligibility_reason="" if decision.eligible else "not_eligible",
            recovery_probability=(
                decision.recovery_probability if decision.eligible else None
            ),
            revenue_at_risk=decision.revenue_at_risk,
            expected_recovery=decision.expected_recovery_value,
            decision_action=decision.recommended_action,
            decision_reasons=list(decision.reasons),
            priority=decision.priority,
            execution_mode=EXECUTION_MODE,
        )

        audit.add_event(
            AuditEventType.WORKFLOW_STARTED,
            {"payment_id": payment_id, "action": decision.recommended_action},
        )

        # --------------------------------------------------------
        # GUARDRAIL 1 — Eligibility (authoritative from decision)
        # --------------------------------------------------------

        if not decision.eligible:
            audit.add_event(
                AuditEventType.RECOVERY_BLOCKED,
                {"reason": "payment_not_eligible"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "ineligible"},
            )
            return self._blocked_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                stopping_reason="Payment is not eligible for recovery.",
                audit=audit,
            )

        audit.add_event(
            AuditEventType.ELIGIBILITY_VERIFIED,
            {"eligible": True},
        )

        # --------------------------------------------------------
        # GUARDRAIL 2 — Action-based stopping rules
        # --------------------------------------------------------

        action = decision.recommended_action

        audit.add_event(
            AuditEventType.DECISION_READY,
            {"action": action, "priority": decision.priority},
        )

        if action == "DO_NOT_RETRY":
            audit.add_event(
                AuditEventType.RECOVERY_BLOCKED,
                {"reason": "action_do_not_retry"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "action_do_not_retry"},
            )
            return self._blocked_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                stopping_reason="Decision engine recommended DO_NOT_RETRY.",
                audit=audit,
            )

        if action == "DEFER_RECOVERY":
            audit.add_event(
                AuditEventType.RECOVERY_DEFERRED,
                {"reason": "decision_deferred"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "deferred"},
            )
            return self._deferred_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                action=action,
                audit=audit,
            )

        if action == "ESCALATE_TO_HUMAN":
            audit.add_event(
                AuditEventType.RECOVERY_ESCALATED,
                {"reason": "action_escalate"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "escalated"},
            )
            return self._escalated_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                action=action,
                audit=audit,
            )

        if action == "SEND_PAYMENT_REMINDER":
            audit.add_event(
                AuditEventType.RECOVERY_OUTREACH_REQUIRED,
                {"reason": "action_outreach"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "outreach_required"},
            )
            return self._outreach_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                action=action,
                audit=audit,
            )

        # --------------------------------------------------------
        # GUARDRAIL 3 — Hard retry ceiling
        # --------------------------------------------------------

        if current_retry_count >= MAX_RETRIES:
            audit.add_event(
                AuditEventType.RETRY_LIMIT_REACHED,
                {"current_retry_count": current_retry_count, "max_retries": MAX_RETRIES},
            )
            audit.add_event(
                AuditEventType.RECOVERY_ESCALATED,
                {"reason": "retry_limit_exceeded"},
            )
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": "retry_limit_exceeded_escalated"},
            )
            return self._escalated_result(
                payment_id=payment_id,
                workflow_id=workflow_id,
                action=action,
                stopping_reason="Retry limit exceeded. Escalated for human review.",
                audit=audit,
            )

        # --------------------------------------------------------
        # EXECUTION — bounded simulation loop
        #
        # RETRY_PAYMENT and RETRY_WITH_CAUTION both attempt
        # exactly one retry in this MVP implementation.
        # MAX_WORKFLOW_STEPS caps infinite loops.
        # --------------------------------------------------------

        attempts = 0
        amount_recovered = 0.0
        final_status = WorkflowStatus.FAILED
        stopping_reason = ""

        for step in range(MAX_WORKFLOW_STEPS):

            attempts += 1
            attempt_number = step + 1

            audit.add_event(
                AuditEventType.ATTEMPT_STARTED,
                {
                    "attempt_number": attempt_number,
                    "max_attempts": MAX_WORKFLOW_STEPS,
                },
            )

            outcome: GatewayOutcome = self._gateway.attempt_retry(
                payment_id=payment_id,
                amount=amount,
                failure_reason=failure_reason,
                attempt_number=attempt_number,
            )

            if outcome.success:
                amount_recovered = outcome.amount_recovered
                final_status = WorkflowStatus.RECOVERED
                stopping_reason = "Recovery successful."
                audit.add_event(
                    AuditEventType.ATTEMPT_SUCCEEDED,
                    {
                        "attempt_number": attempt_number,
                        "amount_recovered": amount_recovered,
                    },
                )
                audit.add_event(
                    AuditEventType.WORKFLOW_COMPLETE,
                    {
                        "status": "recovered",
                        "amount_recovered": amount_recovered,
                    },
                )
                # Stop immediately on success.
                break

            else:
                audit.add_event(
                    AuditEventType.ATTEMPT_FAILED,
                    {
                        "attempt_number": attempt_number,
                        "failure_reason": outcome.failure_reason,
                    },
                )
                final_status = WorkflowStatus.FAILED
                stopping_reason = (
                    f"Recovery attempt {attempt_number} failed: "
                    f"{outcome.failure_reason}."
                )
                # In this MVP, one attempt per workflow.
                # Future: configurable retry loop.
                break

        if final_status == WorkflowStatus.FAILED:
            audit.add_event(
                AuditEventType.WORKFLOW_STOPPED,
                {"stopping_reason": stopping_reason},
            )

        # --------------------------------------------------------
        # Finalise audit record
        # --------------------------------------------------------

        audit.attempts = attempts
        audit.status = final_status
        audit.amount_recovered = amount_recovered
        audit.stopping_reason = stopping_reason
        audit.stopped = True

        save_audit_record(audit)

        return OrchestrationResult(
            payment_id=payment_id,
            workflow_id=workflow_id,
            action=action,
            attempts=attempts,
            status=final_status,
            success=final_status == WorkflowStatus.RECOVERED,
            amount_recovered=amount_recovered,
            stopping_reason=stopping_reason,
            escalated=False,
            stopped=True,
            mode=EXECUTION_MODE,
            audit_events=[e.to_dict() for e in audit.events],
        )

    # --------------------------------------------------------
    # Private result builders
    # --------------------------------------------------------

    def _blocked_result(
        self,
        *,
        payment_id: str,
        workflow_id: str,
        stopping_reason: str = "Payment is not eligible for recovery.",
        audit: WorkflowAuditRecord,
    ) -> OrchestrationResult:
        audit.status = WorkflowStatus.BLOCKED
        audit.stopping_reason = stopping_reason
        audit.stopped = True
        save_audit_record(audit)
        return OrchestrationResult(
            payment_id=payment_id,
            workflow_id=workflow_id,
            action="DO_NOT_RETRY",
            attempts=0,
            status=WorkflowStatus.BLOCKED,
            success=False,
            amount_recovered=0.0,
            stopping_reason=stopping_reason,
            escalated=False,
            stopped=True,
            mode=EXECUTION_MODE,
            audit_events=[e.to_dict() for e in audit.events],
        )

    def _deferred_result(
        self,
        *,
        payment_id: str,
        workflow_id: str,
        action: str,
        stopping_reason: str = "Recovery deferred. No immediate retry attempted.",
        audit: WorkflowAuditRecord,
    ) -> OrchestrationResult:
        audit.status = WorkflowStatus.DEFERRED
        audit.stopping_reason = stopping_reason
        audit.stopped = True
        save_audit_record(audit)
        return OrchestrationResult(
            payment_id=payment_id,
            workflow_id=workflow_id,
            action=action,
            attempts=0,
            status=WorkflowStatus.DEFERRED,
            success=False,
            amount_recovered=0.0,
            stopping_reason=stopping_reason,
            escalated=False,
            stopped=True,
            mode=EXECUTION_MODE,
            audit_events=[e.to_dict() for e in audit.events],
        )

    def _escalated_result(
        self,
        *,
        payment_id: str,
        workflow_id: str,
        action: str,
        stopping_reason: str = "Case escalated for human review.",
        audit: WorkflowAuditRecord,
    ) -> OrchestrationResult:
        audit.status = WorkflowStatus.ESCALATED
        audit.stopping_reason = stopping_reason
        audit.escalated = True
        audit.stopped = True
        save_audit_record(audit)
        return OrchestrationResult(
            payment_id=payment_id,
            workflow_id=workflow_id,
            action=action,
            attempts=0,
            status=WorkflowStatus.ESCALATED,
            success=False,
            amount_recovered=0.0,
            stopping_reason=stopping_reason,
            escalated=True,
            stopped=True,
            mode=EXECUTION_MODE,
            audit_events=[e.to_dict() for e in audit.events],
        )

    def _outreach_result(
        self,
        *,
        payment_id: str,
        workflow_id: str,
        action: str,
        stopping_reason: str = "Payment requires customer outreach (reminder).",
        audit: WorkflowAuditRecord,
    ) -> OrchestrationResult:
        audit.status = WorkflowStatus.OUTREACH_REQUIRED
        audit.stopping_reason = stopping_reason
        # Escalate visually in the UI, but it's specifically for outreach.
        audit.escalated = True 
        audit.stopped = True
        save_audit_record(audit)
        return OrchestrationResult(
            payment_id=payment_id,
            workflow_id=workflow_id,
            action=action,
            attempts=0,
            status=WorkflowStatus.OUTREACH_REQUIRED,
            success=False,
            amount_recovered=0.0,
            stopping_reason=stopping_reason,
            escalated=True,
            stopped=True,
            mode=EXECUTION_MODE,
            audit_events=[e.to_dict() for e in audit.events],
        )


# ============================================================
# Helpers
# ============================================================

def _new_workflow_id() -> str:
    return f"wf_{uuid.uuid4().hex[:12]}"
