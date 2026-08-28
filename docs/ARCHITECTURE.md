# ReviveAI — Architecture Specification

## Razorpay Buildathon — Track 03: AI Revenue Recovery

Version: 1.0

---

# 1. Architecture Goal

ReviveAI is designed as a bounded AI revenue recovery system.

The architecture must allow the system to:

1. Receive payment-related events.
2. Detect revenue at risk.
3. Create recovery cases.
4. gather structured payment/customer/subscription context.
5. Estimate recovery probability.
6. Use an AI agent to diagnose and recommend an intervention.
7. Validate that recommendation using deterministic policies.
8. Execute only permitted actions.
9. Observe the result.
10. Record the result in an audit trail.
11. Calculate measurable revenue recovery.

Core architecture principle:

AI RECOMMENDATION
→ DETERMINISTIC VALIDATION
→ CONTROLLED EXECUTION

---

# 2. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │      Merchant       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    React Frontend   │
                         │      Dashboard      │
                         └──────────┬──────────┘
                                    │
                              REST / JSON
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Backend  │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
      │   MongoDB   │       │  AI Agent   │       │  ML Model   │
      └─────────────┘       └──────┬──────┘       └─────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │  Guardrail    │
                            │    Engine     │
                            └───────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │ Action        │
                            │ Executor      │
                            └───────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │   Razorpay    │
                            │   Test APIs   │
                            └───────┬───────┘
                                    │
                                  Events
                                    │
                                    ▼
                            ┌───────────────┐
                            │    Webhook    │
                            │    Handler    │
                            └───────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │ Event         │
                            │ Processor     │
                            └───────┬───────┘
                                    │
                                    ▼
                                MongoDB
```

---

# 3. Major Components

ReviveAI consists of the following major components:

1. React Dashboard
2. FastAPI API Layer
3. Webhook Handler
4. Event Processor
5. Revenue Risk Engine
6. Recovery Case Manager
7. Recovery Probability Model
8. AI Recovery Agent
9. Agent Tool Layer
10. Guardrail Engine
11. Action Executor
12. Razorpay Integration Adapter
13. Audit Service
14. Metrics Service
15. MongoDB Database

---

# 4. Component Responsibilities

## 4.1 React Dashboard

Responsibilities:

* Display revenue-at-risk metrics.
* Display recovered revenue.
* Display recovery cases.
* Display AI decisions.
* Display policy decisions.
* Display payment health.
* Display audit history.
* Allow merchant review of escalated cases.

The frontend must not contain financial business rules.

The frontend communicates with the FastAPI backend.

---

# 5. FastAPI Backend

The FastAPI backend is the main application layer.

Responsibilities:

* REST API endpoints
* Authentication where required
* Recovery case APIs
* Dashboard APIs
* Agent orchestration
* Policy evaluation
* Razorpay API integration
* Webhook processing
* Metrics
* Audit logging

Business logic should be separated from route handlers.

Example:

```text
Route
  ↓
Service
  ↓
Domain Logic
  ↓
Repository / External Adapter
```

---

# 6. Webhook Handler

Razorpay webhooks are the primary event-driven entry point.

The webhook handler must:

1. Receive the raw HTTP request.
2. Validate the Razorpay signature.
3. Read the unique event identifier.
4. Check whether the event was already processed.
5. Store the event or processing record.
6. Return a successful response quickly.
7. Pass heavy processing to the event-processing layer.

Razorpay requires webhook signature validation using the configured webhook secret and the raw request body. Razorpay also documents `x-razorpay-event-id` for duplicate-event detection.

Reference:
https://razorpay.com/docs/webhooks/validate-test/

---

# 7. Event Processor

The Event Processor converts external Razorpay events into internal domain events.

Example:

```text
Razorpay:

subscription.pending

        ↓

Internal Event:

SUBSCRIPTION_PAYMENT_FAILED

        ↓

Recovery Engine
```

Potential external events include:

* payment.failed
* payment.authorized
* payment.captured
* subscription.pending
* subscription.charged
* subscription.halted
* subscription.activated

The exact event mapping must follow the current Razorpay documentation.

---

# 8. Event Idempotency

Razorpay webhook delivery can result in duplicate events.

Therefore:

```text
Webhook
   ↓
Read x-razorpay-event-id
   ↓
Already processed?
   ├── YES → Return success / ignore
   └── NO  → Process
```

The database should maintain a unique index on the external event ID.

The event processor must be safe to execute more than once without creating duplicate recovery cases or duplicate financial actions.

---

# 9. Revenue Risk Engine

The Revenue Risk Engine determines whether an event represents potential revenue loss.

Example:

```text
Payment Failed
      ↓
Amount = ₹2,499
      ↓
Eligible?
      ↓
YES
      ↓
Create Recovery Case
```

The engine calculates:

```text
amount_at_risk
```

and determines:

```text
recovery_eligibility
```

The initial MVP focuses on failed payments and subscription payment failures.

---

# 10. Recovery Case Manager

Every eligible revenue-loss event becomes a Recovery Case.

Example:

```text
REC-00142

Customer:
CUST-1024

Payment:
pay_xxxxx

Amount:
₹2,499

Status:
DETECTED
```

Lifecycle:

```text
DETECTED
   ↓
ANALYZING
   ↓
RECOMMENDED
   ↓
VALIDATING
   ↓
APPROVED / BLOCKED
   ↓
EXECUTING
   ↓
RECOVERED / FAILED / ESCALATED / STOPPED
```

A case must have a clear current state.

State transitions should be deterministic.

---

# 11. Recovery Probability Model

The ML model estimates:

```text
P(recovery | case context)
```

Potential inputs:

* amount
* failure reason
* payment method
* retry count
* previous successful payments
* previous failed payments
* customer age
* customer lifetime value
* subscription age
* previous recovery outcomes

Output:

```text
recovery_probability
```

Example:

```text
0.87
```

The ML model does not execute actions.

It only provides an input to the decision process.

---

# 12. AI Recovery Agent

The AI Recovery Agent is responsible for reasoning over a recovery case.

The agent receives structured context.

Example:

```text
Payment:
₹2,499

Failure:
Temporary failure

Customer age:
18 months

Successful payments:
9

Failed payments:
1

Previous recovery attempts:
0

Recovery probability:
0.87
```

The agent should determine:

1. Likely cause
2. Recovery recommendation
3. Confidence
4. Whether human approval appears necessary
5. Explanation

---

# 13. Agent Output

The agent should produce structured data.

Example:

```json
{
  "diagnosis": "Temporary payment failure",
  "recommended_action": "PAYMENT_LINK_RECOVERY",
  "confidence": 0.91,
  "reason": "Customer has a strong historical payment record and no previous recovery attempts.",
  "requires_human_approval": false
}
```

The output must be schema-validated before entering the Guardrail Engine.

---

# 14. Agent Tool Layer

The agent should not directly access database internals or arbitrary APIs.

Instead, it receives controlled tools.

Potential tools:

```text
get_payment_details
get_customer_profile
get_payment_history
get_subscription_details
get_recovery_history
calculate_recovery_probability
get_failure_reason
```

Potential action tools:

```text
create_payment_link
send_payment_link_notification
request_invoice_charge
escalate_case
stop_recovery
```

The actual availability of each Razorpay action must be validated against the current Razorpay API.

---

# 15. Important Correction: Recovery Execution

ReviveAI must not assume that Razorpay exposes a generic:

```text
retry_payment()
```

endpoint.

Instead, the application should use an internal abstraction:

```text
execute_recovery_action()
```

The Razorpay adapter then selects an appropriate supported mechanism.

For example:

```text
PAYMENT_LINK_RECOVERY
        ↓
Create Razorpay Payment Link
        ↓
Optionally send notification
        ↓
Customer completes payment
        ↓
Payment webhook
        ↓
Recovery confirmed
```

Razorpay provides APIs for creating Payment Links and sending/resending notifications. Payment Links can be used in Test Mode for simulated success/failure testing.

Reference:
https://razorpay.com/docs/api/payments/payment-links/

---

# 16. Subscription Recovery

For subscription failures, Razorpay's Test Mode allows subscription charge outcomes to be simulated.

A failed subscription charge can move the subscription from active to pending and emit a `subscription.pending` webhook.

Repeated failures can eventually cause the subscription to become halted.

ReviveAI should use these events to create and update recovery cases.

Reference:
https://razorpay.com/docs/payments/subscriptions/test/

---

# 17. Guardrail Engine

The Guardrail Engine is deterministic.

The LLM cannot modify it.

Input:

```text
AI Recommendation
+
Recovery Probability
+
Payment Data
+
Customer Data
+
Policy Configuration
```

Output:

```text
APPROVED
BLOCKED
WAIT
ESCALATE
```

Example:

```text
Amount:
₹2,499

Probability:
0.87

Retry count:
0

Cooldown:
Satisfied
```

Policy:

```text
amount <= ₹5,000
probability >= 0.80
retry_count < 2
cooldown = satisfied
```

Result:

```text
APPROVED
```

---

# 18. Guardrail Configuration

Financial limits must be centrally configured.

Example:

```text
MAX_AUTO_RECOVERY_AMOUNT = 5000
MAX_RETRY_ATTEMPTS = 2
MIN_RECOVERY_CONFIDENCE = 0.80
MIN_RETRY_COOLDOWN_HOURS = 24
MAX_CUSTOMER_CONTACTS = 2
```

These values are initial prototype configuration.

They must be configurable rather than duplicated throughout code.

---

# 19. Action Executor

The Action Executor is the only component allowed to perform approved external actions.

Flow:

```text
AI Agent
   ↓
Recommendation
   ↓
Guardrail Engine
   ↓
APPROVED
   ↓
Action Executor
   ↓
Razorpay Adapter
   ↓
Razorpay API
```

If the action is blocked:

```text
Guardrail Engine
   ↓
BLOCKED
   ↓
No external action
   ↓
Audit Log
```

---

# 20. Razorpay Adapter

Razorpay-specific API code should be isolated behind an adapter.

Example:

```text
RazorpayAdapter

create_payment_link()
send_payment_link_notification()
fetch_payment()
fetch_subscription()
fetch_invoice()
```

The rest of the application should not contain raw Razorpay API calls.

This allows the system to:

* Test business logic without Razorpay.
* Replace or mock Razorpay APIs.
* Keep vendor-specific logic isolated.
* Make future API changes easier.

---

# 21. Action Verification

The Action Executor must never assume an action succeeded merely because the API call returned successfully.

Example:

```text
Create Recovery Payment Link
        ↓
Link created
        ↓
WAIT
        ↓
Customer completes payment
        ↓
Razorpay webhook
        ↓
payment.captured
        ↓
Verify payment
        ↓
Mark case RECOVERED
        ↓
Record revenue
```

Revenue recovered must only be recorded after verified payment success.

---

# 22. Audit Service

Every important state transition should create an audit record.

Example:

```text
Case:
REC-00142

Event:
AI_RECOMMENDATION

Diagnosis:
Temporary payment failure

Action:
PAYMENT_LINK_RECOVERY

Confidence:
0.91

Policy:
APPROVED

Timestamp:
...
```

Then:

```text
Event:
PAYMENT_LINK_CREATED
```

Then:

```text
Event:
PAYMENT_CAPTURED
```

Then:

```text
Event:
REVENUE_RECOVERED
```

The audit history must provide a complete timeline.

---

# 23. Metrics Service

The Metrics Service calculates business outcomes from stored events.

Core calculations:

```text
Revenue at Risk
= sum of eligible unrecovered amounts
```

```text
Revenue Recovered
= sum of verified successful recovery amounts
```

```text
Recovery Rate
= Revenue Recovered / Eligible Revenue
```

Other metrics:

* recovery attempts
* successful recoveries
* failed recoveries
* escalation rate
* average recovery time
* average recovered amount
* stopped cases

Metrics should be derived from source data rather than manually entered values.

---

# 24. Database Architecture

MongoDB is the primary database.

Conceptual collections:

```text
merchants
customers
payments
subscriptions
recovery_cases
agent_actions
audit_logs
webhook_events
payment_links
metrics
```

Relationships are represented through IDs.

Example:

```text
Customer
   │
   ├── Payment
   │
   ├── Subscription
   │
   └── Recovery Case
          │
          ├── Agent Actions
          └── Audit Logs
```

---

# 25. Recommended Indexes

Important indexes include:

```text
webhook_events.event_id UNIQUE

payments.payment_id UNIQUE

subscriptions.subscription_id UNIQUE

recovery_cases.case_id UNIQUE

recovery_cases.status

recovery_cases.customer_id

recovery_cases.payment_id

audit_logs.case_id

agent_actions.case_id
```

Indexes should be added after confirming the actual query patterns.

---

# 26. API Architecture

Example backend endpoints:

```text
GET  /api/dashboard/summary

GET  /api/recovery-cases

GET  /api/recovery-cases/{case_id}

POST /api/recovery-cases/{case_id}/approve

POST /api/recovery-cases/{case_id}/escalate

POST /api/recovery-cases/{case_id}/stop

GET  /api/recovery-cases/{case_id}/audit

GET  /api/metrics/recovery

GET  /api/payment-health
```

Webhook endpoints:

```text
POST /webhooks/razorpay
```

The exact API surface may change during implementation.

---

# 27. End-to-End Recovery Workflow

The primary workflow is:

```text
                         RAZORPAY
                            │
                            │ webhook
                            ▼
                    ┌───────────────┐
                    │ Webhook       │
                    │ Verification  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Idempotency   │
                    │ Check         │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Event         │
                    │ Processor     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Risk Engine   │
                    └───────┬───────┘
                            │
                    Revenue at Risk
                            │
                            ▼
                    ┌───────────────┐
                    │ Recovery Case │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ ML Model      │
                    │ Probability   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ AI Agent      │
                    │ Diagnosis     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Guardrails    │
                    └───────┬───────┘
                            │
                   ┌────────┼────────┐
                   │        │        │
                APPROVE   WAIT    ESCALATE
                   │        │        │
                   ▼        ▼        ▼
               Executor   Queue    Human
                   │
                   ▼
             Razorpay API
                   │
                   ▼
               Webhook
                   │
                   ▼
              Verification
                   │
             ┌─────┴─────┐
             │           │
          SUCCESS      FAILURE
             │           │
             ▼           ▼
         RECOVERED    Next Policy
             │           │
             ▼           ▼
          Metrics     Stop/Escalate
```

---

# 28. Example Recovery Workflow

Input:

```text
payment.failed

Amount:
₹2,499

Customer:
CUST-1024
```

Processing:

```text
1. Verify webhook
2. Check event ID
3. Store event
4. Create recovery case
5. Calculate revenue at risk
6. Fetch customer history
7. Calculate recovery probability
8. Ask AI agent for diagnosis
9. Validate structured output
10. Run guardrail engine
11. Approve payment-link recovery
12. Create Razorpay Payment Link
13. Notify customer
14. Wait for payment result
15. Receive payment webhook
16. Verify successful capture
17. Mark case RECOVERED
18. Record ₹2,499 recovered
19. Create audit records
20. Update dashboard metrics
```

---

# 29. Failed Recovery Workflow

Example:

```text
Payment:
₹12,999

Recovery probability:
0.42

AI recommendation:
PAYMENT_LINK_RECOVERY
```

Guardrail:

```text
Probability < 0.80
```

Result:

```text
BLOCKED
```

Then:

```text
Case:
ESCALATED

Reason:
Low recovery confidence
```

No external payment action is executed.

---

# 30. Payment Degradation Workflow

ReviveAI should eventually detect unusual increases in payment failures.

Example:

```text
Normal failure rate:
3%

Current failure rate:
12%

Increase:
4x
```

The system should create:

```text
PAYMENT_DEGRADATION_ALERT
```

The agent should investigate:

* payment method
* failure reason
* time window
* affected customers
* affected revenue

The system must avoid blindly generating recovery attempts for a potentially systemic payment problem.

---

# 31. Frontend Architecture

```text
React
 │
 ├── Dashboard
 │
 ├── Recovery Queue
 │
 ├── Case Details
 │
 ├── AI Decision View
 │
 ├── Payment Health
 │
 ├── Audit Trail
 │
 └── Metrics
```

Frontend service layer:

```text
api/
 ├── dashboardApi
 ├── recoveryApi
 ├── metricsApi
 └── auditApi
```

The frontend should consume backend APIs rather than accessing MongoDB or Razorpay directly.

---

# 32. Backend Architecture

Recommended structure:

```text
backend/
└── app/
    ├── main.py
    │
    ├── api/
    │   ├── routes/
    │   └── dependencies/
    │
    ├── agents/
    │   ├── recovery_agent.py
    │   ├── prompts/
    │   └── tools/
    │
    ├── domain/
    │   ├── recovery/
    │   ├── payments/
    │   └── subscriptions/
    │
    ├── services/
    │   ├── risk_service.py
    │   ├── recovery_service.py
    │   ├── metrics_service.py
    │   └── audit_service.py
    │
    ├── policies/
    │   ├── guardrails.py
    │   └── configuration.py
    │
    ├── integrations/
    │   └── razorpay/
    │       ├── client.py
    │       ├── adapter.py
    │       └── webhooks.py
    │
    ├── models/
    │
    ├── repositories/
    │
    └── utils/
```

This structure may evolve as implementation begins.

---

# 33. ML Architecture

```text
Synthetic Dataset
       ↓
Feature Engineering
       ↓
Train / Validation / Test Split
       ↓
Model Training
       ↓
Evaluation
       ↓
Model Artifact
       ↓
FastAPI Inference Service
       ↓
Recovery Agent Context
```

The ML model should not directly execute actions.

---

# 34. AI Architecture

```text
Recovery Case
      ↓
Context Builder
      ↓
Structured Context
      ↓
LLM
      ↓
Structured Agent Output
      ↓
Schema Validation
      ↓
Guardrail Engine
```

The AI layer should remain separate from the financial execution layer.

---

# 35. Security Architecture

Security priorities:

1. Never expose API keys to frontend.
2. Store credentials in environment variables.
3. Verify Razorpay webhook signatures.
4. Implement webhook idempotency.
5. Validate all AI structured outputs.
6. Apply deterministic guardrails.
7. Never trust AI-generated financial values.
8. Never execute unvalidated actions.
9. Log important actions.
10. Use Test Mode throughout development.

---

# 36. Failure Boundaries

Each major component should fail safely.

If:

```text
ML model unavailable
```

Then:

```text
No automatic financial action
→ Human review / fallback
```

If:

```text
LLM unavailable
```

Then:

```text
No AI recommendation
→ Queue case
```

If:

```text
Guardrail engine unavailable
```

Then:

```text
BLOCK financial action
```

If:

```text
Razorpay API unavailable
```

Then:

```text
Mark execution pending
→ Retry according to controlled infrastructure policy
→ Never duplicate financial action
```

---

# 37. Observability

The system should log:

* webhook received
* webhook verified
* webhook duplicate
* recovery case created
* ML prediction
* AI recommendation
* policy decision
* action execution
* Razorpay response
* recovery success/failure
* escalation
* stop decision

Sensitive credentials must never appear in logs.

---

# 38. Architectural Principle

The most important architectural boundary is:

```text
                 AI
                  │
                  │ recommends
                  ▼
          ┌─────────────────┐
          │ Guardrail       │
          │ Engine          │
          └────────┬────────┘
                   │
                approves
                   │
                   ▼
          ┌─────────────────┐
          │ Action Executor │
          └────────┬────────┘
                   │
                   ▼
              Razorpay
```

The AI can be intelligent.

The AI cannot redefine the rules.

---

# 39. MVP Architecture Boundary

The MVP must successfully support:

```text
Razorpay Test Event
       ↓
Recovery Case
       ↓
ML Probability
       ↓
AI Diagnosis
       ↓
Guardrail
       ↓
Payment Link Recovery
       ↓
Payment Result
       ↓
Revenue Recovered
       ↓
Audit Trail
```

Everything else is secondary.

---

# 40. Architecture Success Criteria

The architecture is considered successful when:

1. A Razorpay Test Mode event can enter the system.
2. A recovery case is automatically created.
3. Revenue at risk is calculated.
4. Recovery probability is generated.
5. AI produces a structured recommendation.
6. Guardrails validate the recommendation.
7. Approved actions reach the Razorpay integration layer.
8. Recovery results are verified through events.
9. Revenue recovered is calculated from verified outcomes.
10. Every important decision is auditable.
11. Unsafe or invalid actions are blocked.
12. Components can be tested independently.

---

# 41. Architectural North Star

ReviveAI should demonstrate:

```text
EVENT
  ↓
INTELLIGENCE
  ↓
DECISION
  ↓
CONTROL
  ↓
ACTION
  ↓
VERIFICATION
  ↓
MEASUREMENT
```

The system should never reduce this to:

```text
LLM → API
```

The architecture exists specifically to make AI-powered financial automation safe, explainable and measurable.
