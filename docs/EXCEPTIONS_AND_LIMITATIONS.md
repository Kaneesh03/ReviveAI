# ReviveAI — Exceptions, Limitations & Operational Boundaries

**Document Version:** 1.0.0  
**Project:** ReviveAI (Razorpay Buildathon — Track 03: AI Revenue Recovery)  
**Status:** Verification Baseline Document  

---

## 1. Executive Summary

ReviveAI is designed as an AI-powered revenue recovery intelligence platform governed by deterministic financial safety policies. This document details the technical and operational boundaries, dataset characteristics, model constraints, and exception-handling behaviors of the current system.

The core design principle is:
> **AI investigates, explains, and drafts communication. Deterministic policy controls financial eligibility, recovery decisions, and bounded execution.**

---

## 2. Payment Data Limitations

1. **Synthetic & Historical Training Distribution:**
   - The current dataset (`recovery_training.csv`, 6,012 records) is generated for benchmarking and training recovery probability models.
   - While modeled on realistic subscription payment lifecycle attributes (card, UPI, netbanking), it does not capture all nuances of real-world multi-merchant or international gateway payment distributions.
2. **Dataset Scope:**
   - The recovery dataset intentionally contains failed payment scenarios. Non-failed (successful) payments are validated directly at the deterministic eligibility policy layer rather than through the recovery dataset.
3. **Static Snapshot vs. Real-Time Streaming:**
   - In the current MVP phase, data retrieval queries the processed local dataset. Production deployment will ingest streaming webhook events directly into an operational MongoDB store.

---

## 3. Machine Learning Model Limitations

1. **Model Scope:**
   - The recovery probability model (trained with scikit-learn Logistic Regression / Random Forest Pipeline) is trained strictly on the **recovery-eligible population** (3,558 training records).
   - Ineligible payments (e.g. permanent payment method errors, halted subscriptions) bypass the ML inference step entirely because deterministic policy already forbids automated retry.
2. **Measured Quality Metrics:**
   - **ROC-AUC:** `0.6960` on a 20% stratified holdout test set (712 evaluation samples).
   - **Accuracy:** `81.88%` on the holdout test set.
3. **Decision-Support Signal, Not a Guarantee:**
   - Recovery probability is an estimated mathematical likelihood based on historical features (retry count, customer tenure, LTV, failure reason). It is a decision-support signal for ranking and priority calculation, not a guarantee of payment settlement.
4. **Model Drift & Retraining:**
   - Production distribution shifts (e.g., changes in bank downtime patterns or seasonal purchasing) require scheduled model re-evaluation and calibration.

---

## 4. Recovery Execution Limitations

1. **Simulation Mode Execution:**
   - All recovery executions performed by `PaymentRecoveryGateway` operate strictly in **`SIMULATION` mode**.
   - No live money is transferred, no live cards are charged, and no real-money transactions occur.
2. **Execution Gate:**
   - The only component authorized to invoke the simulation gateway is the `RecoveryOrchestrator`.
   - The AI Agent, LLM providers (`NVIDIAProvider`, `MockProvider`), and user input have **zero direct execution authority**.

---

## 5. Customer Outreach Limitations

1. **Draft Generation Only:**
   - The `OutreachAgent` generates personalized, empathetic email drafts based on customer tenure, LTV, and failure codes.
   - All generated outreach drafts require **explicit merchant review and approval** in the Escalation Hub.
2. **Simulated Delivery:**
   - In this MVP version, email delivery is simulated and displayed in the frontend dashboard. No real SMTP/SendGrid delivery is executed automatically without merchant integration.

---

## 6. Policy & Guardrail Limitations

1. **Configurable Thresholds:**
   - Current deterministic policy limits:
     - `MAX_RETRY_COUNT = 2` (attempts above this are blocked).
     - `MAX_RECOVERY_AMOUNT = ₹50,000.00` (transactions above this are blocked from automated retries).
     - `MAX_WORKFLOW_STEPS = 3` (hard workflow engine loop safety ceiling).
2. **Deterministic Rules:**
   - These thresholds are defined in authoritative domain constants (`eligibility.py`, `orchestrator.py`) and cannot be overridden by prompt injection or LLM reasoning.
   - Transitioning to production will require merchant-specific configuration sets.

---

## 7. Scalability & Infrastructure Limitations

1. **Benchmarked Local Throughput:**
   - Local batch throughput benchmark demonstrates **~9.57 payments/second** (single 9-item batch) and **~7.26 payments/second sustained** (135 evaluations over 15 iterations).
   - These benchmarks represent single-process execution. Distributed throughput with horizontal worker scaling and asynchronous queues (Celery/Redis) will be required for large-scale enterprise volume.
2. **In-Memory Audit Trail:**
   - The current development audit store holds workflow records in memory. Production deployment requires persistence to MongoDB collections with audit log indexing.

---

## 8. Security & Production Readiness

1. **Credential Isolation:**
   - All external credentials (`NVIDIA_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) are loaded strictly from server-side environment variables (`.env`).
   - Zero credentials or API keys are exposed to client-side bundles or frontend code.
2. **Production Deployment Requirements:**
   - Production readiness requires:
     - Role-Based Access Control (RBAC) and merchant authentication.
     - Webhook HMAC SHA256 signature verification.
     - End-to-end TLS encryption.
     - Centralized SIEM/audit logging.

---

## 9. Comprehensive Exception Matrix

The table below documents how ReviveAI handles edge cases and exceptions deterministically:

| Scenario / Exception | Policy Action | Outcome / Status | Execution Behavior |
|---|---|---|---|
| **Unknown Payment ID** | Investigation returns `found=False` | HTTP 404 / Item error | Processed gracefully; isolated in batch without crashing other items. |
| **Permanent Failure** (`payment_method_issue`, `repeated_failure`, `unknown_failure`) | `evaluate_recovery_eligibility()` returns `eligible=False` | `status = "blocked"` / Action: `DO_NOT_RETRY` | 0 gateway attempts made. Recovery blocked. |
| **Halted Subscription** (`subscription_status = "halted"`) | Policy rejects halted subscription | `status = "blocked"` / Action: `DO_NOT_RETRY` | 0 gateway attempts made. Prevents unauthorized billing. |
| **Retry Limit Exceeded** (`retry_count > 2`) | Policy rejects excess retries | `status = "blocked"` / Action: `DO_NOT_RETRY` | 0 gateway attempts made. Halted by safety policy. |
| **Retry Limit Reached** (`retry_count == 2`) | Evaluated by decision engine | `status = "escalated"` / Action: `ESCALATE_TO_HUMAN` | Routed to Escalation Hub for merchant manual evaluation. |
| **Customer Action Needed** (`insufficient_funds`, `card_expired`) | Decision engine evaluates failure reason | `status = "outreach_required"` / Action: `SEND_PAYMENT_REMINDER` | Automated retry halted; AI email draft prepared for merchant review. |
| **High Amount Exceeded** (`amount > ₹50,000`) | Policy rejects excessive transaction amount | `status = "blocked"` / Action: `DO_NOT_RETRY` | Prevents automated money movement on large transaction values. |
| **Missing Failure Reason** | Guardrail requires diagnostic code | `status = "blocked"` / Action: `DO_NOT_RETRY` | Rejects unclassified payment records. |
| **Payment Status Not Failed** (`payment_status = "success"`) | Policy requires `payment_status == "failed"` | `status = "blocked"` / Reason: `payment_not_failed` | Prevents double-charging or retrying settled payments. |
| **ML Model File Missing / Corrupted** | `get_model()` raises structured `FileNotFoundError` | Investigation reports error | Error logged in agent state; does not execute retries blindly. |
| **Batch Item Failure** | Individual payment item fails or throws | `BatchItemResult.error` recorded | Batch continues processing remaining items; aggregate metrics remain accurate. |
| **Read-Only / Explain Call** | `POST /explain` invoked | `status = 200` with structured explanation | 0 audit records created, 0 state mutations, 100% idempotent. |
