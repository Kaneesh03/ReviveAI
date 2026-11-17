"""
app/domain/recovery/audit.py

Structured audit trail for recovery workflows.

Every significant event in a recovery workflow is recorded here.

The audit trail is designed to answer:
    WHO/WHAT acted?          → recovery_orchestrator (deterministic)
    WHY?                     → see reason / eligibility fields
    ON WHICH PAYMENT?        → payment_id
    WHAT WAS THE DECISION?   → decision_action
    WHAT ACTION WAS TAKEN?   → execution_action
    WHAT HAPPENED?           → outcome / status
    WHY DID THE WORKFLOW STOP? → stopping_reason

No secrets are exposed in audit records.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ============================================================
# Event types
# ============================================================

class AuditEventType:
    WORKFLOW_STARTED          = "workflow_started"
    ELIGIBILITY_VERIFIED      = "eligibility_verified"
    DECISION_READY            = "decision_ready"
    RECOVERY_BLOCKED          = "recovery_blocked"
    RECOVERY_DEFERRED         = "recovery_deferred"
    RECOVERY_ESCALATED        = "recovery_escalated"
    RECOVERY_OUTREACH_REQUIRED = "recovery_outreach_required"
    ATTEMPT_STARTED           = "attempt_started"
    ATTEMPT_SUCCEEDED         = "attempt_succeeded"
    ATTEMPT_FAILED            = "attempt_failed"
    RETRY_LIMIT_REACHED       = "retry_limit_reached"
    WORKFLOW_STOPPED          = "workflow_stopped"
    WORKFLOW_COMPLETE         = "workflow_complete"


# ============================================================
# Audit event
# ============================================================

@dataclass
class AuditEvent:
    """One timestamped audit event in a recovery workflow."""

    workflow_id:    str
    payment_id:     str
    event_type:     str
    timestamp:      str
    details:        dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Audit record (full workflow)
# ============================================================

@dataclass
class WorkflowAuditRecord:
    """
    Complete audit record for one recovery workflow.

    Answers every auditability requirement:
    - Who/what acted: always 'recovery_orchestrator'
    - Why: eligibility_reason + decision_reasons
    - On which payment: payment_id
    - Decision: decision_action
    - Action attempted: execution_action
    - Outcome: status + amount_recovered
    - Why stopped: stopping_reason
    """

    workflow_id:          str
    payment_id:           str
    created_at:           str
    actor:                str = "recovery_orchestrator"

    # Eligibility
    eligible:             bool = False
    eligibility_reason:   str = ""

    # Recovery analysis (populated for eligible payments only)
    recovery_probability: float | None = None
    revenue_at_risk:      float = 0.0
    expected_recovery:    float = 0.0

    # Decision
    decision_action:      str = ""
    decision_reasons:     list[str] = field(default_factory=list)
    priority:             str = "NONE"

    # Execution
    execution_action:     str = ""
    attempts:             int = 0
    status:               str = "pending"
    amount_recovered:     float = 0.0
    stopping_reason:      str = ""
    escalated:            bool = False
    stopped:              bool = False

    # Execution mode (always SIMULATION during development)
    execution_mode:       str = "SIMULATION"

    # Individual events
    events:               list[AuditEvent] = field(default_factory=list)

    def add_event(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            AuditEvent(
                workflow_id=self.workflow_id,
                payment_id=self.payment_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details=details or {},
            )
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # events are already dicts via asdict
        return d


# ============================================================
# In-memory audit store
#
# For MVP/demo: stores workflow records in memory.
# Production would persist to MongoDB.
# ============================================================

_audit_store: dict[str, WorkflowAuditRecord] = {}


def save_audit_record(record: WorkflowAuditRecord) -> None:
    _audit_store[record.workflow_id] = record


def get_audit_record(workflow_id: str) -> WorkflowAuditRecord | None:
    return _audit_store.get(workflow_id)


def get_all_audit_records() -> list[WorkflowAuditRecord]:
    return list(_audit_store.values())


def clear_audit_store() -> None:
    """Clear all records — used only in tests."""
    _audit_store.clear()
