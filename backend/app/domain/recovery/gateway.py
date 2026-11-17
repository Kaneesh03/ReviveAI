"""
app/domain/recovery/gateway.py

Deterministic Payment Recovery Simulation Gateway.

THIS IS A SIMULATION / TEST MODE COMPONENT.
No real money is moved. No real payment APIs are called.

This gateway produces controlled, deterministic outcomes for
recovery attempts, making the demo fully reproducible.

Architecture position:
    RecoveryOrchestrator → PaymentRecoveryGateway → SimulatedOutcome

The gateway is NEVER accessible to the LLM or to user input.
It is called ONLY by the RecoveryOrchestrator after all
deterministic guardrails have been satisfied.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


# ============================================================
# Execution mode — always SIMULATION during development
# ============================================================

EXECUTION_MODE = "SIMULATION"


# ============================================================
# Deterministic simulation outcome table
#
# Maps failure_reason → whether a retry succeeds.
#
# These outcomes are fixed and deterministic so that the
# hackathon demo always produces the same results.
#
# NEVER use random() here. Demo reproducibility is required.
# ============================================================

SIMULATION_OUTCOMES: dict[str, bool] = {
    "temporary_bank_failure": True,    # Retry succeeds
    "network_error":          True,    # Retry succeeds
    "insufficient_funds":     False,   # Retry fails (funds not available)
}

# Failure reasons that must NEVER be attempted.
# The orchestrator enforces this, but we also check here as
# a defence-in-depth measure.
NEVER_EXECUTE_REASONS: set[str] = {
    "payment_method_issue",
    "repeated_failure",
    "unknown_failure",
}


# ============================================================
# Outcome model
# ============================================================

@dataclass
class GatewayOutcome:
    """Result of one simulated recovery attempt."""

    payment_id:       str
    attempt_number:   int
    success:          bool
    amount_recovered: float      # 0.0 if not successful
    failure_reason:   str | None  # reason retry failed, if any
    timestamp:        str
    mode:             str = EXECUTION_MODE

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id":       self.payment_id,
            "attempt_number":   self.attempt_number,
            "success":          self.success,
            "amount_recovered": self.amount_recovered,
            "failure_reason":   self.failure_reason,
            "timestamp":        self.timestamp,
            "mode":             self.mode,
        }


# ============================================================
# Gateway
# ============================================================

class PaymentRecoveryGateway:
    """
    Deterministic simulation gateway for payment recovery.

    This class simulates what a real payment retry would do,
    using a fixed outcome table rather than calling any
    real payment infrastructure.

    Called ONLY by RecoveryOrchestrator.
    Never accessible to the LLM.
    """

    def attempt_retry(
        self,
        *,
        payment_id:     str,
        amount:         float,
        failure_reason: str,
        attempt_number: int,
    ) -> GatewayOutcome:
        """
        Simulate one payment retry attempt.

        Parameters
        ----------
        payment_id : str
            The payment being retried.
        amount : float
            The original payment amount (full amount if recovered).
        failure_reason : str
            The original failure reason — used for outcome lookup.
        attempt_number : int
            Which attempt this is (1-indexed).

        Returns
        -------
        GatewayOutcome
            Deterministic simulated result.

        Raises
        ------
        ValueError
            If a permanently-failed payment is passed to this gateway.
            This should have been blocked by the orchestrator, but we
            add a defence-in-depth check here.
        """

        timestamp = datetime.now(timezone.utc).isoformat()

        # Defence-in-depth: never execute permanently blocked reasons.
        if failure_reason in NEVER_EXECUTE_REASONS:
            raise ValueError(
                f"PaymentRecoveryGateway refused to execute "
                f"payment {payment_id}: failure_reason "
                f"'{failure_reason}' is permanently blocked. "
                f"This is a programming error — the orchestrator "
                f"should have blocked this before reaching the gateway."
            )

        # Look up deterministic outcome.
        success = SIMULATION_OUTCOMES.get(failure_reason, False)

        return GatewayOutcome(
            payment_id=payment_id,
            attempt_number=attempt_number,
            success=success,
            amount_recovered=round(amount, 2) if success else 0.0,
            failure_reason=None if success else f"retry_failed:{failure_reason}",
            timestamp=timestamp,
            mode=EXECUTION_MODE,
        )
