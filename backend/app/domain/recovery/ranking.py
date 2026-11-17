"""
app/domain/recovery/ranking.py

Deterministic Recovery Opportunity Ranking.

This module takes a list of payment investigation results
(from RecoveryAgent.investigate()) and returns them sorted
by recovery opportunity value.

Ranking criteria (in order of priority):
  1. Eligible payments always rank above blocked payments.
  2. Higher expected_recovery_value ranks higher.
  3. Higher recovery_probability ranks higher.
  4. Higher revenue_at_risk ranks higher.
  5. Existing deterministic priority (HIGH > MEDIUM > LOW > NONE).

No new ML model is introduced.
No LLM is involved.
All inputs come from the existing authoritative backend pipeline.

The ranking itself is a pure deterministic sort — the same
input always produces the same ranked output.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ============================================================
# Priority order for tie-breaking
# ============================================================

_PRIORITY_ORDER: dict[str, int] = {
    "HIGH":   0,
    "MEDIUM": 1,
    "LOW":    2,
    "NONE":   3,
}


# ============================================================
# Ranked opportunity model
# ============================================================

@dataclass
class RankedOpportunity:
    """
    A single ranked recovery opportunity.

    Fields
    ------
    rank : int
        1-based rank (1 = best opportunity).
        Blocked payments are ranked separately below eligible ones.
    payment_id : str
    amount : float
    currency : str
    failure_reason : str | None
    eligible : bool
    recovery_probability : float | None
        None for blocked payments (not calculated).
    revenue_at_risk : float
    expected_recovery_value : float
        0.0 for blocked payments.
    priority : str
        HIGH / MEDIUM / LOW / NONE
    recommended_action : str
    status : str
        "eligible" | "blocked"
    reasons : list[str]
        Authoritative reasons from the decision engine.
    """
    rank:                    int
    payment_id:              str
    amount:                  float
    currency:                str
    failure_reason:          str | None
    eligible:                bool
    recovery_probability:    float | None
    revenue_at_risk:         float
    expected_recovery_value: float
    priority:                str
    recommended_action:      str
    status:                  str
    reasons:                 list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Opportunity summary
# ============================================================

@dataclass
class OpportunitySummary:
    """
    Aggregate view of all ranked opportunities.

    Does NOT calculate any new business metrics.
    Values are derived from the per-opportunity results.
    """
    total_payments:          int   = 0
    eligible_payments:       int   = 0
    blocked_payments:        int   = 0
    total_revenue_at_risk:   float = 0.0
    total_expected_recovery: float = 0.0
    top_opportunity_id:      str | None = None
    top_opportunity_value:   float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# Ranking result
# ============================================================

@dataclass
class RankingResult:
    opportunities: list[RankedOpportunity] = field(default_factory=list)
    summary:       OpportunitySummary       = field(default_factory=OpportunitySummary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunities": [o.to_dict() for o in self.opportunities],
            "summary":       self.summary.to_dict(),
        }


# ============================================================
# Ranker
# ============================================================

class RecoveryOpportunityRanker:
    """
    Deterministic recovery opportunity ranker.

    Usage
    -----
    ranker = RecoveryOpportunityRanker()
    result = ranker.rank(investigation_results)

    Parameters
    ----------
    investigation_results : list[dict]
        Each dict is the output of RecoveryAgent.investigate()
        for one payment_id.  Missing or errored payments are
        handled gracefully.
    """

    def rank(
        self,
        investigation_results: list[dict[str, Any]],
    ) -> RankingResult:
        """
        Rank recovery opportunities from investigation results.

        The ranking is deterministic — the same inputs always
        produce the same output.

        Eligible payments always appear before blocked payments.
        Within each tier, payments are sorted by:
          1. expected_recovery_value (desc)
          2. recovery_probability (desc)
          3. revenue_at_risk (desc)
          4. priority (HIGH > MEDIUM > LOW > NONE)
        """

        raw_opps: list[RankedOpportunity] = []

        for inv in investigation_results:
            opp = _build_opportunity(inv)
            if opp is not None:
                raw_opps.append(opp)

        # --------------------------------------------------------
        # Sort: eligible first, then by value descending
        # --------------------------------------------------------
        sorted_opps = sorted(raw_opps, key=_sort_key)

        # Assign 1-based ranks
        for i, opp in enumerate(sorted_opps):
            opp.rank = i + 1

        # --------------------------------------------------------
        # Build summary
        # --------------------------------------------------------
        summary = _build_summary(sorted_opps)

        return RankingResult(
            opportunities=sorted_opps,
            summary=summary,
        )


# ============================================================
# Internal helpers
# ============================================================

def _build_opportunity(
    inv: dict[str, Any],
) -> RankedOpportunity | None:
    """
    Build a RankedOpportunity from one RecoveryAgent investigation result.
    Returns None for completely failed / not-found investigations.
    """

    payment_raw  = inv.get("payment") or {}
    eligibility  = inv.get("eligibility") or {}
    prediction   = inv.get("prediction") or {}
    revenue_risk = inv.get("revenue_risk") or {}
    decision_raw = inv.get("decision") or {}

    payment_id = inv.get("payment_id", "")

    # Skip entirely missing payments
    if not payment_raw and not decision_raw:
        return None

    eligible = bool(eligibility.get("eligible", False))

    amount   = float(payment_raw.get("amount", 0.0))
    currency = str(payment_raw.get("currency", "INR"))
    failure_reason_raw = payment_raw.get("failure_reason")
    failure_reason = (
        str(failure_reason_raw)
        if failure_reason_raw and str(failure_reason_raw).lower() not in ("nan", "none", "")
        else None
    )

    # Recovery probability — only meaningful for eligible payments
    recovery_prob: float | None = None
    if eligible and prediction.get("recovery_probability") is not None:
        recovery_prob = float(prediction["recovery_probability"])
    elif eligible and decision_raw.get("recovery_probability"):
        recovery_prob = float(decision_raw["recovery_probability"])

    revenue_at_risk = float(
        revenue_risk.get("revenue_at_risk")
        or decision_raw.get("revenue_at_risk")
        or amount
    )

    expected_recovery = float(
        revenue_risk.get("expected_recovery_value")
        or decision_raw.get("expected_recovery_value")
        or 0.0
    )

    priority = str(decision_raw.get("priority", "NONE"))
    recommended_action = str(decision_raw.get("recommended_action", "DO_NOT_RETRY"))
    reasons = list(decision_raw.get("reasons", []))

    status = "eligible" if eligible else "blocked"

    return RankedOpportunity(
        rank=0,  # assigned after sort
        payment_id=payment_id,
        amount=round(amount, 2),
        currency=currency,
        failure_reason=failure_reason,
        eligible=eligible,
        recovery_probability=round(recovery_prob, 4) if recovery_prob is not None else None,
        revenue_at_risk=round(revenue_at_risk, 2),
        expected_recovery_value=round(expected_recovery, 2),
        priority=priority,
        recommended_action=recommended_action,
        status=status,
        reasons=reasons,
    )


def _sort_key(opp: RankedOpportunity) -> tuple:
    """
    Deterministic sort key.

    Lower value = higher rank (closer to #1).

    Tier 0 = eligible, Tier 1 = blocked.
    Within eligible: highest expected_recovery_value first.
    Within blocked:  highest revenue_at_risk first.
    """
    tier = 0 if opp.eligible else 1
    priority_order = _PRIORITY_ORDER.get(opp.priority, 3)
    prob = opp.recovery_probability or 0.0

    return (
        tier,
        -opp.expected_recovery_value,
        -prob,
        -opp.revenue_at_risk,
        priority_order,
    )


def _build_summary(
    opps: list[RankedOpportunity],
) -> OpportunitySummary:
    """Aggregate summary from ranked list."""

    summary = OpportunitySummary()
    summary.total_payments = len(opps)

    for opp in opps:
        if opp.eligible:
            summary.eligible_payments += 1
            summary.total_expected_recovery += opp.expected_recovery_value
        else:
            summary.blocked_payments += 1
        summary.total_revenue_at_risk += opp.revenue_at_risk

    summary.total_revenue_at_risk   = round(summary.total_revenue_at_risk, 2)
    summary.total_expected_recovery = round(summary.total_expected_recovery, 2)

    if opps:
        top = opps[0]  # rank 1
        summary.top_opportunity_id    = top.payment_id
        summary.top_opportunity_value = top.expected_recovery_value

    return summary
