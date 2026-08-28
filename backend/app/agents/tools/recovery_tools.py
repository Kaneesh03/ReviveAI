from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.domain.recovery.decision_engine import (
    make_recovery_decision,
)
from app.domain.recovery.eligibility import (
    evaluate_recovery_eligibility,
)
from app.domain.recovery.revenue_risk import (
    calculate_revenue_risk,
)


# ============================================================
# Paths
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[3]
ROOT_DIR = BACKEND_DIR.parent

DATA_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "recovery_training.csv"
)

MODEL_FILE = (
    BACKEND_DIR
    / "ml"
    / "models"
    / "recovery_model.joblib"
)


# ============================================================
# Model cache
# ============================================================

_model = None


def get_model():
    """Load the recovery model once and reuse it."""

    global _model

    if _model is None:

        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Recovery model not found: {MODEL_FILE}"
            )

        _model = joblib.load(
            MODEL_FILE
        )

    return _model


# ============================================================
# Payment lookup
# ============================================================

def get_payment(
    payment_id: str,
) -> dict[str, Any]:
    """
    Retrieve one payment by payment ID.

    Only decision-time information is returned.

    Future outcome fields such as:
        - recovered
        - recovered_amount
        - time_to_recovery_hours
        - recovery_probability_ground_truth

    are deliberately hidden from the agent.
    """

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Payment dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(
        DATA_FILE
    )

    matches = df[
        df["payment_id"] == payment_id
    ]

    if matches.empty:

        return {
            "found": False,
            "payment_id": payment_id,
        }

    payment = (
        matches.iloc[0]
        .to_dict()
    )

    # --------------------------------------------------------
    # Never expose future outcome information to the agent.
    # --------------------------------------------------------

    forbidden_future_fields = {
        "recovered",
        "recovered_amount",
        "time_to_recovery_hours",
        "recovery_probability_ground_truth",
    }

    payment = {
        key: value
        for key, value in payment.items()
        if key not in forbidden_future_fields
    }

    return {
        "found": True,
        "payment": payment,
    }


# ============================================================
# Eligibility
# ============================================================

def check_payment_eligibility(
    payment_id: str,
) -> dict[str, Any]:
    """
    Check whether a payment is eligible for recovery.
    """

    result = get_payment(
        payment_id
    )

    if not result["found"]:

        return {
            "payment_id": payment_id,
            "eligible": False,
            "reason": "payment_not_found",
        }

    payment = result["payment"]

    failure_reason = payment[
        "failure_reason"
    ]

    if pd.isna(failure_reason):
        failure_reason = None
    else:
        failure_reason = str(
            failure_reason
        )

    eligibility = (
        evaluate_recovery_eligibility(
            payment_status=str(
                payment["payment_status"]
            ),
            failure_reason=failure_reason,
            amount=float(
                payment["amount"]
            ),
            retry_count=int(
                payment["retry_count"]
            ),
            subscription_status=str(
                payment[
                    "subscription_status"
                ]
            ),
        )
    )

    return {
        "payment_id": payment_id,
        "eligible": eligibility.eligible,
        "reason": eligibility.reason,
    }


# ============================================================
# ML recovery prediction
# ============================================================

def predict_recovery(
    payment_id: str,
) -> dict[str, Any]:
    """
    Predict recovery probability for a failed payment.
    """

    result = get_payment(
        payment_id
    )

    if not result["found"]:

        return {
            "payment_id": payment_id,
            "success": False,
            "error": "Payment not found.",
        }

    payment = result["payment"]

    if payment["payment_status"] != "failed":

        return {
            "payment_id": payment_id,
            "success": False,
            "error": (
                "Recovery prediction is only "
                "available for failed payments."
            ),
        }

    # --------------------------------------------------------
    # Build model input.
    #
    # This must match the features used during training.
    # --------------------------------------------------------

    features = pd.DataFrame(
        [
            {
                "amount": float(
                    payment["amount"]
                ),
                "currency": str(
                    payment["currency"]
                ),
                "payment_method": str(
                    payment["payment_method"]
                ),
                "failure_reason": str(
                    payment["failure_reason"]
                ),
                "retry_count": int(
                    payment["retry_count"]
                ),
                "subscription_status": str(
                    payment["subscription_status"]
                ),
                "subscription_age_days": int(
                    payment[
                        "subscription_age_days"
                    ]
                ),
                "subscription_retry_count": int(
                    payment[
                        "subscription_retry_count"
                    ]
                ),
                "customer_age_days": int(
                    payment[
                        "customer_age_days"
                    ]
                ),
                "lifetime_value": float(
                    payment[
                        "lifetime_value"
                    ]
                ),
                "successful_payment_count": int(
                    payment[
                        "successful_payment_count"
                    ]
                ),
                "failed_payment_count": int(
                    payment[
                        "failed_payment_count"
                    ]
                ),
                "previous_recovery_attempts": int(
                    payment[
                        "previous_recovery_attempts"
                    ]
                ),
                "previous_recovery_successes": int(
                    payment[
                        "previous_recovery_successes"
                    ]
                ),
            }
        ]
    )

    model = get_model()

    probability = float(
        model.predict_proba(
            features
        )[0][1]
    )

    return {
        "payment_id": payment_id,
        "success": True,
        "recovery_probability": round(
            probability,
            4,
        ),
    }


# ============================================================
# Revenue risk
# ============================================================

def calculate_payment_revenue_risk(
    payment_id: str,
) -> dict[str, Any]:
    """
    Calculate revenue at risk and expected recovery value.
    """

    payment_result = get_payment(
        payment_id
    )

    if not payment_result["found"]:

        return {
            "payment_id": payment_id,
            "success": False,
            "error": "Payment not found.",
        }

    prediction = predict_recovery(
        payment_id
    )

    if not prediction["success"]:
        return prediction

    payment = payment_result[
        "payment"
    ]

    probability = float(
        prediction[
            "recovery_probability"
        ]
    )

    risk = calculate_revenue_risk(
        amount=float(
            payment["amount"]
        ),
        recovery_probability=probability,
    )

    return {
        "payment_id": payment_id,
        "success": True,
        "revenue_at_risk": risk.revenue_at_risk,
        "recovery_probability": (
            risk.recovery_probability
        ),
        "expected_recovery_value": (
            risk.expected_recovery_value
        ),
    }


# ============================================================
# Complete recovery decision
# ============================================================

def make_payment_recovery_decision(
    payment_id: str,
) -> dict[str, Any]:
    """
    Produce the complete recovery decision.

    Flow:

        Payment
           ↓
        Eligibility
           ↓
        ML prediction
           ↓
        Revenue risk
           ↓
        Decision engine
    """

    payment_result = get_payment(
        payment_id
    )

    if not payment_result["found"]:

        return {
            "payment_id": payment_id,
            "success": False,
            "error": "Payment not found.",
        }

    payment = payment_result[
        "payment"
    ]

    # --------------------------------------------------------
    # Eligibility
    # --------------------------------------------------------

    eligibility = (
        check_payment_eligibility(
            payment_id
        )
    )

    eligible = bool(
        eligibility["eligible"]
    )

    # --------------------------------------------------------
    # Ineligible case
    # --------------------------------------------------------

    if not eligible:

        decision = (
            make_recovery_decision(
                eligible=False,
                amount=float(
                    payment["amount"]
                ),
                recovery_probability=0.0,
                failure_reason=str(
                    payment[
                        "failure_reason"
                    ]
                ),
                retry_count=int(
                    payment["retry_count"]
                ),
                subscription_status=str(
                    payment[
                        "subscription_status"
                    ]
                ),
                lifetime_value=float(
                    payment[
                        "lifetime_value"
                    ]
                ),
            )
        )

        return {
            "payment_id": payment_id,
            "success": True,
            "eligibility": eligibility,
            "decision": asdict(
                decision
            ),
        }

    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    prediction = predict_recovery(
        payment_id
    )

    if not prediction["success"]:

        return prediction

    probability = float(
        prediction[
            "recovery_probability"
        ]
    )

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    decision = make_recovery_decision(
        eligible=True,
        amount=float(
            payment["amount"]
        ),
        recovery_probability=probability,
        failure_reason=str(
            payment[
                "failure_reason"
            ]
        ),
        retry_count=int(
            payment["retry_count"]
        ),
        subscription_status=str(
            payment[
                "subscription_status"
            ]
        ),
        lifetime_value=float(
            payment[
                "lifetime_value"
            ]
        ),
    )

    return {
        "payment_id": payment_id,
        "success": True,
        "eligibility": eligibility,
        "prediction": prediction,
        "decision": asdict(
            decision
        ),
    }