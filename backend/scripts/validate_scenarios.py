"""
scripts/validate_scenarios.py

ReviveAI - Multi-Scenario Validation

Run from the backend directory:

    python scripts/validate_scenarios.py

This script exercises three distinct validation layers:

  1. ELIGIBLE scenarios   - real failed-payment records run through
                            RecoveryAgent (eligibility + ML + decision).

  2. INELIGIBLE scenarios - real failed-payment records whose properties
                            make them ineligible.  Guardrail checks that
                            no retry action is ever recommended.

  3. POLICY-LAYER tests   - deterministic eligibility function called
                            directly for cases outside the recovery dataset
                            (e.g. successful payments).  The recovery API
                            intentionally contains only failed payments, so
                            these cases are validated at the policy layer,
                            not through the API.

  4. API-SCOPE tests      - nonexistent payment ID verified to return
                            not-found, confirming correct API error handling.

It does NOT modify the dataset, ML model, eligibility rules, or
any other business logic.  It is read-only validation.
"""
from __future__ import annotations

import sys
import os
import math

# Add backend root to path so imports work when called directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.recovery_agent import RecoveryAgent
from app.domain.recovery.eligibility import evaluate_recovery_eligibility


# ============================================================
# ELIGIBLE SCENARIOS (run through RecoveryAgent)
# IDs from data/processed/recovery_training.csv (failed payments only)
# ============================================================

ELIGIBLE_SCENARIOS = [
    {
        "label":             "High recovery (temp failure, high amount)",
        "payment_id":        "pay_002610",
        "expect_eligible":   True,
        "expect_action_not": ["DO_NOT_RETRY"],
        "description":       "temporary_bank_failure | active | retry=1 | amount=28100.45",
    },
    {
        "label":             "Temporary bank failure (low amount)",
        "payment_id":        "pay_000041",
        "expect_eligible":   True,
        "expect_action_not": ["DO_NOT_RETRY"],
        "description":       "temporary_bank_failure | active | retry=0 | amount=4274.20",
    },
    {
        "label":             "Network error (eligible)",
        "payment_id":        "pay_000039",
        "expect_eligible":   True,
        "expect_action_not": ["DO_NOT_RETRY"],
        "description":       "network_error | active | retry=1 | amount=2580.63",
    },
    {
        "label":             "Insufficient funds (eligible)",
        "payment_id":        "pay_000012",
        "expect_eligible":   True,
        "expect_action_not": ["DO_NOT_RETRY"],
        "description":       "insufficient_funds | active | retry=0 | amount=2004.43",
    },
]

# ============================================================
# INELIGIBLE SCENARIOS (run through RecoveryAgent)
# 5 real failed-payment records that must be blocked
# ============================================================

INELIGIBLE_SCENARIOS = [
    {
        "label":           "Permanent failure (payment_method_issue)",
        "payment_id":      "pay_000016",
        "expect_eligible": False,
        "expect_action":   "DO_NOT_RETRY",
        "description":     "payment_method_issue | active | retry=1 | amount=2942.43",
    },
    {
        "label":           "Permanent failure (repeated_failure)",
        "payment_id":      "pay_000049",
        "expect_eligible": False,
        "expect_action":   "DO_NOT_RETRY",
        "description":     "repeated_failure | active | retry=2 | amount=976.73",
    },
    {
        "label":           "Permanent failure (unknown_failure)",
        "payment_id":      "pay_000116",
        "expect_eligible": False,
        "expect_action":   "DO_NOT_RETRY",
        "description":     "unknown_failure | active | retry=1 | amount=3861.83",
    },
    {
        "label":           "Halted subscription",
        "payment_id":      "pay_000040",
        "expect_eligible": False,
        "expect_action":   "DO_NOT_RETRY",
        "description":     "network_error | HALTED sub | retry=1 | amount=2741.75",
    },
    {
        "label":           "Retry limit exceeded (retry=3)",
        "payment_id":      "pay_000062",
        "expect_eligible": False,
        "expect_action":   "DO_NOT_RETRY",
        "description":     "repeated_failure | active | retry=3 | amount=4823.33",
    },
]

# Combine for the agent loop
SCENARIOS = ELIGIBLE_SCENARIOS + INELIGIBLE_SCENARIOS

# ============================================================
# POLICY-LAYER SCENARIOS
# Tested by calling evaluate_recovery_eligibility() directly.
# These are NOT run through the recovery API because
# recovery_training.csv intentionally contains failed payments only.
# Successful payments return 404 from the API — that is correct
# API-scope behaviour, but it does NOT exercise the eligibility
# policy rule that rejects successful payments.  This section does.
# ============================================================

POLICY_SCENARIOS = [
    {
        "label":           "Successful payment (policy layer)",
        "description":     "payment_status=success | policy rejects before API scope",
        "kwargs": {
            "payment_status":      "success",
            "failure_reason":      None,
            "amount":              2000.00,
            "retry_count":         0,
            "subscription_status": "active",
        },
        "expect_eligible": False,
        "expect_reason":   "payment_not_failed",
    },
]

# ============================================================
# API-SCOPE SCENARIOS
# Nonexistent payment ID - tests API error handling only.
# ============================================================

API_SCOPE_SCENARIOS = [
    {
        "label":            "Unknown / nonexistent payment",
        "payment_id":       "pay_DOES_NOT_EXIST",
        "expect_not_found": True,
        "description":      "ID does not exist in the dataset",
    },
]


# ============================================================
# Helpers
# ============================================================

def _fmt_pct(v):
    if v is None:
        return "N/A"
    return "{:.2f}%".format(v * 100)


def _fmt_inr(v):
    if v is None:
        return "N/A"
    return "Rs.{:,.2f}".format(v)


def _check(condition, msg, results):
    status = "PASS" if condition else "FAIL"
    results.append((status, msg))
    marker = "[PASS]" if condition else "[FAIL]"
    print("    {}  {}".format(marker, msg))


def _approx_equal(a, b, rel_tol=1e-3):
    """Allow only normal floating-point rounding differences."""
    if a == 0 and b == 0:
        return True
    return math.isclose(a, b, rel_tol=rel_tol)


# ============================================================
# Main validation
# ============================================================

def run_validation():
    """Return number of failing checks."""

    agent = RecoveryAgent()

    sep    = "=" * 68
    subsep = "-" * 68

    print()
    print(sep)
    print("  REVIVEAI MULTI-SCENARIO VALIDATION")
    print(sep)

    # --- Column widths for summary table ---
    col_scenario  = 42
    col_id        = 20
    col_eligible  = 10
    col_prob      = 12
    col_priority  = 10
    col_action    = 22

    widths = [col_scenario, col_id, col_eligible, col_prob, col_priority, col_action]

    def _row(*cells):
        return "  " + "  ".join(
            str(c).ljust(w) for c, w in zip(cells, widths)
        )

    table_rows = []
    all_checks = []

    # ============================================================
    # LAYER 1: Agent-based scenarios (ELIGIBLE + INELIGIBLE)
    # Real failed-payment IDs run through RecoveryAgent
    # ============================================================

    print()
    print("  LAYER 1 -- AGENT-BASED SCENARIOS (4 eligible, 5 ineligible)")
    print("  " + subsep)
    print("  Data source: data/processed/recovery_training.csv (failed payments)")
    print()

    for scenario in SCENARIOS:
        payment_id        = scenario["payment_id"]
        label             = scenario["label"]
        expect_eligible   = scenario.get("expect_eligible")
        expect_action_not = scenario.get("expect_action_not", [])

        result = agent.investigate(payment_id)

        status      = result.get("status")
        payment     = result.get("payment") or {}
        eligibility = result.get("eligibility") or {}
        decision    = result.get("decision") or {}
        prediction  = result.get("prediction") or {}

        eligible = eligibility.get("eligible")
        prob     = decision.get("recovery_probability") if decision else None
        priority = decision.get("priority") if decision else "N/A"
        action   = decision.get("recommended_action") if decision else "N/A"
        rar      = decision.get("revenue_at_risk") if decision else None
        erv      = decision.get("expected_recovery_value") if decision else None
        amount   = payment.get("amount") if payment else None

        eligible_str = "YES" if eligible else ("NO" if eligible is False else "N/A")
        prob_str     = _fmt_pct(prob) if eligible else "N/A"

        table_rows.append(_row(
            label[:col_scenario],
            payment_id,
            eligible_str,
            prob_str,
            priority or "N/A",
            action or "N/A",
        ))

        print("\n  " + subsep)
        print("  SCENARIO: {}".format(label))
        print("  ID:       {}".format(payment_id))
        print("  Desc:     {}".format(scenario.get("description", "")))
        print()

        checks = []

        _check(bool(payment), "Payment retrieved successfully", checks)
        _check(
            status == "decision_complete",
            "Status is 'decision_complete' (got '{}')".format(status),
            checks,
        )

        actions_taken = result.get("actions_taken", [])
        _check("get_payment" in actions_taken, "Agent called get_payment tool", checks)

        if expect_eligible is True:
            _check(eligible is True, "Eligible=True as expected", checks)

            ml_prob = (prediction or {}).get("recovery_probability")
            _check(ml_prob is not None, "ML recovery_probability exists", checks)
            _check(
                0.0 <= (ml_prob or 0) <= 1.0,
                "ML probability in [0,1]: {}".format(ml_prob),
                checks,
            )

            if ml_prob is not None and prob is not None:
                _check(
                    _approx_equal(ml_prob, prob),
                    "Decision probability matches ML: {:.4f} approx {:.4f}".format(prob, ml_prob),
                    checks,
                )

            if amount is not None and prob is not None and erv is not None:
                expected_erv = round(amount * prob, 2)
                _check(
                    _approx_equal(expected_erv, erv, rel_tol=1e-3),
                    "expected_recovery_value = amount x prob: {} approx {}".format(
                        _fmt_inr(expected_erv), _fmt_inr(erv)
                    ),
                    checks,
                )

            if amount is not None and rar is not None:
                _check(
                    _approx_equal(amount, rar, rel_tol=1e-4),
                    "revenue_at_risk = amount: {} approx {}".format(
                        _fmt_inr(amount), _fmt_inr(rar)
                    ),
                    checks,
                )

            for banned in expect_action_not:
                _check(
                    action != banned,
                    "Action is NOT '{}' (guardrail: eligible must not be blocked)".format(banned),
                    checks,
                )

        elif expect_eligible is False:
            _check(eligible is False, "Eligible=False as expected", checks)

            # CRITICAL GUARDRAIL: ineligible payments must NEVER get RETRY_PAYMENT
            _check(
                action not in ("RETRY_PAYMENT", "RETRY_WITH_CAUTION"),
                "GUARDRAIL: ineligible payment does not recommend retry (got '{}')".format(action),
                checks,
            )
            _check(
                action == "DO_NOT_RETRY",
                "Action=DO_NOT_RETRY for ineligible (got '{}')".format(action),
                checks,
            )

            if erv is not None:
                _check(
                    erv == 0.0,
                    "expected_recovery_value=0.0 for ineligible (got {})".format(erv),
                    checks,
                )

        passes = sum(1 for s, _ in checks if s == "PASS")
        fails  = sum(1 for s, _ in checks if s == "FAIL")
        print("\n  Result: {} checks passed, {} failed".format(passes, fails))

        all_checks.extend(checks)

    # ============================================================
    # LAYER 2: Policy-layer scenarios
    # Direct calls to evaluate_recovery_eligibility().
    # NOT run through the recovery API because the recovery dataset
    # contains failed payments only.  Successful payments return 404
    # from the API -- that is correct API-scope behaviour -- but it
    # does NOT exercise the policy rule that rejects successful
    # payments.  This layer does.
    # ============================================================

    print()
    print(sep)
    print("  LAYER 2 -- POLICY-LAYER VALIDATION")
    print("  " + subsep)
    print("  Method: evaluate_recovery_eligibility() called directly")
    print("  Note:   The successful-payment case is validated at the")
    print("          deterministic eligibility-policy layer, NOT through")
    print("          the recovery API, because the recovery dataset")
    print("          intentionally contains failed payments only.")
    print()

    for scenario in POLICY_SCENARIOS:
        label          = scenario["label"]
        kwargs         = scenario["kwargs"]
        expect_eligible = scenario["expect_eligible"]
        expect_reason  = scenario.get("expect_reason")

        result = evaluate_recovery_eligibility(**kwargs)

        table_rows.append(_row(
            label[:col_scenario],
            "(policy layer)",
            "YES" if result.eligible else "NO",
            "N/A",
            "N/A",
            "N/A",
        ))

        print("\n  " + subsep)
        print("  SCENARIO: {}".format(label))
        print("  Desc:     {}".format(scenario.get("description", "")))
        print("  Input:    payment_status='{}'".format(kwargs.get("payment_status")))
        print()

        checks = []

        _check(
            result.eligible is expect_eligible,
            "eligible={} as expected (got {})".format(expect_eligible, result.eligible),
            checks,
        )

        if expect_reason:
            _check(
                result.reason == expect_reason,
                "reason='{}' as expected (got '{}')".format(expect_reason, result.reason),
                checks,
            )

        passes = sum(1 for s, _ in checks if s == "PASS")
        fails  = sum(1 for s, _ in checks if s == "FAIL")
        print("\n  Result: {} checks passed, {} failed".format(passes, fails))

        all_checks.extend(checks)

    # ============================================================
    # LAYER 3: API-scope scenarios
    # Nonexistent payment ID -- confirms correct API error handling.
    # ============================================================

    print()
    print(sep)
    print("  LAYER 3 -- API-SCOPE VALIDATION")
    print("  " + subsep)
    print("  Method: RecoveryAgent.investigate() with nonexistent payment ID")
    print()

    for scenario in API_SCOPE_SCENARIOS:
        payment_id = scenario["payment_id"]
        label      = scenario["label"]

        result  = agent.investigate(payment_id)
        status  = result.get("status")
        payment = result.get("payment") or {}

        table_rows.append(_row(
            label[:col_scenario],
            payment_id,
            "N/A",
            "N/A",
            "N/A",
            "NOT FOUND",
        ))

        print("\n  " + subsep)
        print("  SCENARIO: {}".format(label))
        print("  ID:       {}".format(payment_id))
        print("  Desc:     {}".format(scenario.get("description", "")))
        print()

        checks = []
        _check(
            status == "failed" and not payment,
            "Not-found: agent status=failed and no payment data returned",
            checks,
        )

        passes = sum(1 for s, _ in checks if s == "PASS")
        fails  = sum(1 for s, _ in checks if s == "FAIL")
        print("\n  Result: {} checks passed, {} failed".format(passes, fails))

        all_checks.extend(checks)

    # ============================================================
    # Summary table
    # ============================================================

    print()
    print(sep)
    print("  SUMMARY TABLE")
    print(sep)
    print()
    print("  Eligible scenarios (agent):    {} real failed payments".format(len(ELIGIBLE_SCENARIOS)))
    print("  Ineligible scenarios (agent):  {} real failed payments".format(len(INELIGIBLE_SCENARIOS)))
    print("  Policy-layer validation:       {} (successful-payment eligibility rule)".format(len(POLICY_SCENARIOS)))
    print("  API-scope validation:          {} (nonexistent payment -> not-found)".format(len(API_SCOPE_SCENARIOS)))
    print()
    print(_row("Scenario", "Payment ID", "Eligible", "Prob.", "Priority", "Action"))
    print("  " + "-" * (sum(widths) + 2 * len(widths)))
    for row in table_rows:
        print(row)
    print()

    # ============================================================
    # Overall result
    # ============================================================

    total_passes = sum(1 for s, _ in all_checks if s == "PASS")
    total_fails  = sum(1 for s, _ in all_checks if s == "FAIL")

    print(sep)
    if total_fails == 0:
        print("  [OK] VALIDATION COMPLETE -- {} checks passed, 0 failed".format(total_passes))
    else:
        print("  [!!] VALIDATION COMPLETE -- {} passed, {} FAILED".format(
            total_passes, total_fails
        ))
        print()
        print("  Failed checks:")
        for status, msg in all_checks:
            if status == "FAIL":
                print("    [FAIL] {}".format(msg))
    print(sep)
    print()

    return total_fails


if __name__ == "__main__":
    fails = run_validation()
    sys.exit(1 if fails else 0)

