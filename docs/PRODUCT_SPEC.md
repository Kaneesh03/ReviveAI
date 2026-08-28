# ReviveAI — Product Specification

## Razorpay Buildathon — Track 03: AI Revenue Recovery

Version: 1.0

---

# 1. Product Overview

## Product Name

ReviveAI

## Product Category

AI-powered Revenue Recovery Agent

## Target Platform

Razorpay

## Buildathon Track

Track 03 — AI Revenue Recovery

---

# 2. One-Line Product Definition

ReviveAI is an AI-powered revenue recovery agent that detects revenue at risk, diagnoses why the revenue is slipping, determines the most appropriate recovery intervention, validates that intervention through deterministic guardrails, executes permitted actions through Razorpay Test Mode, and measures the resulting revenue recovery.

---

# 3. Core Product Loop

The entire system is built around:

DETECT
→ DIAGNOSE
→ DECIDE
→ VALIDATE
→ ACT
→ MEASURE

Every major feature should contribute to this loop.

---

# 4. Problem Statement

Merchants using online payment infrastructure lose revenue through payment failures, subscription payment failures, repeated unsuccessful retries, checkout abandonment and other payment-related problems.

Traditional payment dashboards primarily show that a payment failed.

They do not automatically determine:

- Why the revenue is at risk
- How likely it is to be recovered
- Which intervention is appropriate
- Whether the intervention should be automated
- When recovery should stop
- When a human should intervene
- How much revenue was actually recovered

ReviveAI addresses this gap by creating an intelligent but bounded revenue recovery workflow.

---

# 5. Target User

## Primary User

Online merchants and businesses that use Razorpay to collect payments.

Examples:

- SaaS businesses
- Subscription businesses
- E-commerce businesses
- Education platforms
- Digital services
- Membership platforms

The initial prototype will represent a merchant operating a subscription/payment business.

---

# 6. Primary User Problem

The merchant should be able to answer:

1. How much revenue is currently at risk?
2. Which payments or subscriptions are responsible?
3. Why are those payments failing?
4. Which cases are worth attempting to recover?
5. What action should be taken?
6. Which actions can be safely automated?
7. Which cases require human approval?
8. How much revenue did the recovery process actually recover?

---

# 7. MVP Scope

The MVP focuses on:

## Failed Payment and Subscription Recovery

The first complete workflow will be:

Payment Failure
→ Detection
→ Recovery Case Creation
→ Customer Analysis
→ Payment Analysis
→ Recovery Probability
→ AI Diagnosis
→ Recovery Recommendation
→ Guardrail Validation
→ Permitted Action
→ Result
→ Audit Log
→ Revenue Metrics

---

# 8. MVP Recovery Actions

The initial system supports five conceptual actions.

## 8.1 RETRY_PAYMENT

Attempt a permitted payment retry when policy conditions are satisfied.

## 8.2 SEND_PAYMENT_REMINDER

Notify the customer that payment requires attention.

## 8.3 ESCALATE_TO_HUMAN

Send the case to merchant/human review.

## 8.4 WAIT_FOR_COOLDOWN

Wait before attempting another recovery action.

## 8.5 STOP_RECOVERY

Terminate further automated recovery attempts when continuing is not justified.

---

# 9. Revenue-at-Risk Definition

Revenue at risk represents the amount of money associated with payment events that are currently unsuccessful but potentially recoverable.

For the MVP:

Revenue at Risk =
Sum of eligible failed payment/subscription amounts

The system must distinguish between:

- Total failed revenue
- Potentially recoverable revenue
- Recovery-attempted revenue
- Successfully recovered revenue
- Revenue requiring human intervention
- Revenue permanently lost

---

# 10. Recovery Case

Every potentially recoverable event should create a Recovery Case.

Example:

Case ID:
REC-00142

Payment:
pay_xxxxx

Customer:
cust_1024

Amount:
₹2,499

Reason:
Insufficient funds

Recovery probability:
0.87

Recommended action:
RETRY_PAYMENT

Policy:
APPROVED

Status:
RECOVERED

Revenue recovered:
₹2,499

---

# 11. Recovery Case Lifecycle

A Recovery Case follows:

DETECTED
→ ANALYZING
→ RECOMMENDED
→ VALIDATING
→ APPROVED / BLOCKED
→ EXECUTING
→ RECOVERED / FAILED / ESCALATED / STOPPED

The system must never skip directly from AI recommendation to financial execution.

---

# 12. AI Responsibilities

The AI agent is responsible for:

- Investigating a recovery case
- Gathering relevant context through tools
- Understanding payment history
- Understanding customer history
- Understanding subscription status
- Interpreting failure information
- Explaining likely causes
- Recommending a recovery action
- Explaining why the action was selected
- Identifying when escalation is appropriate
- Identifying when recovery should stop

---

# 13. AI Non-Responsibilities

The AI must NOT:

- Directly bypass financial policies
- Modify guardrail thresholds
- Invent transaction data
- Invent customer history
- Invent payment results
- Claim revenue was recovered without verification
- Change retry limits
- Change financial limits
- Disable safety policies
- Execute unrestricted payment actions

Financial enforcement must remain deterministic.

---

# 14. AI Agent Tools

Potential tools include:

- get_payment_details
- get_customer_profile
- get_payment_history
- get_subscription_details
- get_failure_reason
- get_recovery_history
- calculate_recovery_probability
- recommend_recovery_action
- request_payment_retry
- send_payment_reminder
- escalate_case
- stop_recovery
- create_audit_log

Tools should use least-privilege access.

---

# 15. Recovery Probability Model

The system will include an ML model that estimates:

Probability of successful revenue recovery.

Example:

Input:

Payment amount:
₹2,499

Previous successful payments:
9

Previous failed payments:
1

Retry count:
0

Failure type:
Temporary

Output:

Recovery probability:
0.87

---

# 16. ML Features

Potential features include:

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
- Previous recovery results
- Historical payment behavior

---

# 17. Initial ML Models

Initial models should prioritize simplicity and interpretability.

Candidate models:

1. Logistic Regression
2. Random Forest

The final model will be selected based on evaluation results rather than complexity.

---

# 18. ML Evaluation

The model must be evaluated on a held-out test dataset.

Potential metrics:

- Precision
- Recall
- F1 Score
- ROC-AUC

The test dataset must not be used for training.

All reported metrics must be reproducible.

---

# 19. AI Diagnosis

The LLM receives structured information about a recovery case.

Example context:

Customer:
18 months old

Successful payments:
9

Failed payments:
1

Current amount:
₹2,499

Failure reason:
Temporary bank failure

Previous recovery attempts:
0

Recovery probability:
0.87

The LLM should produce a structured diagnosis.

Example:

Diagnosis:
Temporary payment failure.

Reasoning summary:
Customer has historically successful payment behavior and no previous recovery attempts. The amount is within the automatic recovery threshold.

Recommended action:
RETRY_PAYMENT

Confidence:
0.91

---

# 20. Structured AI Output

The AI should produce structured output similar to:

{
  "diagnosis": "...",
  "recovery_probability": 0.87,
  "recommended_action": "RETRY_PAYMENT",
  "confidence": 0.91,
  "reason": "...",
  "requires_human_approval": false
}

The system must validate this output before taking any action.

---

# 21. Guardrail Engine

The Guardrail Engine is deterministic.

The LLM cannot modify or bypass it.

Example policies:

MAX_AUTO_RECOVERY_AMOUNT
MAX_RETRY_ATTEMPTS
MIN_RETRY_COOLDOWN
MIN_RECOVERY_CONFIDENCE
MAX_CUSTOMER_CONTACTS
HUMAN_APPROVAL_THRESHOLD

Example decision:

Amount <= automatic limit
AND
Retry count < maximum retries
AND
Cooldown satisfied
AND
Recovery probability >= minimum confidence

→ APPROVED

Otherwise:

→ WAIT
→ ESCALATE
→ STOP

---

# 22. Human-in-the-Loop

Human approval should be required when:

- Transaction amount exceeds automatic threshold
- Recovery probability is low
- Maximum retry attempts are reached
- Customer behavior is unusual
- Policy rules require manual approval
- AI output is incomplete or invalid
- The system cannot confidently determine an appropriate action

---

# 23. Failure Handling

The system must handle failure gracefully.

Example:

Payment failure
→ Retry #1
→ Failed
→ Retry #2
→ Failed
→ Maximum retries reached
→ STOP
→ ESCALATE_TO_HUMAN

The system must not continue retrying indefinitely.

---

# 24. Razorpay Integration

The project will use Razorpay Test Mode.

Initial integration areas:

- Payments
- Subscriptions
- Webhooks

Relevant payment events may include:

- payment.failed
- payment.authorized
- payment.captured

Relevant subscription events may include:

- subscription.pending
- subscription.charged
- subscription.halted
- subscription.activated

The exact event implementation must follow current Razorpay API documentation.

---

# 25. Webhook Processing

Webhook workflow:

Razorpay
→ Webhook Endpoint
→ Signature Verification
→ Event Validation
→ Idempotency Check
→ Event Processing
→ Database
→ Recovery Engine

The system must prevent duplicate processing.

---

# 26. Database Entities

Initial entities:

## Merchant

- merchant_id
- name
- email
- configuration
- created_at

## Customer

- customer_id
- merchant_id
- name
- email
- created_at
- lifetime_value
- status

## Payment

- payment_id
- merchant_id
- customer_id
- amount
- currency
- method
- status
- failure_code
- failure_reason
- created_at

## Subscription

- subscription_id
- customer_id
- plan
- amount
- status
- retry_count
- current_period
- created_at

## Recovery Case

- case_id
- payment_id
- subscription_id
- customer_id
- amount_at_risk
- reason
- recovery_probability
- recommended_action
- status
- created_at
- updated_at

## Agent Action

- action_id
- case_id
- action
- reason
- confidence
- policy_result
- execution_result
- timestamp

## Audit Log

- audit_id
- case_id
- actor
- event
- action
- reason
- policy_result
- result
- timestamp

---

# 27. Dashboard

The dashboard should provide:

## Overview

- Revenue at Risk
- Revenue Recovered
- Recovery Rate
- Active Recovery Cases
- Human Escalations

## Recovery Queue

Display:

- Customer
- Amount
- Problem
- Recovery Probability
- Recommended Action
- Policy Status
- Case Status

## AI Decision View

Display:

- Diagnosis
- Reasoning summary
- Recovery probability
- Recommended action
- Confidence
- Policy decision

## Payment Health

Display:

- Payment success rate
- Payment failure rate
- Failure trends
- Payment degradation alerts

## Audit Trail

Display:

- Agent actions
- Policy decisions
- Execution results
- Timestamps

---

# 28. Business Metrics

The system must calculate:

Revenue at Risk

Eligible Recovery Amount

Recovery Attempts

Successful Recoveries

Revenue Recovered

Recovery Rate

Average Recovery Amount

Average Recovery Time

Human Escalation Rate

Stopped Recovery Cases

Failed Recovery Attempts

---

# 29. Primary Success Metric

The primary business metric is:

REVENUE RECOVERED

The system should demonstrate:

Revenue at Risk
→ Recovery Attempts
→ Successful Recoveries
→ Revenue Recovered

---

# 30. Evaluation Dataset

The project should include a synthetic dataset containing realistic payment and subscription scenarios.

Initial target:

10,000+ payment events.

Possible distribution:

- Successful payments
- Failed payments
- Temporary failures
- Permanent failures
- Subscription failures
- Repeated failures
- Recoverable cases
- Non-recoverable cases

The dataset should be generated deterministically so experiments can be reproduced.

---

# 31. Evaluation Dataset Split

Suggested split:

70% Training
15% Validation
15% Test

The test set must remain isolated until final evaluation.

---

# 32. Agent Evaluation

The agent should be evaluated on:

- Diagnosis correctness
- Recommendation correctness
- Tool-call success rate
- Invalid action rate
- Guardrail violation rate
- Escalation correctness
- Stop-decision correctness

---

# 33. Safety Evaluation

The system should demonstrate:

Unauthorized financial actions:
0

Guardrail bypasses:
0

Unverified recovery claims:
0

Duplicate webhook processing:
0

Unlimited retry loops:
0

The exact values must be verified through tests.

---

# 34. Demo Scenario

The primary demo should show:

1. A merchant has a subscription payment.
2. Payment fails.
3. Razorpay generates a webhook.
4. ReviveAI receives the event.
5. A recovery case is created.
6. The system calculates revenue at risk.
7. The ML model estimates recovery probability.
8. The AI agent investigates the case.
9. The AI diagnoses the failure.
10. The AI recommends a recovery action.
11. Guardrails validate the action.
12. The permitted action executes in Test Mode.
13. The result is received.
14. Revenue recovered is recorded.
15. The audit trail is updated.
16. Dashboard metrics update.

---

# 35. Example Successful Demo

Customer:

CUST-1024

Amount:

₹2,499

Payment:

FAILED

Failure:

Temporary failure

Previous successful payments:

9

Previous failures:

1

Recovery probability:

87%

AI recommendation:

RETRY_PAYMENT

Guardrail:

APPROVED

Execution:

SUCCESS

Revenue recovered:

₹2,499

Final status:

RECOVERED

---

# 36. Example Failed Demo

Customer:

CUST-2048

Amount:

₹12,999

Previous retries:

2

Recovery probability:

42%

AI recommendation:

RETRY_PAYMENT

Guardrail:

BLOCKED

Reason:

Recovery confidence below threshold and retry limit reached.

Final action:

ESCALATE_TO_HUMAN

This scenario demonstrates that the system does not blindly follow the AI.

---

# 37. Example Payment Degradation Scenario

The system detects:

Normal payment failure rate:

3%

Current failure rate:

12%

Change:

4x increase

The system should flag:

PAYMENT DEGRADATION DETECTED

The system should avoid blindly retrying large numbers of payments.

Instead:

- Investigate the failure pattern
- Estimate affected revenue
- Alert the merchant
- Recommend appropriate action
- Avoid excessive retries

---

# 38. Product Principles

ReviveAI must be:

## Explainable

The merchant should understand why an action was recommended.

## Bounded

AI actions must remain within deterministic policies.

## Auditable

Every significant action must be recorded.

## Measurable

Revenue recovery must be quantified.

## Reliable

Failures should be handled gracefully.

## Human-controlled

High-risk cases must be escalated.

---

# 39. Non-Goals

The initial MVP will NOT attempt to:

- Process real money
- Replace Razorpay
- Build a new payment gateway
- Build a custom LLM
- Build a mobile application
- Implement dozens of recovery strategies
- Build microservices unnecessarily
- Provide unrestricted AI financial control
- Automate every merchant finance workflow

---

# 40. Future Expansion

After the MVP is stable, possible extensions include:

1. Checkout abandonment recovery
2. Payment degradation detection
3. Overdue invoice recovery
4. B2B receivables agent
5. Personalized recovery messaging
6. Hinglish recovery assistant
7. Voice-based recovery
8. Merchant AI copilot
9. Recovery campaign optimization
10. Multi-agent recovery orchestration

These are optional and must not compromise the MVP.

---

# 41. Final Product Definition

ReviveAI is not a chatbot.

ReviveAI is not only an analytics dashboard.

ReviveAI is not only an ML prediction model.

ReviveAI is an AI-powered revenue recovery system that combines:

Payment Intelligence
+
Machine Learning
+
AI Agent Reasoning
+
Deterministic Financial Guardrails
+
Razorpay APIs
+
Workflow Automation
+
Auditability
+
Business Metrics

Its central workflow is:

DETECT
→ DIAGNOSE
→ DECIDE
→ VALIDATE
→ ACT
→ MEASURE

The final demonstration must prove that this workflow works end-to-end.