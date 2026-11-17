"""
tests/test_api.py

Integration tests for the FastAPI recovery endpoint.

These tests use the TestClient (no live server required).
They exercise the full stack:

    HTTP request
        ↓
    Route handler
        ↓
    RecoveryAgent (deterministic)
        ↓
    AgentLoop + MockProvider (deterministic)
        ↓
    Structured response
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# Health check
# ============================================================

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ============================================================
# Valid eligible payment
# ============================================================

def test_analyze_valid_eligible_payment():
    """
    pay_002610 is a known eligible payment with:
        - recovery_probability ≈ 0.8876
        - revenue_at_risk      ≈ 28100.45
        - expected_recovery_value ≈ 24941.96
        - priority             = HIGH
        - recommended_action   = RETRY_PAYMENT
    """
    response = client.post(
        "/api/v1/recovery/analyze",
        json={"payment_id": "pay_002610"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    # Top-level shape
    assert data["payment_id"] == "pay_002610"
    assert data["status"] in ("decision_complete", "failed", "unknown")

    # Payment info present
    assert data["payment"] is not None
    assert data["payment"]["payment_id"] == "pay_002610"

    # Eligibility
    assert data["eligibility"] is not None
    assert data["eligibility"]["eligible"] is True

    # Decision
    assert data["decision"] is not None
    decision = data["decision"]

    assert decision["eligible"] is True

    prob = decision["recovery_probability"]
    assert 0.88 <= prob <= 0.90, (
        f"Expected recovery_probability ≈ 0.8876, got {prob}"
    )

    rar = decision["revenue_at_risk"]
    assert 28000 <= rar <= 28200, (
        f"Expected revenue_at_risk ≈ 28100.45, got {rar}"
    )

    erv = decision["expected_recovery_value"]
    assert 24000 <= erv <= 26000, (
        f"Expected expected_recovery_value ≈ 24941.96, got {erv}"
    )

    assert decision["priority"] == "HIGH"
    assert decision["recommended_action"] == "RETRY_PAYMENT"

    # Agent narrative
    assert data["agent"] is not None
    assert data["agent"]["status"] == "complete"
    assert data["agent"]["iterations"] >= 1
    assert isinstance(data["agent"]["explanation"], str)
    assert len(data["agent"]["explanation"]) > 0


# ============================================================
# Unknown payment ID
# ============================================================

def test_analyze_unknown_payment_returns_404():
    response = client.post(
        "/api/v1/recovery/analyze",
        json={"payment_id": "pay_DOES_NOT_EXIST"},
    )
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not found" in detail.lower()


# ============================================================
# Malformed request — missing payment_id
# ============================================================

def test_analyze_missing_payment_id_returns_422():
    response = client.post(
        "/api/v1/recovery/analyze",
        json={},
    )
    assert response.status_code == 422


# ============================================================
# Malformed request — empty string payment_id
# ============================================================

def test_analyze_empty_payment_id_returns_422():
    response = client.post(
        "/api/v1/recovery/analyze",
        json={"payment_id": ""},
    )
    assert response.status_code == 422


# ============================================================
# Ineligible payment
# ============================================================

def test_analyze_ineligible_payment():
    """
    Find a payment that is not eligible and verify that:
    - status is not 404
    - decision.eligible is False
    - decision.recommended_action is DO_NOT_RETRY
    """
    # Search for a payment with a permanent failure reason.
    # pay_000001 and similar low-numbered IDs tend to be
    # ineligible in the synthetic dataset.
    # We iterate a few IDs to find one that returns ineligible.

    found_ineligible = False

    for suffix in range(1, 50):
        pid = f"pay_{suffix:06d}"

        response = client.post(
            "/api/v1/recovery/analyze",
            json={"payment_id": pid},
        )

        if response.status_code == 404:
            continue

        assert response.status_code == 200

        data = response.json()

        if (
            data.get("eligibility") is not None
            and data["eligibility"]["eligible"] is False
        ):
            decision = data.get("decision")
            assert decision is not None
            assert decision["eligible"] is False
            assert decision["recommended_action"] == "DO_NOT_RETRY"
            found_ineligible = True
            break

    # There should always be ineligible payments in the dataset.
    assert found_ineligible, (
        "Could not find an ineligible payment in pay_000001..pay_000049"
    )
