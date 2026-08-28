# ReviveAI — AI Agent Specification

## Razorpay Buildathon — Track 03: AI Revenue Recovery

Version: 1.0

---

# 1. Agent Identity

Agent Name:

ReviveAI Recovery Agent

Agent Type:

Bounded AI Decision and Workflow Agent

Primary Objective:

Identify the most appropriate recovery intervention for a revenue-at-risk case while operating within deterministic financial safety policies.

---

# 2. Agent Mission

The ReviveAI Recovery Agent investigates failed or at-risk payment cases and determines the most appropriate next step.

The agent must:

1. Understand the recovery case.
2. Gather relevant evidence.
3. Analyze customer and payment history.
4. Use the recovery probability model.
5. Diagnose the likely reason for revenue loss.
6. Recommend an appropriate recovery action.
7. Explain the recommendation.
8. Identify whether human intervention is appropriate.
9. Produce a structured decision.
10. Hand the decision to the Guardrail Engine.

The agent does NOT have authority to override deterministic financial policies.

---

# 3. Agent Boundary

The agent operates between:

Recovery Case
and
Guardrail Engine.

Architecture:

```text
Recovery Case
      ↓
Context Builder
      ↓
Recovery Agent
      ↓
Structured Recommendation
      ↓
Schema Validation
      ↓
Guardrail Engine
      ↓
Action Executor
```

The agent cannot directly call unrestricted financial APIs.

---

# 4. Agent Input

The agent receives a structured Recovery Case.

Example:

```json
{
  "case_id": "REC-00142",
  "payment_id": "pay_demo_001",
  "customer_id": "cust_1024",
  "amount_at_risk": 2499,
  "currency": "INR",
  "payment_status": "failed",
  "failure_reason": "temporary_bank_failure",
  "retry_count": 0,
  "recovery_probability": 0.87
}
```

Additional context may be retrieved through tools.

---

# 5. Agent Context

The agent may receive:

## Payment Context

* Payment ID
* Amount
* Currency
* Payment status
* Payment method
* Failure code
* Failure description
* Attempt count
* Timestamp

## Customer Context

* Customer ID
* Account age
* Historical successful payments
* Historical failed payments
* Lifetime value
* Recent activity

## Subscription Context

* Subscription ID
* Plan
* Subscription amount
* Subscription status
* Current period
* Previous charge outcomes
* Retry count

## Recovery Context

* Previous recovery attempts
* Previous recovery actions
* Previous recovery results
* Current recovery case status

## ML Context

* Recovery probability
* Model version
* Relevant model features where appropriate

---

# 6. Agent Tools

The agent must access information through controlled tools.

Initial read-only tools:

```text
get_payment_details
get_customer_profile
get_payment_history
get_subscription_details
get_recovery_history
get_failure_reason
calculate_recovery_probability
```

Potential action-oriented tools:

```text
create_payment_link
send_payment_link_notification
escalate_case
stop_recovery
```

Action-oriented tools must themselves enforce authorization and policy validation.

---

# 7. Tool Access Principles

The agent follows least privilege.

The agent should only receive tools required for the current task.

The agent must not receive:

* Raw database access
* Arbitrary SQL execution
* Arbitrary MongoDB queries
* Shell access
* Arbitrary HTTP requests
* Unrestricted Razorpay credentials
* Direct access to secret values
* Arbitrary financial transaction execution

The agent interacts with controlled application tools.

---

# 8. Agent Workflow

The standard agent workflow is:

```text
START
  ↓
Load Recovery Case
  ↓
Validate Case
  ↓
Gather Required Context
  ↓
Analyze Failure
  ↓
Review Customer History
  ↓
Review Recovery History
  ↓
Obtain Recovery Probability
  ↓
Diagnose Revenue Risk
  ↓
Generate Candidate Actions
  ↓
Select Recommended Action
  ↓
Determine Confidence
  ↓
Determine Escalation Requirement
  ↓
Produce Structured Output
  ↓
Schema Validation
  ↓
Guardrail Engine
  ↓
END
```

---

# 9. Investigation Strategy

The agent should gather only the information needed to make a decision.

Example:

```text
Payment failed
      ↓
Get payment details
      ↓
Failure reason identified
      ↓
Get customer history
      ↓
Get previous recovery attempts
      ↓
Get recovery probability
      ↓
Decision
```

The agent should not repeatedly call tools without purpose.

---

# 10. Evidence-Based Reasoning

Agent recommendations must be based on available evidence.

Valid evidence may include:

* Payment failure reason
* Historical payment success rate
* Number of previous failures
* Retry count
* Customer lifetime value
* Recovery probability
* Subscription status
* Previous recovery outcomes

The agent must not invent missing evidence.

If important information is unavailable, the agent should state that the information is unavailable and consider escalation.

---

# 11. Diagnosis

The agent should identify the most likely cause of revenue risk.

Possible diagnosis categories include:

```text
TEMPORARY_PAYMENT_FAILURE

INSUFFICIENT_FUNDS

PAYMENT_METHOD_ISSUE

REPEATED_PAYMENT_FAILURE

SUBSCRIPTION_PAYMENT_FAILURE

CHECKOUT_ABANDONMENT

PAYMENT_DEGRADATION

UNKNOWN
```

The exact categories may evolve during implementation.

---

# 12. Recovery Actions

The agent may recommend only predefined actions.

Initial action set:

```text
RETRY_PAYMENT
PAYMENT_LINK_RECOVERY
SEND_PAYMENT_REMINDER
WAIT_FOR_COOLDOWN
ESCALATE_TO_HUMAN
STOP_RECOVERY
```

The final mapping to Razorpay APIs must be handled by the Razorpay Integration Adapter.

---

# 13. Candidate Action Selection

The agent should consider:

1. Revenue amount
2. Failure reason
3. Recovery probability
4. Previous attempts
5. Customer history
6. Subscription state
7. Recovery history
8. Applicable policies

Example:

```text
Amount:
₹2,499

Recovery probability:
87%

Previous retries:
0

Failure:
Temporary

Customer history:
Strong

Candidate actions:
- Retry
- Reminder
- Escalate

Recommended:
PAYMENT_LINK_RECOVERY
```

The recommendation is then passed to the Guardrail Engine.

---

# 14. Structured Agent Output

The agent must return structured output.

Example:

```json
{
  "case_id": "REC-00142",
  "diagnosis": {
    "category": "TEMPORARY_PAYMENT_FAILURE",
    "summary": "The payment appears to have failed due to a temporary issue."
  },
  "recovery_probability": 0.87,
  "recommended_action": "PAYMENT_LINK_RECOVERY",
  "confidence": 0.91,
  "reason": "The customer has a strong historical payment record and has not previously undergone recovery attempts.",
  "requires_human_approval": false
}
```

---

# 15. Output Schema

The application must validate the agent output before using it.

Conceptual schema:

```text
case_id
diagnosis
diagnosis.category
diagnosis.summary
recovery_probability
recommended_action
confidence
reason
requires_human_approval
```

Invalid output must not reach the Action Executor.

---

# 16. Agent Confidence

The agent should produce a confidence value.

Confidence represents confidence in the recommendation, not financial certainty.

Example:

```text
0.91
```

The system must distinguish:

```text
Recovery Probability
```

from:

```text
Agent Recommendation Confidence
```

These are different values.

Example:

```text
Recovery probability:
0.87

Agent confidence:
0.91
```

---

# 17. Recovery Probability vs Agent Confidence

Recovery probability asks:

"How likely is this revenue to be recovered?"

Agent confidence asks:

"How confident is the agent that its recommended intervention is appropriate?"

These values must not be confused.

---

# 18. Agent Decision Categories

The agent should ultimately recommend one of:

```text
ACT
WAIT
ESCALATE
STOP
```

Examples:

### ACT

The case appears suitable for a permitted recovery intervention.

### WAIT

A cooldown or external condition must be satisfied.

### ESCALATE

Human review is appropriate.

### STOP

Further automated recovery is not justified.

---

# 19. Example: ACT

Input:

```text
Amount:
₹2,499

Recovery probability:
0.87

Previous retries:
0

Failure:
Temporary

Customer history:
Strong
```

Agent:

```text
Diagnosis:
Temporary payment failure

Recommendation:
PAYMENT_LINK_RECOVERY

Confidence:
0.91

Decision:
ACT
```

Guardrails then determine whether ACT is actually allowed.

---

# 20. Example: WAIT

Input:

```text
Amount:
₹1,999

Recovery probability:
0.84

Previous retry:
1

Cooldown:
Not completed
```

Agent:

```text
Recommendation:
WAIT_FOR_COOLDOWN

Decision:
WAIT
```

No external financial action should be executed.

---

# 21. Example: ESCALATE

Input:

```text
Amount:
₹25,000

Recovery probability:
0.79

Customer history:
Mixed
```

Agent:

```text
Recommendation:
ESCALATE_TO_HUMAN

Decision:
ESCALATE
```

The high amount and lower confidence make automatic intervention inappropriate under the prototype policy.

---

# 22. Example: STOP

Input:

```text
Amount:
₹2,499

Recovery probability:
0.21

Previous retries:
2

Multiple previous failures
```

Agent:

```text
Recommendation:
STOP_RECOVERY

Decision:
STOP
```

The system should not continue retrying indefinitely.

---

# 23. Guardrail Boundary

The most important agent boundary is:

```text
AI Recommendation
       ↓
Schema Validation
       ↓
Guardrail Engine
       ↓
APPROVED?
       ↓
Action Executor
```

The agent cannot:

* Change limits
* Change retry counts
* Change cooldowns
* Approve itself
* Disable guardrails
* Execute blocked actions

---

# 24. Guardrail Rejection

The Guardrail Engine may reject an otherwise reasonable AI recommendation.

Example:

```text
AI:
PAYMENT_LINK_RECOVERY

Confidence:
0.91

Amount:
₹15,000
```

Guardrail:

```text
Automatic recovery limit:
₹5,000

Result:
BLOCKED
```

Final state:

```text
ESCALATED
```

The AI recommendation remains recorded for auditability.

---

# 25. Tool Failure Handling

If a read-only tool fails:

```text
Tool failure
     ↓
Retry according to controlled infrastructure policy
     ↓
If still unavailable
     ↓
Agent cannot safely decide
     ↓
ESCALATE / WAIT
```

The agent must not invent the missing information.

---

# 26. LLM Failure Handling

If the LLM is unavailable:

```text
LLM unavailable
     ↓
No AI recommendation
     ↓
Recovery case remains pending
     ↓
Human review or safe fallback
```

The system must never automatically execute a financial action because the LLM failed.

---

# 27. Invalid Output Handling

If the LLM produces malformed output:

```text
LLM
 ↓
Invalid JSON / invalid schema
 ↓
Reject output
 ↓
Record failure
 ↓
Retry controlled generation if configured
 ↓
If unsuccessful
 ↓
Escalate
```

No financial action should occur from invalid AI output.

---

# 28. Hallucination Prevention

The agent must only use information supplied by:

* Recovery Case
* Controlled tools
* ML model
* Trusted application state

The agent must not invent:

* Payment status
* Customer history
* Transaction amount
* Recovery results
* Razorpay responses
* Financial metrics

If evidence is missing:

```text
UNKNOWN
```

or:

```text
ESCALATE
```

should be preferred over guessing.

---

# 29. Financial Value Integrity

The LLM must never be the authoritative source for:

* Payment amount
* Revenue recovered
* Transaction status
* Currency
* Payment ID
* Subscription ID
* Financial totals

These values must come from application data or verified Razorpay responses.

---

# 30. Recovery Verification

The agent may recommend recovery.

It cannot declare revenue recovered.

Revenue is considered recovered only after the application verifies a successful payment event.

Example:

```text
Agent:
"Recommend recovery"

        ↓

Guardrail:
APPROVED

        ↓

Razorpay:
Payment Link created

        ↓

Customer:
Completes payment

        ↓

Razorpay:
Successful payment event

        ↓

Application:
Verifies event

        ↓

Revenue:
RECOVERED
```

---

# 31. Agent Memory

The agent should not maintain uncontrolled long-term conversational memory.

Relevant case information should be stored in the application database.

The agent retrieves required state through controlled tools.

This ensures:

* Reproducibility
* Auditability
* Predictability
* Easier testing

---

# 32. Agent State

The agent workflow may use states such as:

```text
IDLE
INVESTIGATING
ANALYZING
RECOMMENDING
WAITING
ESCALATING
COMPLETED
FAILED
```

Agent state should not replace the authoritative Recovery Case state.

The Recovery Case remains the source of truth.

---

# 33. Agent Loop

The conceptual agent loop is:

```text
OBSERVE
   ↓
RETRIEVE
   ↓
ANALYZE
   ↓
DECIDE
   ↓
PROPOSE
   ↓
VALIDATE
   ↓
ACT
   ↓
OBSERVE RESULT
```

For financial actions, the VALIDATE step is mandatory.

---

# 34. Agent Loop Example

```text
OBSERVE:
Payment failed.

RETRIEVE:
Customer history.

RETRIEVE:
Payment history.

RETRIEVE:
Recovery history.

ANALYZE:
Customer historically succeeds.

PREDICT:
Recovery probability = 0.87.

DECIDE:
Payment-link recovery appears appropriate.

PROPOSE:
PAYMENT_LINK_RECOVERY.

VALIDATE:
Guardrail Engine approves.

ACT:
Create recovery payment link.

OBSERVE:
Payment captured.

MEASURE:
Revenue recovered = ₹2,499.
```

---

# 35. Agent Tool Policy

Read tools should be preferred over action tools.

The agent should gather sufficient evidence before recommending an action.

A financial action tool should only become available after the application has established that the case is eligible.

Where practical:

```text
Read tools
→ available during investigation

Action tools
→ available only after policy validation
```

---

# 36. Prompt Design

The production agent prompt should emphasize:

* Role
* Goal
* Available evidence
* Available actions
* Tool usage
* Structured output
* Financial safety
* No hallucination
* No policy modification
* Escalation behavior

The exact production prompt will be stored separately from application code.

Recommended location:

```text
backend/app/agents/prompts/
```

---

# 37. Prompt Versioning

Agent prompts should be versioned.

Example:

```text
recovery_agent_v1
recovery_agent_v2
```

Agent actions should record the prompt/model version where appropriate.

This allows future evaluation of changes.

---

# 38. Model Configuration

The LLM provider should be configurable.

The application should not tightly couple the agent to one model provider.

Conceptual configuration:

```text
LLM_PROVIDER
LLM_MODEL
LLM_TEMPERATURE
```

Secrets must remain in environment variables.

---

# 39. Temperature and Determinism

Because the agent is used in a financial workflow:

* Prefer low randomness.
* Use structured output.
* Validate every response.
* Keep business rules deterministic.

The exact LLM temperature will be selected during implementation and evaluation.

---

# 40. Agent Evaluation

The agent must be evaluated independently from the ML model.

Evaluation categories:

## Diagnosis

Did the agent correctly identify the likely problem?

## Recommendation

Did the agent select an appropriate recovery action?

## Escalation

Did the agent correctly identify high-risk cases?

## Stop Decision

Did the agent stop when continued recovery was inappropriate?

## Tool Usage

Did the agent use relevant tools efficiently?

## Safety

Did the agent produce actions that violated policy?

---

# 41. Agent Evaluation Dataset

Create a fixed evaluation set containing scenarios such as:

```text
Temporary failure
Insufficient funds
Repeated failure
High-value payment
Low recovery probability
Cooldown active
Previous recovery success
Previous recovery failure
Unknown failure
Payment degradation
```

Each scenario should have an expected outcome.

---

# 42. Agent Evaluation Example

Scenario:

```text
Amount:
₹2,499

Recovery probability:
0.88

Retries:
0

Failure:
Temporary

Customer history:
Strong
```

Expected:

```text
Recommendation:
PAYMENT_LINK_RECOVERY

Decision:
ACT
```

The agent passes if its recommendation matches an acceptable action.

---

# 43. Agent Safety Metrics

Important metrics:

```text
Guardrail violation rate

Unauthorized action rate

Invalid action rate

Hallucinated financial fact rate

Incorrect escalation rate

Incorrect stop rate
```

Primary safety objective:

```text
Unauthorized financial actions = 0
```

---

# 44. Agent Business Metrics

The agent should ultimately contribute to:

```text
Revenue recovered

Recovery rate

Recovery attempts

Successful recovery rate

Average recovery value

Human escalation rate

Time to recovery
```

---

# 45. Agent Audit Requirements

Every agent decision should record:

```text
case_id

agent_version

model

timestamp

tools_used

diagnosis

recovery_probability

recommended_action

confidence

reason

policy_result

execution_result
```

The full private chain-of-thought must NOT be stored as an audit requirement.

The system should store a concise decision explanation and the evidence used.

---

# 46. Explanation Requirements

The merchant-facing explanation should be concise and evidence-based.

Good:

```text
The payment failed due to a temporary issue.
The customer has completed 9 previous payments successfully.
No recovery attempt has been made yet.
Recovery probability is 87%.
A payment-link recovery was recommended.
```

Bad:

```text
I thought deeply about the payment and decided...
```

The merchant should receive a decision summary, not hidden internal reasoning.

---

# 47. Agent Safety Invariants

The following must always remain true:

1. AI cannot bypass guardrails.
2. AI cannot modify financial limits.
3. AI cannot declare revenue recovered.
4. AI cannot invent financial facts.
5. AI cannot directly access secrets.
6. AI cannot execute arbitrary HTTP requests.
7. AI cannot perform unlimited retries.
8. AI cannot disable human approval.
9. Invalid AI output cannot trigger financial actions.
10. Unverified payment success cannot become recovered revenue.

---

# 48. Golden Recovery Workflow

The primary agent workflow is:

```text
Payment Failure
      ↓
Recovery Case
      ↓
Gather Evidence
      ↓
Recovery Probability
      ↓
AI Diagnosis
      ↓
AI Recommendation
      ↓
Schema Validation
      ↓
Guardrail Validation
      ↓
Controlled Action
      ↓
Razorpay Event
      ↓
Verification
      ↓
Revenue Recovered
      ↓
Audit
```

---

# 49. Golden Demo

Example:

```text
Customer:
CUST-1024

Payment:
₹2,499

Status:
FAILED

Failure:
Temporary bank failure

Historical successful payments:
9

Historical failures:
1

Recovery probability:
87%

AI recommendation:
PAYMENT_LINK_RECOVERY

AI confidence:
91%

Guardrail:
APPROVED

Action:
Payment Link created

Customer:
Payment completed

Verification:
SUCCESS

Revenue recovered:
₹2,499
```

---

# 50. Agent Design Principle

ReviveAI must not attempt to maximize autonomy.

It should maximize:

```text
SAFE AUTONOMY
```

The agent should act automatically when:

* Evidence is sufficient.
* Confidence is sufficient.
* The action is predefined.
* Policy allows the action.
* The action can be verified.

The agent should wait, stop or escalate when these conditions are not satisfied.

---

# 51. Final Agent Architecture

```text
                  ┌──────────────────┐
                  │  Recovery Case   │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Context Builder  │
                  └────────┬─────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    Recovery Agent     │
                │                       │
                │ Observe               │
                │ Retrieve              │
                │ Analyze               │
                │ Diagnose              │
                │ Recommend             │
                └───────────┬───────────┘
                            │
                 ┌──────────┴───────────┐
                 │                      │
                 ▼                      ▼
          Controlled Tools         ML Model
                 │                      │
                 └──────────┬───────────┘
                            │
                            ▼
                   Structured Output
                            │
                            ▼
                   Schema Validation
                            │
                            ▼
                  ┌──────────────────┐
                  │ Guardrail Engine │
                  └────────┬─────────┘
                           │
                 ┌─────────┼──────────┐
                 ▼         ▼          ▼
              APPROVE     WAIT     ESCALATE
                 │
                 ▼
          Action Executor
                 │
                 ▼
          Razorpay Adapter
                 │
                 ▼
           Razorpay Test
                 │
                 ▼
             Webhooks
                 │
                 ▼
             Verification
                 │
                 ▼
        Metrics + Audit Trail
```

---

# 52. Definition of Done

The AI Agent implementation is considered complete when:

* The agent can investigate a Recovery Case.
* The agent can use controlled tools.
* The agent can produce structured output.
* Output is schema validated.
* Diagnosis is evidence-based.
* Recovery probability is separated from agent confidence.
* The agent cannot bypass guardrails.
* Financial actions require deterministic validation.
* Revenue is only marked recovered after verification.
* Invalid AI output cannot trigger actions.
* Agent failures fail safely.
* Decisions are auditable.
* Agent behavior can be evaluated using a fixed test set.

---

# 53. Agent North Star

The ReviveAI Recovery Agent should demonstrate:

```text
OBSERVE
→ UNDERSTAND
→ RECOMMEND
→ VALIDATE
→ ACT
→ VERIFY
→ LEARN FROM OUTCOME
```

while maintaining:

```text
NO UNAUTHORIZED FINANCIAL ACTIONS
```

The purpose of the agent is not to replace financial controls.

The purpose of the agent is to make revenue recovery intelligent while keeping financial authority deterministic and auditable.
