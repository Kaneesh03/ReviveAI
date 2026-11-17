"""
backend/tests/test_explainability.py

Comprehensive test suite for Phase 9 Explainable Recovery Intelligence & Decision Transparency.
Covers:
1. Eligibility explanations
2. Probability bands and boundary conditions
3. Financial impact consistency
4. Deterministic decision trace verification
5. API endpoint validation (POST /explain, 404, 422, non-interference with existing routes)
6. Critical Read-Only Invariants
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agents.recovery_agent import RecoveryAgent
from app.domain.recovery.audit import get_all_audit_records, clear_audit_store
from app.domain.recovery.explainability import (
    RecoveryExplainabilityEngine,
    interpret_probability_confidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    CONFIDENCE_NA,
    PROBABILITY_HIGH_THRESHOLD,
    PROBABILITY_MEDIUM_THRESHOLD,
)

client = TestClient(app)


# ============================================================
# 1. Eligibility Explanations
# ============================================================

class TestEligibilityExplanations:
    def test_eligible_payment_explanation_is_correct(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_002610")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        assert res.eligibility_explanation.eligible is True
        assert "eligible for bounded recovery" in res.eligibility_explanation.summary.lower()
        factors = res.eligibility_explanation.factors
        assert len(factors) > 0
        assert all(f.impact == "positive" for f in factors)
        assert any("failure" in f.factor.lower() for f in factors)
        assert any("retry count" in f.factor.lower() for f in factors)

    def test_permanent_failure_explanation_is_correct(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_000016")  # payment_method_issue
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        assert res.eligibility_explanation.eligible is False
        assert "blocked" in res.eligibility_explanation.summary.lower()
        neg_factors = [f for f in res.eligibility_explanation.factors if f.impact == "negative"]
        assert len(neg_factors) > 0
        assert any("permanent failure" in f.factor.lower() for f in neg_factors)

    def test_halted_subscription_explanation_is_correct(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_000040")  # halted subscription
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        assert res.eligibility_explanation.eligible is False
        assert "subscription" in res.eligibility_explanation.summary.lower() or "blocked" in res.eligibility_explanation.summary.lower()
        neg_factors = [f for f in res.eligibility_explanation.factors if f.impact == "negative"]
        assert any("halted" in f.factor.lower() for f in neg_factors)

    def test_retry_limit_exceeded_explanation_is_correct(self):
        engine = RecoveryExplainabilityEngine()
        mock_inv = {
            "payment_id": "pay_test_retry_exceeded",
            "payment": {
                "payment_id": "pay_test_retry_exceeded",
                "amount": 1200.0,
                "currency": "INR",
                "payment_status": "failed",
                "failure_reason": "temporary_bank_failure",
                "retry_count": 3,
                "subscription_status": "active",
            },
            "eligibility": {
                "eligible": False,
                "reason": "retry_limit_exceeded",
            },
            "prediction": {},
            "revenue_risk": {
                "revenue_at_risk": 1200.0,
                "expected_recovery_value": 0.0,
            },
            "decision": {
                "eligible": False,
                "priority": "NONE",
                "recommended_action": "DO_NOT_RETRY",
                "reasons": ["Retry limit exceeded."],
            },
        }
        res = engine.explain(mock_inv)

        assert res.eligibility_explanation.eligible is False
        neg_factors = [f for f in res.eligibility_explanation.factors if f.impact == "negative"]
        assert any("retry limit" in f.factor.lower() for f in neg_factors)



# ============================================================
# 2. Probability Bands & Boundary Conditions
# ============================================================

class TestProbabilityBands:
    def test_high_probability_maps_to_high(self):
        assert interpret_probability_confidence(0.95) == CONFIDENCE_HIGH
        assert interpret_probability_confidence(0.85) == CONFIDENCE_HIGH
        assert interpret_probability_confidence(1.0) == CONFIDENCE_HIGH

    def test_medium_probability_maps_to_medium(self):
        assert interpret_probability_confidence(0.75) == CONFIDENCE_MEDIUM
        assert interpret_probability_confidence(0.60) == CONFIDENCE_MEDIUM
        assert interpret_probability_confidence(0.50) == CONFIDENCE_MEDIUM

    def test_low_probability_maps_to_low(self):
        assert interpret_probability_confidence(0.49) == CONFIDENCE_LOW
        assert interpret_probability_confidence(0.10) == CONFIDENCE_LOW
        assert interpret_probability_confidence(0.0) == CONFIDENCE_LOW

    def test_boundary_values(self):
        # Exact high boundary
        assert interpret_probability_confidence(PROBABILITY_HIGH_THRESHOLD) == CONFIDENCE_HIGH
        assert interpret_probability_confidence(PROBABILITY_HIGH_THRESHOLD - 0.0001) == CONFIDENCE_MEDIUM

        # Exact medium boundary
        assert interpret_probability_confidence(PROBABILITY_MEDIUM_THRESHOLD) == CONFIDENCE_MEDIUM
        assert interpret_probability_confidence(PROBABILITY_MEDIUM_THRESHOLD - 0.0001) == CONFIDENCE_LOW

        # None / Not Applicable
        assert interpret_probability_confidence(None) == CONFIDENCE_NA


# ============================================================
# 3. Financial Values & Invariance
# ============================================================

class TestFinancialValues:
    def test_financial_values_match_underlying_engine(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_002610")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        expected_rar = inv["revenue_risk"]["revenue_at_risk"]
        expected_ev = inv["revenue_risk"]["expected_recovery_value"]

        assert res.financial_impact.revenue_at_risk == expected_rar
        assert res.financial_impact.expected_recovery_value == expected_ev
        assert res.financial_impact.currency == "INR"

    def test_blocked_payment_zero_expected_recovery(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_000016")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        assert res.financial_impact.expected_recovery_value == 0.0
        assert res.prediction_explanation.confidence_level == CONFIDENCE_NA


# ============================================================
# 4. Deterministic Decision Trace
# ============================================================

class TestDecisionTrace:
    def test_decision_trace_step_sequence(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_002610")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        trace = res.decision_trace
        assert len(trace) == 5
        step_names = [t.step for t in trace]
        expected_names = [
            "Payment Analysis",
            "Eligibility Check",
            "Recovery Prediction",
            "Revenue Risk",
            "Decision",
        ]
        assert step_names == expected_names

    def test_eligible_payment_trace_statuses(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_002610")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        trace = {t.step: t for t in res.decision_trace}
        assert trace["Payment Analysis"].status == "COMPLETE"
        assert trace["Eligibility Check"].status == "PASS"
        assert trace["Recovery Prediction"].status == "COMPLETE"
        assert trace["Revenue Risk"].status == "COMPLETE"
        assert trace["Decision"].status in ("RECOMMENDED", "OUTREACH", "ESCALATED")

    def test_blocked_payment_trace_statuses(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_000016")
        engine = RecoveryExplainabilityEngine()
        res = engine.explain(inv)

        trace = {t.step: t for t in res.decision_trace}
        assert trace["Payment Analysis"].status == "COMPLETE"
        assert trace["Eligibility Check"].status == "BLOCKED"
        assert trace["Recovery Prediction"].status == "SKIPPED"
        assert trace["Revenue Risk"].status == "COMPLETE"
        assert trace["Decision"].status == "BLOCKED"
        assert "DO_NOT_RETRY" in trace["Decision"].value


# ============================================================
# 5. API Tests (/explain)
# ============================================================

class TestExplainAPI:
    def test_explain_valid_eligible_payment(self):
        res = client.post("/api/v1/recovery/explain", json={"payment_id": "pay_002610"})
        assert res.status_code == 200
        data = res.json()
        assert data["payment_id"] == "pay_002610"
        assert "explainability" in data
        assert "decision_trace" in data
        assert data["explainability"]["eligibility_explanation"]["eligible"] is True
        assert len(data["decision_trace"]) == 5

    def test_explain_valid_blocked_payment(self):
        res = client.post("/api/v1/recovery/explain", json={"payment_id": "pay_000016"})
        assert res.status_code == 200
        data = res.json()
        assert data["payment_id"] == "pay_000016"
        assert data["explainability"]["eligibility_explanation"]["eligible"] is False
        assert data["explainability"]["decision_explanation"]["recommended_action"] == "DO_NOT_RETRY"

    def test_explain_unknown_payment_returns_404(self):
        res = client.post("/api/v1/recovery/explain", json={"payment_id": "pay_nonexistent_999"})
        assert res.status_code == 404

    def test_explain_missing_id_returns_422(self):
        res = client.post("/api/v1/recovery/explain", json={})
        assert res.status_code == 422

    def test_explain_empty_id_returns_422(self):
        res = client.post("/api/v1/recovery/explain", json={"payment_id": ""})
        assert res.status_code == 422


# ============================================================
# 6. Critical Read-Only Invariant Tests
# ============================================================

class TestReadOnlyInvariant:
    def test_explain_does_not_create_audit_records(self):
        clear_audit_store()
        initial_records_count = len(get_all_audit_records())
        assert initial_records_count == 0

        # Call explain API multiple times
        res1 = client.post("/api/v1/recovery/explain", json={"payment_id": "pay_002610"})
        res2 = client.post("/api/v1/recovery/explain", json={"payment_id": "pay_000016"})
        assert res1.status_code == 200
        assert res2.status_code == 200

        # Audit store must remain completely empty (no executions triggered)
        records_after = get_all_audit_records()
        assert len(records_after) == 0

    def test_explain_is_idempotent_and_deterministic(self):
        engine = RecoveryExplainabilityEngine()
        agent = RecoveryAgent()
        inv1 = agent.investigate("pay_002610")
        inv2 = agent.investigate("pay_002610")

        res1 = engine.explain(inv1).to_dict()
        res2 = engine.explain(inv2).to_dict()

        assert res1 == res2

    def test_explain_does_not_modify_investigation_object(self):
        agent = RecoveryAgent()
        inv = agent.investigate("pay_002610")
        engine = RecoveryExplainabilityEngine()

        orig_eligible = inv["eligibility"]["eligible"]
        orig_prob = inv["prediction"]["recovery_probability"]
        orig_rar = inv["revenue_risk"]["revenue_at_risk"]

        engine.explain(inv)

        assert inv["eligibility"]["eligible"] == orig_eligible
        assert inv["prediction"]["recovery_probability"] == orig_prob
        assert inv["revenue_risk"]["revenue_at_risk"] == orig_rar
