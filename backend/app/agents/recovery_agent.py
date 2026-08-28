from typing import Any

from app.agents.core.agent_state import (
    AgentState,
)

from app.agents.tools.recovery_tools import (
    get_payment,
    check_payment_eligibility,
    predict_recovery,
    calculate_payment_revenue_risk,
    make_payment_recovery_decision,
)


class RecoveryAgent:
    """
    ReviveAI recovery investigation agent.

    Responsibilities:

    1. Retrieve payment information.
    2. Check recovery eligibility.
    3. Predict recovery probability.
    4. Calculate revenue risk.
    5. Produce a recovery decision.

    The agent does not directly modify payment records.
    """

    def investigate(
        self,
        payment_id: str,
    ) -> dict[str, Any]:

        state = AgentState(
            payment_id=payment_id
        )

        # ====================================================
        # STEP 1 — Retrieve payment
        # ====================================================

        state.status = (
            "retrieving_payment"
        )

        payment_result = get_payment(
            payment_id
        )

        state.actions_taken.append(
            "get_payment"
        )

        if not payment_result.get(
            "found",
            False,
        ):

            state.errors.append(
                "Payment not found."
            )

            state.status = "failed"

            return self._build_response(
                state
            )

        state.payment = (
            payment_result["payment"]
        )

        # ====================================================
        # STEP 2 — Eligibility
        # ====================================================

        state.status = (
            "checking_eligibility"
        )

        eligibility = (
            check_payment_eligibility(
                payment_id
            )
        )

        state.actions_taken.append(
            "check_payment_eligibility"
        )

        state.eligibility = (
            eligibility
        )

        # ====================================================
        # STOP if not eligible
        # ====================================================

        if not eligibility.get(
            "eligible",
            False,
        ):

            state.status = (
                "decision_complete"
            )

            decision_result = (
                make_payment_recovery_decision(
                    payment_id
                )
            )

            state.actions_taken.append(
                "make_payment_recovery_decision"
            )

            if decision_result.get(
                "success",
                False,
            ):

                state.decision = (
                    decision_result[
                        "decision"
                    ]
                )

            return self._build_response(
                state
            )

        # ====================================================
        # STEP 3 — ML prediction
        # ====================================================

        state.status = (
            "predicting_recovery"
        )

        prediction = predict_recovery(
            payment_id
        )

        state.actions_taken.append(
            "predict_recovery"
        )

        if not prediction.get(
            "success",
            False,
        ):

            state.errors.append(
                prediction.get(
                    "error",
                    "Recovery prediction failed.",
                )
            )

            state.status = "failed"

            return self._build_response(
                state
            )

        state.prediction = (
            prediction
        )

        # ====================================================
        # STEP 4 — Revenue risk
        # ====================================================

        state.status = (
            "calculating_revenue_risk"
        )

        revenue_risk = (
            calculate_payment_revenue_risk(
                payment_id
            )
        )

        state.actions_taken.append(
            "calculate_payment_revenue_risk"
        )

        if not revenue_risk.get(
            "success",
            False,
        ):

            state.errors.append(
                revenue_risk.get(
                    "error",
                    "Revenue risk calculation failed.",
                )
            )

            state.status = "failed"

            return self._build_response(
                state
            )

        state.revenue_risk = (
            revenue_risk
        )

        # ====================================================
        # STEP 5 — Final decision
        # ====================================================

        state.status = (
            "making_recovery_decision"
        )

        decision_result = (
            make_payment_recovery_decision(
                payment_id
            )
        )

        state.actions_taken.append(
            "make_payment_recovery_decision"
        )

        if not decision_result.get(
            "success",
            False,
        ):

            state.errors.append(
                decision_result.get(
                    "error",
                    "Recovery decision failed.",
                )
            )

            state.status = "failed"

            return self._build_response(
                state
            )

        state.decision = (
            decision_result[
                "decision"
            ]
        )

        state.status = (
            "decision_complete"
        )

        return self._build_response(
            state
        )

    # ========================================================
    # Response builder
    # ========================================================

    def _build_response(
        self,
        state: AgentState,
    ) -> dict[str, Any]:

        return {
            "payment_id": state.payment_id,
            "status": state.status,
            "payment": state.payment,
            "eligibility": state.eligibility,
            "prediction": state.prediction,
            "revenue_risk": state.revenue_risk,
            "decision": state.decision,
            "actions_taken": state.actions_taken,
            "errors": state.errors,
        }