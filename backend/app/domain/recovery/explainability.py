"""
app/domain/recovery/explainability.py

Explainable Recovery Intelligence & Decision Transparency Engine.

This component is READ-ONLY and 100% DETERMINISTIC.
It consumes existing outputs from:
- Payment investigation
- Deterministic eligibility policy
- ML recovery prediction
- Revenue risk engine
- Deterministic decision engine

It does NOT make decisions, modify data, trigger actions, or execute transactions.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ============================================================
# Probability Band Constants
# ============================================================

PROBABILITY_HIGH_THRESHOLD   = 0.80
PROBABILITY_MEDIUM_THRESHOLD = 0.50

CONFIDENCE_HIGH   = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW    = "LOW"
CONFIDENCE_NA     = "NOT_APPLICABLE"


# ============================================================
# Dataclasses for Structured Explanation
# ============================================================

@dataclass
class DecisionTraceStep:
    """A single deterministic trace step in the recovery pipeline."""
    step: str
    status: str
    value: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExplanationFactor:
    """An individual factor contributing to eligibility or decision."""
    factor: str
    impact: str  # "positive" | "negative" | "neutral"
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EligibilityExplanation:
    eligible: bool
    summary: str
    factors: list[ExplanationFactor] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "summary": self.summary,
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class PredictionExplanation:
    recovery_probability: float | None
    confidence_level: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionExplanation:
    recommended_action: str
    priority: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FinancialImpact:
    revenue_at_risk: float
    expected_recovery_value: float
    currency: str = "INR"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryExplanationResult:
    payment_id: str
    eligibility_explanation: EligibilityExplanation
    prediction_explanation: PredictionExplanation
    decision_explanation: DecisionExplanation
    financial_impact: FinancialImpact
    decision_trace: list[DecisionTraceStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "eligibility_explanation": self.eligibility_explanation.to_dict(),
            "prediction_explanation": self.prediction_explanation.to_dict(),
            "decision_explanation": self.decision_explanation.to_dict(),
            "financial_impact": self.financial_impact.to_dict(),
            "decision_trace": [t.to_dict() for t in self.decision_trace],
        }


# ============================================================
# Deterministic Probability Interpretation
# ============================================================

def interpret_probability_confidence(probability: float | None) -> str:
    """
    Interpret probability into deterministic confidence bands.
    
    0.80 to 1.00 -> HIGH
    0.50 to 0.79 -> MEDIUM
    0.00 to 0.49 -> LOW
    None         -> NOT_APPLICABLE
    """
    if probability is None:
        return CONFIDENCE_NA
    
    p = float(probability)
    if p >= PROBABILITY_HIGH_THRESHOLD:
        return CONFIDENCE_HIGH
    elif p >= PROBABILITY_MEDIUM_THRESHOLD:
        return CONFIDENCE_MEDIUM
    else:
        return CONFIDENCE_LOW


# ============================================================
# Explainability Engine
# ============================================================

class RecoveryExplainabilityEngine:
    """
    Consumes outputs of the existing deterministic recovery pipeline
    and produces an explainable, auditable narrative and decision trace.
    """

    def explain(self, investigation_result: dict[str, Any]) -> RecoveryExplanationResult:
        payment_id = str(investigation_result.get("payment_id", ""))
        payment_raw = investigation_result.get("payment") or {}
        eligibility_raw = investigation_result.get("eligibility") or {}
        prediction_raw = investigation_result.get("prediction") or {}
        revenue_raw = investigation_result.get("revenue_risk") or {}
        decision_raw = investigation_result.get("decision") or {}

        eligible = bool(eligibility_raw.get("eligible", False))
        eligibility_reason = str(eligibility_raw.get("reason", "unknown"))

        amount = float(payment_raw.get("amount", 0.0) or 0.0)
        currency = str(payment_raw.get("currency", "INR") or "INR")
        failure_reason = str(payment_raw.get("failure_reason", "") or "")
        retry_count = int(payment_raw.get("retry_count", 0) or 0)
        subscription_status = str(payment_raw.get("subscription_status", "") or "")
        payment_status = str(payment_raw.get("payment_status", "failed") or "failed")

        # Probability
        recovery_prob: float | None = None
        if eligible:
            if prediction_raw.get("recovery_probability") is not None:
                recovery_prob = float(prediction_raw["recovery_probability"])
            elif decision_raw.get("recovery_probability") is not None:
                recovery_prob = float(decision_raw["recovery_probability"])

        # Revenue
        revenue_at_risk = float(
            revenue_raw.get("revenue_at_risk")
            or decision_raw.get("revenue_at_risk")
            or amount
        )
        expected_recovery = float(
            revenue_raw.get("expected_recovery_value")
            or decision_raw.get("expected_recovery_value")
            or (amount * recovery_prob if recovery_prob is not None else 0.0)
        )

        priority = str(decision_raw.get("priority", "NONE"))
        recommended_action = str(decision_raw.get("recommended_action", "DO_NOT_RETRY" if not eligible else "DEFER_RECOVERY"))

        # 1. Build Eligibility Explanation
        elig_explanation = self._build_eligibility_explanation(
            eligible=eligible,
            reason=eligibility_reason,
            failure_reason=failure_reason,
            payment_status=payment_status,
            retry_count=retry_count,
            subscription_status=subscription_status,
            amount=amount,
        )

        # 2. Build Prediction Explanation
        pred_explanation = self._build_prediction_explanation(
            eligible=eligible,
            recovery_prob=recovery_prob,
        )

        # 3. Build Decision Explanation
        dec_explanation = self._build_decision_explanation(
            eligible=eligible,
            recommended_action=recommended_action,
            priority=priority,
            recovery_prob=recovery_prob,
            failure_reason=failure_reason,
            retry_count=retry_count,
        )

        # 4. Build Financial Impact
        financial_impact = FinancialImpact(
            revenue_at_risk=round(revenue_at_risk, 2),
            expected_recovery_value=round(expected_recovery, 2),
            currency=currency,
        )

        # 5. Build Decision Trace
        decision_trace = self._build_decision_trace(
            payment_id=payment_id,
            payment_status=payment_status,
            amount=amount,
            currency=currency,
            eligible=eligible,
            eligibility_reason=eligibility_reason,
            recovery_prob=recovery_prob,
            revenue_at_risk=revenue_at_risk,
            expected_recovery=expected_recovery,
            recommended_action=recommended_action,
            priority=priority,
        )

        return RecoveryExplanationResult(
            payment_id=payment_id,
            eligibility_explanation=elig_explanation,
            prediction_explanation=pred_explanation,
            decision_explanation=dec_explanation,
            financial_impact=financial_impact,
            decision_trace=decision_trace,
        )

    # --------------------------------------------------------
    # Private Helper Builders
    # --------------------------------------------------------

    def _build_eligibility_explanation(
        self,
        *,
        eligible: bool,
        reason: str,
        failure_reason: str,
        payment_status: str,
        retry_count: int,
        subscription_status: str,
        amount: float,
    ) -> EligibilityExplanation:
        factors: list[ExplanationFactor] = []

        if eligible:
            summary = "Payment is eligible for bounded recovery under deterministic policy."
            
            # Factor 1: Failure reason
            human_reason = failure_reason.replace("_", " ").title()
            if failure_reason in ("temporary_bank_failure", "network_error"):
                factors.append(ExplanationFactor(
                    factor=f"Transient Failure ({human_reason})",
                    impact="positive",
                    explanation="This failure reason indicates a transient network or banking issue that is potentially recoverable."
                ))
            elif failure_reason == "insufficient_funds":
                factors.append(ExplanationFactor(
                    factor=f"Customer Balance Issue ({human_reason})",
                    impact="positive",
                    explanation="Insufficient funds may be recovered once customer funds are replenished or payment reminder sent."
                ))
            else:
                factors.append(ExplanationFactor(
                    factor=f"Failure Reason ({human_reason})",
                    impact="positive",
                    explanation="The recorded failure code is permitted for automated evaluation."
                ))

            # Factor 2: Retry count
            factors.append(ExplanationFactor(
                factor=f"Retry Count ({retry_count}/2)",
                impact="positive",
                explanation=f"Retry count ({retry_count}) is within the deterministic policy threshold (max 2 retries)."
            ))

            # Factor 3: Subscription status
            if subscription_status:
                factors.append(ExplanationFactor(
                    factor=f"Subscription Status ({subscription_status.capitalize()})",
                    impact="positive",
                    explanation=f"Subscription is {subscription_status}, allowing recovery without customer churn conflict."
                ))

            # Factor 4: Amount check
            factors.append(ExplanationFactor(
                factor=f"Amount Check (₹{amount:,.2f})",
                impact="positive",
                explanation=f"Transaction amount is within the automatic safety ceiling (₹50,000)."
            ))

        else:
            summary = f"Recovery blocked: Deterministic policy rejected payment ({reason})."

            if reason == "payment_not_failed" or payment_status != "failed":
                factors.append(ExplanationFactor(
                    factor="Payment Status Not Failed",
                    impact="negative",
                    explanation=f"Payment status is '{payment_status}'. Only failed payments require revenue recovery."
                ))
            elif reason == "permanent_failure_reason":
                human_reason = failure_reason.replace("_", " ").title()
                factors.append(ExplanationFactor(
                    factor=f"Permanent Failure ({human_reason})",
                    impact="negative",
                    explanation=f"'{failure_reason}' is classified as a permanent failure. Retrying without customer remediation will fail and increase dispute risk."
                ))
            elif reason == "subscription_halted" or subscription_status == "halted":
                factors.append(ExplanationFactor(
                    factor="Subscription Halted",
                    impact="negative",
                    explanation="The associated subscription is halted. Automated recovery is disabled to prevent unauthorized billing."
                ))
            elif reason == "retry_limit_exceeded" or retry_count > 2:
                factors.append(ExplanationFactor(
                    factor=f"Retry Limit Exceeded ({retry_count} attempts)",
                    impact="negative",
                    explanation=f"Payment has reached {retry_count} retries (policy ceiling is 2). Further automated attempts are halted."
                ))
            elif reason == "amount_above_recovery_limit":
                factors.append(ExplanationFactor(
                    factor=f"Amount Exceeds Limit (₹{amount:,.2f})",
                    impact="negative",
                    explanation="Payment amount exceeds the maximum automatic recovery limit of ₹50,000."
                ))
            elif reason == "missing_failure_reason":
                factors.append(ExplanationFactor(
                    factor="Missing Failure Reason",
                    impact="negative",
                    explanation="No failure reason was provided. Automated recovery requires structured diagnostic codes."
                ))
            else:
                factors.append(ExplanationFactor(
                    factor=f"Policy Restriction ({reason})",
                    impact="negative",
                    explanation=f"Payment violates deterministic eligibility guardrail: {reason}."
                ))

        return EligibilityExplanation(
            eligible=eligible,
            summary=summary,
            factors=factors,
        )

    def _build_prediction_explanation(
        self,
        *,
        eligible: bool,
        recovery_prob: float | None,
    ) -> PredictionExplanation:
        if not eligible or recovery_prob is None:
            return PredictionExplanation(
                recovery_probability=None,
                confidence_level=CONFIDENCE_NA,
                summary="Recovery probability was not evaluated because this payment is blocked by eligibility policy."
            )

        conf = interpret_probability_confidence(recovery_prob)
        pct_str = f"{recovery_prob * 100:.1f}%"

        if conf == CONFIDENCE_HIGH:
            summary = f"The ML model predicts a {pct_str} likelihood of recovery (HIGH confidence), indicating strong historical recovery indicators."
        elif conf == CONFIDENCE_MEDIUM:
            summary = f"The ML model predicts a {pct_str} likelihood of recovery (MEDIUM confidence), warranting cautious recovery."
        else:
            summary = f"The ML model predicts a {pct_str} likelihood of recovery (LOW confidence), indicating low likelihood of automated recovery."

        return PredictionExplanation(
            recovery_probability=round(recovery_prob, 4),
            confidence_level=conf,
            summary=summary,
        )

    def _build_decision_explanation(
        self,
        *,
        eligible: bool,
        recommended_action: str,
        priority: str,
        recovery_prob: float | None,
        failure_reason: str,
        retry_count: int,
    ) -> DecisionExplanation:
        if not eligible:
            return DecisionExplanation(
                recommended_action="DO_NOT_RETRY",
                priority="NONE",
                summary="No recovery action permitted. Payment violates deterministic eligibility guardrails."
            )

        if recommended_action == "RETRY_PAYMENT":
            summary = (
                f"Deterministic decision engine recommends immediate bounded retry (Priority: {priority}). "
                f"High expected recovery value with favorable transient failure characteristics."
            )
        elif recommended_action == "RETRY_WITH_CAUTION":
            summary = (
                f"Deterministic decision engine recommends bounded retry with caution (Priority: {priority}). "
                f"Moderate recovery probability suggests one controlled attempt."
            )
        elif recommended_action == "SEND_PAYMENT_REMINDER":
            summary = (
                f"Customer outreach recommended ({recommended_action}). "
                f"Failure reason '{failure_reason}' requires customer action before retrying."
            )
        elif recommended_action == "ESCALATE_TO_HUMAN":
            summary = (
                f"Human review required ({recommended_action}). "
                f"Retry count ({retry_count}) or risk profile exceeds automated policy boundaries."
            )
        elif recommended_action == "DEFER_RECOVERY":
            summary = (
                f"Recovery deferred ({recommended_action}). "
                f"Low expected recovery value; automated retry postponed."
            )
        else:
            summary = f"Recommended action is {recommended_action} with priority {priority}."

        return DecisionExplanation(
            recommended_action=recommended_action,
            priority=priority,
            summary=summary,
        )

    def _build_decision_trace(
        self,
        *,
        payment_id: str,
        payment_status: str,
        amount: float,
        currency: str,
        eligible: bool,
        eligibility_reason: str,
        recovery_prob: float | None,
        revenue_at_risk: float,
        expected_recovery: float,
        recommended_action: str,
        priority: str,
    ) -> list[DecisionTraceStep]:
        trace: list[DecisionTraceStep] = []

        # Step 1: Payment Analysis
        trace.append(DecisionTraceStep(
            step="Payment Analysis",
            status="COMPLETE",
            value=f"{payment_id} ({payment_status.upper()})",
            explanation=f"Payment record loaded with amount {currency} {amount:,.2f}."
        ))

        # Step 2: Eligibility Check
        trace.append(DecisionTraceStep(
            step="Eligibility Check",
            status="PASS" if eligible else "BLOCKED",
            value="Eligible" if eligible else f"Blocked ({eligibility_reason})",
            explanation=(
                "Payment meets deterministic policy criteria."
                if eligible else
                f"Payment failed deterministic policy check: {eligibility_reason}."
            )
        ))

        # Step 3: Recovery Prediction
        if eligible and recovery_prob is not None:
            conf = interpret_probability_confidence(recovery_prob)
            trace.append(DecisionTraceStep(
                step="Recovery Prediction",
                status="COMPLETE",
                value=f"{recovery_prob * 100:.1f}% ({conf})",
                explanation=f"The calibrated ML model predicted {recovery_prob * 100:.1f}% recovery probability."
            ))
        else:
            trace.append(DecisionTraceStep(
                step="Recovery Prediction",
                status="SKIPPED",
                value="N/A",
                explanation="ML prediction skipped because recovery is blocked by eligibility policy."
            ))

        # Step 4: Revenue Risk
        trace.append(DecisionTraceStep(
            step="Revenue Risk",
            status="COMPLETE",
            value=f"₹{revenue_at_risk:,.2f} (EV: ₹{expected_recovery:,.2f})",
            explanation=f"Quantified revenue at risk of ₹{revenue_at_risk:,.2f} with ₹{expected_recovery:,.2f} expected recovery."
        ))

        # Step 5: Decision
        if not eligible:
            status_val = "BLOCKED"
        elif "RETRY" in recommended_action:
            status_val = "RECOMMENDED"
        elif recommended_action == "SEND_PAYMENT_REMINDER":
            status_val = "OUTREACH"
        elif recommended_action == "ESCALATE_TO_HUMAN":
            status_val = "ESCALATED"
        else:
            status_val = "DEFERRED"

        trace.append(DecisionTraceStep(
            step="Decision",
            status=status_val,
            value=f"{recommended_action} ({priority})",
            explanation=f"Deterministic decision engine evaluated priority as {priority} and recommended {recommended_action}."
        ))

        return trace
