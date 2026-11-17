"""
app/domain/recovery/batch.py

Batch Recovery Processor + Aggregate Metrics.

Processes a list of payment IDs through the full recovery pipeline:

    For each payment_id:
        RecoveryAgent.investigate()   — deterministic analysis
        RecoveryOrchestrator.execute() — bounded simulated execution
        AuditRecord                    — recorded for every payment

Aggregate metrics are calculated from the outcomes.

One failed payment NEVER crashes the entire batch.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from app.agents.recovery_agent import RecoveryAgent
from app.domain.recovery.decision_engine import RecoveryDecision
from app.domain.recovery.orchestrator import (
    RecoveryOrchestrator,
    OrchestrationResult,
)


# ============================================================
# Per-payment batch item result
# ============================================================

@dataclass
class BatchItemResult:
    payment_id:       str
    status:           str
    eligible:         bool
    recovery_probability: float | None
    revenue_at_risk:  float
    expected_recovery: float
    execution_status: str
    amount_recovered: float
    workflow_id:      str | None
    error:            str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Aggregate metrics
# ============================================================

@dataclass
class BatchMetrics:
    """
    Aggregate metrics across all payments in a batch.

    Definitions
    -----------
    recovery_rate =
        successful_recoveries / recovery_attempts   (0 if no attempts)

    revenue_recovery_rate =
        total_revenue_recovered / total_revenue_at_risk  (0 if no risk)
    """

    total_payments:         int   = 0
    eligible_payments:      int   = 0
    blocked_payments:       int   = 0
    deferred_payments:      int   = 0
    escalated_payments:     int   = 0
    recovery_attempts:      int   = 0
    successful_recoveries:  int   = 0
    failed_recoveries:      int   = 0
    stopped_workflows:      int   = 0
    errored_payments:       int   = 0

    total_revenue_at_risk:    float = 0.0
    total_expected_recovery:  float = 0.0
    total_revenue_recovered:  float = 0.0

    recovery_rate:        float = 0.0  # computed after collection
    revenue_recovery_rate: float = 0.0  # computed after collection

    def compute_rates(self) -> None:
        """Compute derived rate metrics. Call after all items are processed."""

        if self.recovery_attempts > 0:
            self.recovery_rate = round(
                self.successful_recoveries / self.recovery_attempts,
                4,
            )
        else:
            self.recovery_rate = 0.0

        if self.total_revenue_at_risk > 0:
            self.revenue_recovery_rate = round(
                self.total_revenue_recovered / self.total_revenue_at_risk,
                4,
            )
        else:
            self.revenue_recovery_rate = 0.0

        # Round money fields to 2 dp to avoid floating-point drift.
        self.total_revenue_at_risk = round(self.total_revenue_at_risk, 2)
        self.total_expected_recovery = round(self.total_expected_recovery, 2)
        self.total_revenue_recovered = round(self.total_revenue_recovered, 2)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Batch result (items + metrics)
# ============================================================

@dataclass
class BatchResult:
    items:   list[BatchItemResult] = field(default_factory=list)
    metrics: BatchMetrics = field(default_factory=BatchMetrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "metrics": self.metrics.to_dict(),
        }


# ============================================================
# Batch processor
# ============================================================

class RecoveryBatchProcessor:
    """
    Process a list of payment IDs through the full recovery pipeline.

    For each payment:
    1. Investigate (RecoveryAgent — deterministic)
    2. Execute bounded recovery (RecoveryOrchestrator)
    3. Record outcome

    One failure never crashes the batch.
    """

    def __init__(
        self,
        orchestrator: RecoveryOrchestrator | None = None,
    ) -> None:
        self._agent = RecoveryAgent()
        self._orchestrator = orchestrator or RecoveryOrchestrator()

    def process(
        self,
        payment_ids: list[str],
    ) -> BatchResult:
        """
        Process a list of payment IDs.

        Parameters
        ----------
        payment_ids : list[str]
            Payment IDs to process. Must be non-empty strings.

        Returns
        -------
        BatchResult
            Per-payment results and aggregate metrics.
        """

        result = BatchResult()
        metrics = result.metrics
        metrics.total_payments = len(payment_ids)

        for payment_id in payment_ids:
            try:
                item = self._process_one(payment_id)
            except Exception as exc:  # noqa: BLE001
                # One payment error must NOT crash the batch.
                item = BatchItemResult(
                    payment_id=payment_id,
                    status="error",
                    eligible=False,
                    recovery_probability=None,
                    revenue_at_risk=0.0,
                    expected_recovery=0.0,
                    execution_status="error",
                    amount_recovered=0.0,
                    workflow_id=None,
                    error=str(exc),
                )
                metrics.errored_payments += 1

            result.items.append(item)
            _update_metrics(metrics, item)

        metrics.compute_rates()
        return result

    def _process_one(
        self,
        payment_id: str,
    ) -> BatchItemResult:
        """Process one payment through investigate → execute."""

        # --- Investigate (deterministic) ---
        investigation = self._agent.investigate(payment_id)

        if investigation.get("status") == "failed" and not investigation.get("payment"):
            return BatchItemResult(
                payment_id=payment_id,
                status="not_found",
                eligible=False,
                recovery_probability=None,
                revenue_at_risk=0.0,
                expected_recovery=0.0,
                execution_status="not_found",
                amount_recovered=0.0,
                workflow_id=None,
                error="Payment not found.",
            )

        payment_raw    = investigation.get("payment") or {}
        eligibility    = investigation.get("eligibility") or {}
        prediction     = investigation.get("prediction") or {}
        revenue_risk   = investigation.get("revenue_risk") or {}
        decision_raw   = investigation.get("decision") or {}

        eligible = bool(eligibility.get("eligible", False))
        amount   = float(payment_raw.get("amount", 0.0))
        failure_reason = str(payment_raw.get("failure_reason", ""))
        retry_count    = int(payment_raw.get("retry_count", 0))

        recovery_prob  = (
            float(prediction.get("recovery_probability", 0.0))
            if prediction.get("recovery_probability") is not None
            else None
        )
        revenue_at_risk   = float(revenue_risk.get("revenue_at_risk", amount))
        expected_recovery = float(revenue_risk.get("expected_recovery_value", 0.0))

        # Build a RecoveryDecision from the raw dict for the orchestrator.
        decision = RecoveryDecision(
            eligible=bool(decision_raw.get("eligible", eligible)),
            recovery_probability=float(decision_raw.get("recovery_probability", 0.0)),
            revenue_at_risk=float(decision_raw.get("revenue_at_risk", amount)),
            expected_recovery_value=float(decision_raw.get("expected_recovery_value", 0.0)),
            priority=str(decision_raw.get("priority", "NONE")),
            recommended_action=str(decision_raw.get("recommended_action", "DO_NOT_RETRY")),
            reasons=list(decision_raw.get("reasons", [])),
        )

        # --- Execute (bounded orchestrator) ---
        exec_result: OrchestrationResult = self._orchestrator.execute(
            decision=decision,
            payment_id=payment_id,
            amount=amount,
            failure_reason=failure_reason,
            current_retry_count=retry_count,
        )

        return BatchItemResult(
            payment_id=payment_id,
            status=investigation.get("status", "unknown"),
            eligible=eligible,
            recovery_probability=recovery_prob,
            revenue_at_risk=revenue_at_risk,
            expected_recovery=expected_recovery,
            execution_status=exec_result.status,
            amount_recovered=exec_result.amount_recovered,
            workflow_id=exec_result.workflow_id,
            error=None,
        )


# ============================================================
# Metrics accumulator
# ============================================================

def _update_metrics(
    metrics: BatchMetrics,
    item: BatchItemResult,
) -> None:
    """Accumulate one item result into the running metrics."""

    if item.eligible:
        metrics.eligible_payments += 1
    else:
        metrics.blocked_payments += 1

    metrics.total_revenue_at_risk += item.revenue_at_risk
    metrics.total_expected_recovery += item.expected_recovery

    status = item.execution_status

    if status == "recovered":
        metrics.recovery_attempts += 1
        metrics.successful_recoveries += 1
        metrics.stopped_workflows += 1
        metrics.total_revenue_recovered += item.amount_recovered

    elif status == "failed":
        metrics.recovery_attempts += 1
        metrics.failed_recoveries += 1
        metrics.stopped_workflows += 1

    elif status == "deferred":
        metrics.deferred_payments += 1
        metrics.stopped_workflows += 1

    elif status == "escalated":
        metrics.escalated_payments += 1
        metrics.stopped_workflows += 1

    elif status in ("blocked", "not_found"):
        metrics.stopped_workflows += 1

    elif status == "error":
        pass  # already counted in errored_payments
