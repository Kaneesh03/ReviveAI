# ReviveAI — AI Agent Development Instructions

## 1. Project Identity

Project Name: ReviveAI

Track: Razorpay Buildathon — Track 03: AI Revenue Recovery

ReviveAI is an AI-powered revenue recovery system for merchants using Razorpay.

The system detects revenue at risk, diagnoses the cause of the revenue loss, predicts recovery probability, recommends an appropriate recovery intervention, validates that intervention against deterministic safety policies, executes permitted actions through Razorpay Test Mode APIs, and records the complete outcome in an auditable manner.

Core product loop:

DETECT → DIAGNOSE → DECIDE → VALIDATE → ACT → MEASURE

---

## 2. Primary Problem

Merchants lose revenue through events such as:

- Failed payments
- Failed subscription charges
- Checkout abandonment
- Repeated payment failures
- Payment degradation
- Overdue receivables

The MVP focuses primarily on:

FAILED PAYMENT AND SUBSCRIPTION RECOVERY.

The goal is not simply to identify failed payments.

The system must determine:

1. What revenue is at risk?
2. Why is it at risk?
3. How likely is recovery?
4. What intervention should be attempted?
5. Is that intervention safe and permitted?
6. Did the intervention recover revenue?
7. What should happen if recovery fails?

---

## 3. Product Goal

Build a working, measurable AI revenue recovery agent that can:

- Detect revenue-at-risk events
- Create recovery cases
- Analyze customer and payment history
- Estimate recovery probability
- Diagnose likely causes
- Recommend recovery actions
- Validate recommendations using deterministic policies
- Execute permitted recovery actions using Razorpay Test Mode
- Stop when recovery should no longer continue
- Escalate cases requiring human intervention
- Record every important decision and action
- Measure revenue recovered

---

## 4. Core Architecture

The intended architecture is:

Razorpay Test APIs
        ↓
Webhook Layer
        ↓
Event Processor
        ↓
MongoDB
        ↓
Revenue Risk Engine
        ↓
Recovery Probability Model
        ↓
AI Recovery Agent
        ↓
Guardrail / Policy Engine
        ↓
Action Executor
        ↓
Razorpay Test APIs
        ↓
Result Processor
        ↓
Audit Log + Metrics
        ↓
React Dashboard

Do not bypass this architecture without a documented reason.

---

## 5. Critical Financial Safety Rule

THE LLM MUST NEVER HAVE DIRECT UNRESTRICTED ACCESS TO MONEY-MOVING APIs.

Never implement:

LLM → Razorpay payment API

Instead:

LLM
 ↓
Structured Recommendation
 ↓
Deterministic Guardrail Engine
 ↓
Policy Validation
 ↓
Permission Check
 ↓
Action Executor
 ↓
Razorpay Test API

The LLM can recommend an action.

The deterministic policy engine decides whether the action is permitted.

---

## 6. AI Agent Responsibilities

The AI agent may:

- Investigate a recovery case
- Request relevant customer information through tools
- Request payment history through tools
- Request subscription information through tools
- Request recovery history
- Interpret failure information
- Explain likely causes
- Recommend recovery actions
- Explain why an action was recommended
- Decide when a case should be escalated
- Decide when recovery should stop

The AI agent must NOT:

- Bypass guardrails
- Modify financial policy rules
- Directly execute unrestricted financial actions
- Invent payment information
- Invent recovery results
- Claim that revenue was recovered without verified evidence
- Increase retry limits
- Increase transaction limits
- Disable safety mechanisms
- Override human approval requirements

---

## 7. Initial Recovery Actions

The MVP supports these conceptual recovery actions:

1. RETRY_PAYMENT
2. SEND_PAYMENT_REMINDER
3. ESCALATE_TO_HUMAN
4. STOP_RECOVERY
5. WAIT_FOR_COOLDOWN

Additional actions may be added later only after the MVP is stable.

---

## 8. Guardrail Principles

All automated financial actions must pass deterministic policy validation.

Initial conceptual policies include:

- Maximum automatic recovery amount
- Maximum retry attempts
- Minimum retry cooldown
- Minimum recovery confidence
- Maximum customer contact frequency
- Human approval threshold
- Recovery eligibility rules

Example:

IF amount <= automatic_limit
AND retry_count < maximum_retries
AND cooldown_satisfied = true
AND recovery_probability >= minimum_confidence

THEN action may be approved.

Otherwise:

- WAIT
- ESCALATE
- or STOP

The exact numerical limits must be configurable and must not be hardcoded throughout the application.

---

## 9. Auditability

Every significant agent decision must be auditable.

At minimum, record:

- Case ID
- Payment ID
- Customer ID
- Timestamp
- Problem detected
- Revenue at risk
- AI diagnosis
- AI confidence
- Recommended action
- Policy decision
- Policy reason
- Execution result
- Revenue recovered
- Escalation status

The system must be able to answer:

"Why did ReviveAI take this action?"

---

## 10. Revenue Measurement

The project must measure actual outcomes.

Important metrics include:

- Total revenue at risk
- Eligible recovery amount
- Recovery attempts
- Successful recoveries
- Revenue recovered
- Recovery rate
- Average recovery amount
- Average recovery time
- Human escalation rate
- Stopped recovery cases
- Failed recovery attempts

Never fabricate business metrics.

All displayed metrics must originate from stored application data or explicitly labelled synthetic test data.

---

## 11. Machine Learning

The ML component is responsible primarily for estimating:

RECOVERY PROBABILITY

Potential input features:

- Payment amount
- Payment method
- Failure type
- Failure reason
- Retry count
- Previous successful payments
- Previous failed payments
- Customer age
- Customer lifetime value
- Subscription age
- Historical recovery outcomes

Initial models may include:

- Logistic Regression
- Random Forest

Prefer a simple interpretable model before introducing unnecessary complexity.

The model must be evaluated using a held-out test set.

Potential metrics:

- Precision
- Recall
- F1 Score
- ROC-AUC
- Calibration where appropriate

---

## 12. LLM Responsibilities

The LLM is primarily responsible for:

- Reasoning over structured context
- Diagnosing failures
- Explaining decisions
- Selecting among predefined recovery actions
- Producing structured agent outputs

The LLM should not be responsible for:

- Calculating authoritative financial values
- Enforcing safety policies
- Maintaining retry counters
- Determining whether an action is financially permitted
- Generating authoritative transaction status
- Generating fake metrics

Deterministic code must handle these responsibilities.

---

## 13. Agent Tools

Potential agent tools include:

- get_payment_details
- get_customer_profile
- get_payment_history
- get_subscription_details
- get_failure_reason
- get_recovery_history
- calculate_recovery_probability
- recommend_recovery_action
- send_payment_reminder
- request_payment_retry
- escalate_case
- stop_recovery
- create_audit_log

Tool access must follow least-privilege principles.

Only expose tools required for the current workflow.

---

## 14. Razorpay Integration

Use Razorpay Test Mode during development.

Never use real money.

Never commit Razorpay credentials to Git.

Credentials must be loaded from environment variables.

Expected configuration includes:

RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET

Use .env locally.

Provide .env.example for documentation.

.env must be included in .gitignore.

---

## 15. Webhook Security

Webhook processing must include:

1. Signature verification
2. Event validation
3. Idempotent processing
4. Safe error handling
5. Event logging

Never trust webhook payloads without verification.

Do not process the same event repeatedly.

---

## 16. Database

MongoDB is the intended primary database.

Initial conceptual collections:

- merchants
- customers
- payments
- subscriptions
- recovery_cases
- agent_actions
- audit_logs
- metrics

Keep database logic separated from business logic.

Use appropriate indexes for frequently queried fields.

---

## 17. Backend

Preferred backend:

Python + FastAPI

Responsibilities include:

- REST APIs
- Webhook endpoints
- Agent orchestration
- ML inference
- Policy evaluation
- Razorpay integration
- Database operations
- Audit logging

Business logic should not be placed directly inside route handlers.

---

## 18. Frontend

Preferred frontend:

React + Vite

The dashboard should eventually display:

- Revenue at Risk
- Revenue Recovered
- Recovery Rate
- Active Recovery Cases
- Recovery Queue
- Payment Health
- AI Decisions
- AI Explanations
- Audit Trail
- Evaluation Metrics

Do not build unnecessary pages before the core workflow works.

---

## 19. Development Philosophy

Build incrementally.

Do NOT attempt to generate the complete application in one step.

Preferred development order:

1. Project foundation
2. Database models
3. Synthetic data
4. Revenue risk detection
5. Recovery probability model
6. AI diagnosis
7. Agent tools
8. Recovery strategy
9. Guardrail engine
10. Action executor
11. Razorpay Test Mode integration
12. Webhook processing
13. Audit system
14. Dashboard
15. Evaluation
16. Deployment
17. Documentation

Each stage should work before moving to the next.

---

## 20. Vertical Slice Strategy

Prefer small end-to-end workflows over isolated components.

Example:

Payment failure
 ↓
Recovery case
 ↓
Diagnosis
 ↓
Recommendation
 ↓
Guardrail
 ↓
Action
 ↓
Result
 ↓
Audit

Build this basic slice first.

Then expand it.

---

## 21. Coding Rules

- Write readable code
- Prefer small functions
- Use clear names
- Avoid unnecessary abstractions
- Avoid premature microservices
- Add error handling
- Add tests for important business logic
- Never silently swallow errors
- Never hardcode credentials
- Never hardcode financial limits in multiple places
- Keep configuration centralized
- Document non-obvious decisions

---

## 22. Testing

Important areas requiring tests:

- Revenue-at-risk calculation
- Recovery probability inference
- Guardrail rules
- Retry limits
- Cooldown logic
- Human escalation
- Webhook signature validation
- Webhook idempotency
- Agent tool validation
- Action execution
- Audit logging
- Revenue metrics

Financial policy tests are especially important.

---

## 23. AI Coding Agent Rules

AI coding agents such as OpenCode, Antigravity, and Claude must:

1. Read AGENTS.md before modifying the project.
2. Understand the existing architecture before creating new files.
3. Avoid unnecessary rewrites.
4. Explain significant architectural changes.
5. Run relevant tests after changes.
6. Never remove safety mechanisms to make a demo work.
7. Never replace deterministic financial controls with LLM reasoning.
8. Never introduce real-money transaction logic.
9. Never commit secrets.
10. Prefer incremental implementation.
11. Preserve existing functionality.
12. Ask for clarification when requirements conflict with safety or architecture.

---

## 24. Definition of Done

A feature is not considered complete merely because the code runs.

A feature is complete when:

- It works
- It is tested
- It handles expected failures
- It follows the architecture
- It does not bypass guardrails
- Important decisions are auditable
- It has appropriate documentation

---

## 25. Project North Star

ReviveAI should demonstrate:

DETECT
→ DIAGNOSE
→ DECIDE
→ VALIDATE
→ ACT
→ MEASURE

The final product should convincingly demonstrate that an AI agent can recover merchant revenue while remaining:

- Explainable
- Bounded
- Auditable
- Measurable
- Reliable

The goal is NOT to make the AI autonomous at all costs.

The goal is to make the AI autonomous where appropriate and stop or escalate when it should not act.