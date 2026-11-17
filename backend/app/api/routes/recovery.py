"""
app/api/routes/recovery.py

Endpoints:
  POST /api/v1/recovery/analyze       — deterministic investigation + LLM explanation
  POST /api/v1/recovery/execute       — bounded simulated recovery execution
  POST /api/v1/recovery/batch         — batch execution + aggregate metrics
  POST /api/v1/recovery/opportunities — deterministic recovery opportunity ranking

Architecture:
  LLM is involved ONLY in /analyze (narrative explanation).
  /execute, /batch, and /opportunities are 100% deterministic — LLM has no involvement.

Safety:
  The LLM never controls financial decisions.
  All eligibility, probability, and revenue values come from
  deterministic domain logic and the ML model.
  The RecoveryOrchestrator enforces all guardrails independently.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.llm.agent_loop import AgentLoop
from app.agents.llm.mock_provider import MockProvider
from app.agents.llm.prompts import SYSTEM_PROMPT
from app.agents.recovery_agent import RecoveryAgent
from app.agents.outreach_agent import OutreachAgent
from app.core.config import LLM_PROVIDER
from app.domain.recovery.audit import get_all_audit_records
from app.domain.recovery.batch import RecoveryBatchProcessor
from app.domain.recovery.decision_engine import RecoveryDecision
from app.domain.recovery.orchestrator import RecoveryOrchestrator
from app.domain.recovery.ranking import RecoveryOpportunityRanker
from app.domain.recovery.explainability import RecoveryExplainabilityEngine


router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"],
)


# ============================================================
# Provider factory
# ============================================================

def _get_provider():
    """
    Return the configured LLM provider.

    Defaults to MockProvider so the application works
    without external credentials.
    """

    if LLM_PROVIDER == "nvidia":
        try:
            from app.agents.llm.nvidia_provider import (
                NVIDIAProvider,
            )
            return NVIDIAProvider()

        except Exception as exc:
            # Fall back to MockProvider if NVIDIA is
            # misconfigured or unavailable.
            print(
                f"[WARNING] NVIDIA provider unavailable "
                f"({exc}). Falling back to MockProvider."
            )
            return MockProvider()

    return MockProvider()


# ============================================================
# Request schema
# ============================================================

class RecoveryRequest(BaseModel):
    payment_id: str = Field(
        ...,
        min_length=1,
        description="Payment ID to analyze",
        examples=["pay_002610"],
    )


# ============================================================
# Response schemas
# ============================================================

class PaymentInfo(BaseModel):
    payment_id: str
    amount: float | None = None
    currency: str | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    failure_reason: str | None = None
    retry_count: int | None = None
    subscription_status: str | None = None
    customer_age_days: int | None = None
    lifetime_value: float | None = None


class EligibilityInfo(BaseModel):
    eligible: bool
    reason: str


class PredictionInfo(BaseModel):
    recovery_probability: float


class RevenueRiskInfo(BaseModel):
    revenue_at_risk: float
    recovery_probability: float
    expected_recovery_value: float


class DecisionInfo(BaseModel):
    eligible: bool
    recovery_probability: float
    revenue_at_risk: float
    expected_recovery_value: float
    priority: str
    recommended_action: str
    reasons: list[str]


class AgentInfo(BaseModel):
    status: str
    iterations: int
    actions: list[dict[str, Any]]
    errors: list[str]
    explanation: str


class RecoveryAnalysisResponse(BaseModel):
    payment_id: str
    status: str  # "decision_complete" | "failed" | "not_found"

    payment: PaymentInfo | None = None
    eligibility: EligibilityInfo | None = None
    prediction: PredictionInfo | None = None
    revenue_risk: RevenueRiskInfo | None = None
    decision: DecisionInfo | None = None
    agent: AgentInfo | None = None


# ============================================================
# Endpoint
# ============================================================

@router.post(
    "/analyze",
    response_model=RecoveryAnalysisResponse,
    summary="Analyze a payment for recovery eligibility and recommendation",
)
def analyze_recovery(
    request: RecoveryRequest,
) -> RecoveryAnalysisResponse:
    """
    Full recovery analysis pipeline:

        Payment lookup
           ↓
        Eligibility check  (deterministic)
           ↓
        ML probability     (deterministic)
           ↓
        Revenue risk       (deterministic)
           ↓
        Decision engine    (deterministic)
           ↓
        LLM explanation    (language model)
    """

    payment_id = request.payment_id

    # --------------------------------------------------------
    # Step 1 — Deterministic investigation
    # --------------------------------------------------------

    agent = RecoveryAgent()
    investigation = agent.investigate(payment_id)

    # --------------------------------------------------------
    # Step 2 — Handle not-found case
    # --------------------------------------------------------

    if investigation.get("status") == "failed" and not investigation.get("payment"):
        raise HTTPException(
            status_code=404,
            detail=f"Payment '{payment_id}' not found.",
        )

    # --------------------------------------------------------
    # Step 3 — LLM narrative via AgentLoop
    # --------------------------------------------------------

    provider = _get_provider()
    loop = AgentLoop(provider=provider)

    loop_result = loop.run(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=(
            f"Analyze payment {payment_id} "
            f"and explain whether we should attempt recovery."
        ),
    )

    # --------------------------------------------------------
    # Step 4 — Build structured response
    # --------------------------------------------------------

    payment_raw = investigation.get("payment") or {}
    eligibility_raw = investigation.get("eligibility") or {}
    prediction_raw = investigation.get("prediction") or {}
    revenue_raw = investigation.get("revenue_risk") or {}
    decision_raw = investigation.get("decision") or {}

    # Payment info
    payment_info: PaymentInfo | None = None
    if payment_raw:
        payment_info = PaymentInfo(
            payment_id=payment_id,
            amount=_safe_float(payment_raw.get("amount")),
            currency=_safe_str(payment_raw.get("currency")),
            payment_method=_safe_str(payment_raw.get("payment_method")),
            payment_status=_safe_str(payment_raw.get("payment_status")),
            failure_reason=_safe_str(payment_raw.get("failure_reason")),
            retry_count=_safe_int(payment_raw.get("retry_count")),
            subscription_status=_safe_str(
                payment_raw.get("subscription_status")
            ),
            customer_age_days=_safe_int(payment_raw.get("customer_age_days")),
            lifetime_value=_safe_float(payment_raw.get("lifetime_value")),
        )

    # Eligibility
    eligibility_info: EligibilityInfo | None = None
    if eligibility_raw:
        eligibility_info = EligibilityInfo(
            eligible=bool(eligibility_raw.get("eligible", False)),
            reason=str(eligibility_raw.get("reason", "")),
        )

    # ML prediction
    prediction_info: PredictionInfo | None = None
    if prediction_raw and prediction_raw.get("success"):
        prediction_info = PredictionInfo(
            recovery_probability=float(
                prediction_raw.get("recovery_probability", 0.0)
            ),
        )

    # Revenue risk
    revenue_info: RevenueRiskInfo | None = None
    if revenue_raw and revenue_raw.get("success"):
        revenue_info = RevenueRiskInfo(
            revenue_at_risk=float(revenue_raw.get("revenue_at_risk", 0.0)),
            recovery_probability=float(
                revenue_raw.get("recovery_probability", 0.0)
            ),
            expected_recovery_value=float(
                revenue_raw.get("expected_recovery_value", 0.0)
            ),
        )

    # Decision
    decision_info: DecisionInfo | None = None
    if decision_raw:
        decision_info = DecisionInfo(
            eligible=bool(decision_raw.get("eligible", False)),
            recovery_probability=float(
                decision_raw.get("recovery_probability", 0.0)
            ),
            revenue_at_risk=float(decision_raw.get("revenue_at_risk", 0.0)),
            expected_recovery_value=float(
                decision_raw.get("expected_recovery_value", 0.0)
            ),
            priority=str(decision_raw.get("priority", "NONE")),
            recommended_action=str(
                decision_raw.get("recommended_action", "")
            ),
            reasons=list(decision_raw.get("reasons", [])),
        )

    # Agent narrative
    agent_info = AgentInfo(
        status=loop_result.get("status", ""),
        iterations=int(loop_result.get("iterations", 0)),
        actions=list(loop_result.get("actions", [])),
        errors=list(loop_result.get("errors", [])),
        explanation=str(loop_result.get("answer", "")),
    )

    return RecoveryAnalysisResponse(
        payment_id=payment_id,
        status=investigation.get("status", "unknown"),
        payment=payment_info,
        eligibility=eligibility_info,
        prediction=prediction_info,
        revenue_risk=revenue_info,
        decision=decision_info,
        agent=agent_info,
    )


# ============================================================
# Type coercion helpers — guard against NaN / None from CSV
# ============================================================

def _safe_float(value: Any) -> float | None:
    try:
        v = float(value)
        import math
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value)
    return None if s.lower() in {"nan", "none", ""} else s


# ============================================================
# POST /execute — Bounded recovery execution for one payment
#
# The LLM is NOT involved in this endpoint.
# ============================================================

class ExecuteRequest(BaseModel):
    payment_id: str = Field(
        ...,
        min_length=1,
        description="Payment ID to execute recovery for",
        examples=["pay_002610"],
    )


class ExecutionInfo(BaseModel):
    status: str
    attempts: int
    amount_recovered: float
    stopping_reason: str
    escalated: bool
    stopped: bool
    mode: str


class ExecuteResponse(BaseModel):
    payment_id: str
    workflow_id: str
    action: str
    execution: ExecutionInfo
    audit_events: list[dict[str, Any]]


@router.post(
    "/execute",
    response_model=ExecuteResponse,
    summary="Execute bounded recovery for one payment (SIMULATION MODE)",
)
def execute_recovery(
    request: ExecuteRequest,
) -> ExecuteResponse:
    """
    Execute a bounded, deterministic recovery workflow for one payment.

    This endpoint:
    1. Runs RecoveryAgent.investigate() to get the decision.
    2. Passes the decision to RecoveryOrchestrator (100% deterministic).
    3. The orchestrator enforces all guardrails and executes via
       PaymentRecoveryGateway (SIMULATION MODE — no real money).

    The LLM has NO involvement in this endpoint.
    """

    payment_id = request.payment_id

    # Step 1 — Deterministic investigation.
    agent = RecoveryAgent()
    investigation = agent.investigate(payment_id)

    if investigation.get("status") == "failed" and not investigation.get("payment"):
        raise HTTPException(
            status_code=404,
            detail=f"Payment '{payment_id}' not found.",
        )

    payment_raw  = investigation.get("payment") or {}
    decision_raw = investigation.get("decision") or {}

    # Build RecoveryDecision from the investigation result.
    decision = RecoveryDecision(
        eligible=bool(decision_raw.get("eligible", False)),
        recovery_probability=float(decision_raw.get("recovery_probability", 0.0)),
        revenue_at_risk=float(decision_raw.get("revenue_at_risk", 0.0)),
        expected_recovery_value=float(decision_raw.get("expected_recovery_value", 0.0)),
        priority=str(decision_raw.get("priority", "NONE")),
        recommended_action=str(decision_raw.get("recommended_action", "DO_NOT_RETRY")),
        reasons=list(decision_raw.get("reasons", [])),
    )

    # Step 2 — Bounded orchestrated execution.
    orchestrator = RecoveryOrchestrator()
    result = orchestrator.execute(
        decision=decision,
        payment_id=payment_id,
        amount=float(payment_raw.get("amount", 0.0)),
        failure_reason=str(payment_raw.get("failure_reason", "")),
        current_retry_count=int(payment_raw.get("retry_count", 0)),
    )

    return ExecuteResponse(
        payment_id=result.payment_id,
        workflow_id=result.workflow_id,
        action=result.action,
        execution=ExecutionInfo(
            status=result.status,
            attempts=result.attempts,
            amount_recovered=result.amount_recovered,
            stopping_reason=result.stopping_reason,
            escalated=result.escalated,
            stopped=result.stopped,
            mode=result.mode,
        ),
        audit_events=result.audit_events,
    )


# ============================================================
# POST /batch — Batch execution for multiple payments
#
# The LLM is NOT involved in this endpoint.
# ============================================================

class BatchRequest(BaseModel):
    payment_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of payment IDs to process",
        examples=[["pay_002610", "pay_000016", "pay_000040"]],
    )


class BatchItemInfo(BaseModel):
    payment_id: str
    status: str
    eligible: bool
    recovery_probability: float | None
    revenue_at_risk: float
    expected_recovery: float
    execution_status: str
    amount_recovered: float
    workflow_id: str | None
    error: str | None


class BatchMetricsInfo(BaseModel):
    total_payments: int
    eligible_payments: int
    blocked_payments: int
    deferred_payments: int
    escalated_payments: int
    recovery_attempts: int
    successful_recoveries: int
    failed_recoveries: int
    stopped_workflows: int
    errored_payments: int
    total_revenue_at_risk: float
    total_expected_recovery: float
    total_revenue_recovered: float
    recovery_rate: float
    revenue_recovery_rate: float


class BatchResponse(BaseModel):
    items: list[BatchItemInfo]
    metrics: BatchMetricsInfo


@router.post(
    "/batch",
    response_model=BatchResponse,
    summary="Batch recovery execution for multiple payments (SIMULATION MODE)",
)
def batch_recovery(
    request: BatchRequest,
) -> BatchResponse:
    """
    Process a batch of payments through the full recovery pipeline.

    Each payment is:
    1. Investigated deterministically (RecoveryAgent).
    2. Executed via the bounded orchestrator (SIMULATION MODE).

    One failed payment does NOT crash the batch.
    Aggregate metrics are computed from the combined outcomes.

    The LLM has NO involvement in this endpoint.
    """

    processor = RecoveryBatchProcessor()
    batch_result = processor.process(request.payment_ids)

    items = [
        BatchItemInfo(
            payment_id=item.payment_id,
            status=item.status,
            eligible=item.eligible,
            recovery_probability=item.recovery_probability,
            revenue_at_risk=item.revenue_at_risk,
            expected_recovery=item.expected_recovery,
            execution_status=item.execution_status,
            amount_recovered=item.amount_recovered,
            workflow_id=item.workflow_id,
            error=item.error,
        )
        for item in batch_result.items
    ]

    m = batch_result.metrics
    return BatchResponse(
        items=items,
        metrics=BatchMetricsInfo(
            total_payments=m.total_payments,
            eligible_payments=m.eligible_payments,
            blocked_payments=m.blocked_payments,
            deferred_payments=m.deferred_payments,
            escalated_payments=m.escalated_payments,
            recovery_attempts=m.recovery_attempts,
            successful_recoveries=m.successful_recoveries,
            failed_recoveries=m.failed_recoveries,
            stopped_workflows=m.stopped_workflows,
            errored_payments=m.errored_payments,
            total_revenue_at_risk=m.total_revenue_at_risk,
            total_expected_recovery=m.total_expected_recovery,
            total_revenue_recovered=m.total_revenue_recovered,
            recovery_rate=m.recovery_rate,
            revenue_recovery_rate=m.revenue_recovery_rate,
        ),
    )


# ============================================================
# POST /opportunities \u2014 Deterministic recovery opportunity ranking
#
# The LLM is NOT involved in this endpoint.
# No payment execution occurs.
# ============================================================

class OpportunitiesRequest(BaseModel):
    payment_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of payment IDs to rank",
        examples=[["pay_002610", "pay_000016", "pay_000040"]],
    )


class RankedOpportunityInfo(BaseModel):
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
    reasons:                 list[str]


class OpportunitySummaryInfo(BaseModel):
    total_payments:          int
    eligible_payments:       int
    blocked_payments:        int
    total_revenue_at_risk:   float
    total_expected_recovery: float
    top_opportunity_id:      str | None
    top_opportunity_value:   float


class OpportunitiesResponse(BaseModel):
    opportunities: list[RankedOpportunityInfo]
    summary:       OpportunitySummaryInfo


@router.post(
    "/opportunities",
    response_model=OpportunitiesResponse,
    summary="Rank recovery opportunities for a list of payments (NO execution, NO LLM)",
)
def get_opportunities(
    request: OpportunitiesRequest,
) -> OpportunitiesResponse:
    """
    Deterministic recovery opportunity ranking for a list of payments.

    This endpoint:
    1. Runs RecoveryAgent.investigate() for each payment ID (deterministic).
    2. Passes all investigation results to RecoveryOpportunityRanker.
    3. Returns a ranked list of recovery opportunities.

    Ranking criteria (descending priority):
      - Eligible payments before blocked.
      - Higher expected_recovery_value first.
      - Higher recovery_probability first.
      - Higher revenue_at_risk first.

    The LLM has NO involvement in this endpoint.
    No payment execution occurs.
    Blocked payments are always ranked below eligible payments.
    """

    agent = RecoveryAgent()
    ranker = RecoveryOpportunityRanker()

    # Investigate all payments deterministically (no LLM, no execution)
    investigation_results: list[dict] = []
    for payment_id in request.payment_ids:
        inv = agent.investigate(payment_id)
        investigation_results.append(inv)

    # Rank deterministically
    ranking = ranker.rank(investigation_results)

    opportunities = [
        RankedOpportunityInfo(
            rank=o.rank,
            payment_id=o.payment_id,
            amount=o.amount,
            currency=o.currency,
            failure_reason=o.failure_reason,
            eligible=o.eligible,
            recovery_probability=o.recovery_probability,
            revenue_at_risk=o.revenue_at_risk,
            expected_recovery_value=o.expected_recovery_value,
            priority=o.priority,
            recommended_action=o.recommended_action,
            status=o.status,
            reasons=o.reasons,
        )
        for o in ranking.opportunities
    ]

    s = ranking.summary
    return OpportunitiesResponse(
        opportunities=opportunities,
        summary=OpportunitySummaryInfo(
            total_payments=s.total_payments,
            eligible_payments=s.eligible_payments,
            blocked_payments=s.blocked_payments,
            total_revenue_at_risk=s.total_revenue_at_risk,
            total_expected_recovery=s.total_expected_recovery,
            top_opportunity_id=s.top_opportunity_id,
            top_opportunity_value=s.top_opportunity_value,
        ),
    )


# ============================================================
# POST /draft_reminder
# ============================================================

class DraftReminderRequest(BaseModel):
    payment_id: str

class DraftReminderResponse(BaseModel):
    payment_id: str
    email_draft: str

@router.post(
    "/draft_reminder",
    response_model=DraftReminderResponse,
    summary="Draft a personalized email reminder using AI",
)
def draft_reminder(request: DraftReminderRequest) -> DraftReminderResponse:
    agent = RecoveryAgent()
    investigation = agent.investigate(request.payment_id)
    if investigation.get("status") == "failed" and not investigation.get("payment"):
        raise HTTPException(status_code=404, detail="Payment not found.")
    
    payment_context = investigation.get("payment") or {}
    
    provider = _get_provider()
    outreach = OutreachAgent(provider=provider)
    draft = outreach.draft_reminder(payment_context)
    
    return DraftReminderResponse(payment_id=request.payment_id, email_draft=draft)

# ============================================================
# GET /escalated
# ============================================================

class EscalatedCaseInfo(BaseModel):
    payment_id: str
    workflow_id: str
    amount: float
    status: str
    failure_reason: str
    timestamp: str

class EscalatedCasesResponse(BaseModel):
    cases: list[EscalatedCaseInfo]

@router.get(
    "/escalated",
    response_model=EscalatedCasesResponse,
    summary="Get all escalated or outreach-required cases",
)
def get_escalated_cases() -> EscalatedCasesResponse:
    records = get_all_audit_records()
    
    cases = []
    for r in records:
        if r.status in ["escalated", "outreach_required"]:
            cases.append(
                EscalatedCaseInfo(
                    payment_id=r.payment_id,
                    workflow_id=r.workflow_id,
                    amount=r.revenue_at_risk,
                    status=r.status,
                    failure_reason=r.stopping_reason,
                    timestamp=r.created_at,
                )
            )
            
    # Sort newest first
    cases.sort(key=lambda x: x.timestamp, reverse=True)
    return EscalatedCasesResponse(cases=cases)


# ============================================================
# POST /explain — Deterministic Explainability & Decision Trace
#
# The LLM is NOT involved in this endpoint.
# No execution or payment mutations occur (100% read-only).
# ============================================================

class ExplainRequest(BaseModel):
    payment_id: str = Field(
        ...,
        min_length=1,
        description="Payment ID to explain",
        examples=["pay_002610"],
    )


class FactorInfo(BaseModel):
    factor: str
    impact: str
    explanation: str


class EligibilityExplanationInfo(BaseModel):
    eligible: bool
    summary: str
    factors: list[FactorInfo]


class PredictionExplanationInfo(BaseModel):
    recovery_probability: float | None = None
    confidence_level: str
    summary: str


class DecisionExplanationInfo(BaseModel):
    recommended_action: str
    priority: str
    summary: str


class FinancialImpactInfo(BaseModel):
    revenue_at_risk: float
    expected_recovery_value: float
    currency: str = "INR"


class DecisionTraceStepInfo(BaseModel):
    step: str
    status: str
    value: str
    explanation: str


class ExplainabilityDetails(BaseModel):
    eligibility_explanation: EligibilityExplanationInfo
    prediction_explanation: PredictionExplanationInfo
    decision_explanation: DecisionExplanationInfo
    financial_impact: FinancialImpactInfo


class ExplainResponse(BaseModel):
    payment_id: str
    explainability: ExplainabilityDetails
    decision_trace: list[DecisionTraceStepInfo]


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Get deterministic explainability breakdown and decision trace (Read-Only)",
)
def explain_recovery(request: ExplainRequest) -> ExplainResponse:
    """
    Deterministic explainability engine:
    1. Reuses RecoveryAgent.investigate() for data lookup and deterministic domain outputs.
    2. Runs RecoveryExplainabilityEngine.explain() to construct structured explanations
       and decision trace steps.
    3. 100% Read-Only — no LLM, no state modification, no money movement.
    """
    payment_id = request.payment_id

    agent = RecoveryAgent()
    investigation = agent.investigate(payment_id)

    if investigation.get("status") == "failed" and not investigation.get("payment"):
        raise HTTPException(
            status_code=404,
            detail=f"Payment '{payment_id}' not found.",
        )

    engine = RecoveryExplainabilityEngine()
    res = engine.explain(investigation)

    return ExplainResponse(
        payment_id=res.payment_id,
        explainability=ExplainabilityDetails(
            eligibility_explanation=EligibilityExplanationInfo(
                eligible=res.eligibility_explanation.eligible,
                summary=res.eligibility_explanation.summary,
                factors=[
                    FactorInfo(
                        factor=f.factor,
                        impact=f.impact,
                        explanation=f.explanation,
                    )
                    for f in res.eligibility_explanation.factors
                ],
            ),
            prediction_explanation=PredictionExplanationInfo(
                recovery_probability=res.prediction_explanation.recovery_probability,
                confidence_level=res.prediction_explanation.confidence_level,
                summary=res.prediction_explanation.summary,
            ),
            decision_explanation=DecisionExplanationInfo(
                recommended_action=res.decision_explanation.recommended_action,
                priority=res.decision_explanation.priority,
                summary=res.decision_explanation.summary,
            ),
            financial_impact=FinancialImpactInfo(
                revenue_at_risk=res.financial_impact.revenue_at_risk,
                expected_recovery_value=res.financial_impact.expected_recovery_value,
                currency=res.financial_impact.currency,
            ),
        ),
        decision_trace=[
            DecisionTraceStepInfo(
                step=t.step,
                status=t.status,
                value=t.value,
                explanation=t.explanation,
            )
            for t in res.decision_trace
        ],
    )