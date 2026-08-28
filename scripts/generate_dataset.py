from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

RANDOM_SEED = 42

NUM_CUSTOMERS = 2_000
NUM_PAYMENTS = 20_000

OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
)

RAW_DIR = OUTPUT_DIR / "raw"
PROCESSED_DIR = OUTPUT_DIR / "processed"

RAW_FILE = RAW_DIR / "payment_events.csv"
ML_FILE = PROCESSED_DIR / "recovery_training.csv"


# ============================================================
# Random generator
# ============================================================

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Constants
# ============================================================

PAYMENT_METHODS = [
    "card",
    "upi",
    "netbanking",
    "wallet",
]

FAILURE_REASONS = [
    "temporary_bank_failure",
    "insufficient_funds",
    "payment_method_issue",
    "network_error",
    "repeated_failure",
    "unknown_failure",
]

PERMANENT_FAILURE_REASONS = {
    "payment_method_issue",
    "repeated_failure",
    "unknown_failure",
}


# ============================================================
# Helpers
# ============================================================

def sigmoid(value: float) -> float:
    """Convert a score into a probability between 0 and 1."""

    value = np.clip(
        value,
        -20,
        20,
    )

    return float(
        1.0 / (1.0 + np.exp(-value))
    )


def choose_payment_method() -> str:

    return str(
        rng.choice(
            PAYMENT_METHODS,
            p=[
                0.40,
                0.40,
                0.15,
                0.05,
            ],
        )
    )


def choose_failure_reason() -> str:

    return str(
        rng.choice(
            FAILURE_REASONS,
            p=[
                0.22,
                0.24,
                0.16,
                0.16,
                0.12,
                0.10,
            ],
        )
    )


def failure_is_permanent(
    reason: str,
) -> bool:

    return (
        reason
        in PERMANENT_FAILURE_REASONS
    )


# ============================================================
# Customers
# ============================================================

def generate_customers() -> pd.DataFrame:

    customer_ids = [
        f"cust_{i:05d}"
        for i in range(
            1,
            NUM_CUSTOMERS + 1,
        )
    ]

    customer_age_days = rng.integers(
        low=30,
        high=1_500,
        size=NUM_CUSTOMERS,
    )

    lifetime_value = np.round(
        rng.lognormal(
            mean=np.log(8_000),
            sigma=0.8,
            size=NUM_CUSTOMERS,
        ),
        2,
    )

    successful_payment_count = rng.poisson(
        lam=12,
        size=NUM_CUSTOMERS,
    )

    failed_payment_count = rng.poisson(
        lam=2,
        size=NUM_CUSTOMERS,
    )

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "customer_age_days": customer_age_days,
            "lifetime_value": lifetime_value,
            "successful_payment_count": (
                successful_payment_count
            ),
            "failed_payment_count": (
                failed_payment_count
            ),
        }
    )

    return customers


# ============================================================
# Payments
# ============================================================

def generate_payments(
    customers: pd.DataFrame,
) -> pd.DataFrame:

    customer_indexes = rng.integers(
        0,
        len(customers),
        size=NUM_PAYMENTS,
    )

    selected_customers = (
        customers
        .iloc[customer_indexes]
        .reset_index(drop=True)
    )

    payment_ids = [
        f"pay_{i:06d}"
        for i in range(
            1,
            NUM_PAYMENTS + 1,
        )
    ]

    customer_ids = (
        selected_customers[
            "customer_id"
        ]
    )

    amounts = np.round(
        rng.lognormal(
            mean=np.log(2_500),
            sigma=0.75,
            size=NUM_PAYMENTS,
        ),
        2,
    )

    amounts = np.clip(
        amounts,
        199,
        50_000,
    )

    payment_status = rng.choice(
        [
            "success",
            "failed",
        ],
        size=NUM_PAYMENTS,
        p=[
            0.70,
            0.30,
        ],
    )

    payment_methods = [
        choose_payment_method()
        for _ in range(NUM_PAYMENTS)
    ]

    failure_reasons = []

    for status in payment_status:

        if status == "failed":
            failure_reasons.append(
                choose_failure_reason()
            )
        else:
            failure_reasons.append(
                None
            )

    retry_counts = []

    for status, reason in zip(
        payment_status,
        failure_reasons,
    ):

        if status == "success":

            retry_counts.append(0)

        elif reason == "repeated_failure":

            retry_counts.append(
                int(
                    rng.integers(
                        1,
                        4,
                    )
                )
            )

        else:

            retry_counts.append(
                int(
                    rng.integers(
                        0,
                        3,
                    )
                )
            )

    subscription_ids = [
        f"sub_{customer_id}"
        for customer_id in customer_ids
    ]

    subscription_statuses = rng.choice(
        [
            "active",
            "pending",
            "halted",
        ],
        size=NUM_PAYMENTS,
        p=[
            0.82,
            0.13,
            0.05,
        ],
    )

    subscription_age_days = rng.integers(
        30,
        1_200,
        size=NUM_PAYMENTS,
    )

    subscription_retry_counts = rng.integers(
        0,
        3,
        size=NUM_PAYMENTS,
    )

    payment_dates = pd.date_range(
        end=pd.Timestamp.now().normalize(),
        periods=NUM_PAYMENTS,
        freq="h",
    )

    payments = pd.DataFrame(
        {
            "payment_id": payment_ids,
            "customer_id": customer_ids,
            "subscription_id": subscription_ids,
            "amount": amounts,
            "currency": "INR",
            "payment_method": payment_methods,
            "payment_status": payment_status,
            "failure_reason": failure_reasons,
            "retry_count": retry_counts,
            "created_at": payment_dates,
            "subscription_status": (
                subscription_statuses
            ),
            "subscription_age_days": (
                subscription_age_days
            ),
            "subscription_retry_count": (
                subscription_retry_counts
            ),
        }
    )

    return payments


# ============================================================
# Recovery history
# ============================================================

def generate_recovery_history(
    retry_count: int,
) -> tuple[int, int]:

    max_attempts = min(
        retry_count,
        2,
    )

    if max_attempts <= 0:

        return 0, 0

    attempts = int(
        rng.integers(
            0,
            max_attempts + 1,
        )
    )

    if attempts == 0:

        return 0, 0

    # Previous success is possible but not guaranteed.
    success_probability = 0.35

    successes = int(
        rng.binomial(
            attempts,
            success_probability,
        )
    )

    return attempts, successes


# ============================================================
# Recovery probability
# ============================================================

def calculate_recovery_probability(
    row: pd.Series,
    previous_attempts: int,
    previous_successes: int,
) -> float:

    """
    Generate the hidden ground-truth probability.

    IMPORTANT:
    This function only uses information that would be
    available at decision time.
    """

    score = 0.0

    # --------------------------------------------------------
    # Failure reason
    # --------------------------------------------------------

    reason = row["failure_reason"]

    if reason == "temporary_bank_failure":
        score += 1.20

    elif reason == "network_error":
        score += 0.95

    elif reason == "insufficient_funds":
        score += 0.45

    elif reason == "payment_method_issue":
        score -= 0.90

    elif reason == "repeated_failure":
        score -= 1.30

    elif reason == "unknown_failure":
        score -= 0.45

    # --------------------------------------------------------
    # Customer quality
    # --------------------------------------------------------

    successful_payments = (
        row["successful_payment_count"]
    )

    failed_payments = (
        row["failed_payment_count"]
    )

    score += np.clip(
        successful_payments / 15,
        0,
        1.5,
    )

    score -= np.clip(
        failed_payments / 8,
        0,
        1.5,
    )

    # --------------------------------------------------------
    # Customer age
    # --------------------------------------------------------

    if row["customer_age_days"] > 700:
        score += 0.35

    elif row["customer_age_days"] < 150:
        score -= 0.20

    # --------------------------------------------------------
    # Lifetime value
    # --------------------------------------------------------

    if row["lifetime_value"] > 15_000:
        score += 0.35

    elif row["lifetime_value"] < 3_000:
        score -= 0.15

    # --------------------------------------------------------
    # Retry count
    # --------------------------------------------------------

    score -= (
        row["retry_count"]
        * 0.45
    )

    # --------------------------------------------------------
    # Subscription
    # --------------------------------------------------------

    if row["subscription_status"] == "active":
        score += 0.55

    elif row["subscription_status"] == "pending":
        score += 0.10

    elif row["subscription_status"] == "halted":
        score -= 1.00

    # --------------------------------------------------------
    # Subscription history
    # --------------------------------------------------------

    score -= (
        row["subscription_retry_count"]
        * 0.20
    )

    if row["subscription_age_days"] > 600:
        score += 0.20

    # --------------------------------------------------------
    # Previous recovery history
    # --------------------------------------------------------

    score += (
        previous_successes
        * 0.65
    )

    score -= (
        max(
            previous_attempts
            - previous_successes,
            0,
        )
        * 0.20
    )

    # --------------------------------------------------------
    # Payment amount
    # --------------------------------------------------------

    if row["amount"] > 20_000:
        score -= 0.30

    elif row["amount"] < 1_000:
        score += 0.10

    # --------------------------------------------------------
    # Payment method
    # --------------------------------------------------------

    if row["payment_method"] == "upi":
        score += 0.10

    elif row["payment_method"] == "card":
        score += 0.05

    elif row["payment_method"] == "netbanking":
        score -= 0.05

    elif row["payment_method"] == "wallet":
        score -= 0.10

    # --------------------------------------------------------
    # Convert to probability
    # --------------------------------------------------------

    probability = sigmoid(
        score
    )

    return float(
        np.clip(
            probability,
            0.03,
            0.97,
        )
    )


# ============================================================
# Recovery outcomes
# ============================================================

def generate_recovery_data(
    payments: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:

    df = payments.merge(
        customers,
        on="customer_id",
        how="left",
    )

    recovery_eligible = []
    recovery_probability = []
    recovered = []
    recovered_amount = []
    time_to_recovery = []
    previous_recovery_attempts = []
    previous_recovery_successes = []

    for _, row in df.iterrows():

        # ----------------------------------------------------
        # Successful payment
        # ----------------------------------------------------

        if row["payment_status"] == "success":

            recovery_eligible.append(0)
            recovery_probability.append(0.0)
            recovered.append(0)
            recovered_amount.append(0.0)
            time_to_recovery.append(0.0)
            previous_recovery_attempts.append(0)
            previous_recovery_successes.append(0)

            continue

        # ----------------------------------------------------
        # Recovery history
        # ----------------------------------------------------

        attempts, successes = (
            generate_recovery_history(
                int(row["retry_count"])
            )
        )

        previous_recovery_attempts.append(
            attempts
        )

        previous_recovery_successes.append(
            successes
        )

        # ----------------------------------------------------
        # Eligibility policy
        # ----------------------------------------------------

        reason = row["failure_reason"]

        eligible = (
            not failure_is_permanent(
                reason
            )
            and row["subscription_status"]
            != "halted"
            and row["retry_count"] < 3
            and row["amount"] <= 50_000
        )

        recovery_eligible.append(
            int(eligible)
        )

        # ----------------------------------------------------
        # Ground truth probability
        # ----------------------------------------------------

        probability = (
            calculate_recovery_probability(
                row,
                attempts,
                successes,
            )
        )

        recovery_probability.append(
            round(
                probability,
                4,
            )
        )

        # ----------------------------------------------------
        # Outcome
        # ----------------------------------------------------

        if eligible:

            did_recover = int(
                rng.random()
                < probability
            )

        else:

            did_recover = 0

        recovered.append(
            did_recover
        )

        # ----------------------------------------------------
        # Future information
        # ----------------------------------------------------

        if did_recover:

            recovered_amount.append(
                round(
                    float(row["amount"]),
                    2,
                )
            )

            time_to_recovery.append(
                round(
                    float(
                        rng.uniform(
                            1,
                            72,
                        )
                    ),
                    2,
                )
            )

        else:

            recovered_amount.append(0.0)
            time_to_recovery.append(0.0)

    df[
        "recovery_eligible"
    ] = recovery_eligible

    df[
        "recovery_probability_ground_truth"
    ] = recovery_probability

    df[
        "recovered"
    ] = recovered

    df[
        "recovered_amount"
    ] = recovered_amount

    df[
        "time_to_recovery_hours"
    ] = time_to_recovery

    df[
        "previous_recovery_attempts"
    ] = previous_recovery_attempts

    df[
        "previous_recovery_successes"
    ] = previous_recovery_successes

    return df


# ============================================================
# ML dataset
# ============================================================

def create_ml_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:

    ml_df = df[
        df["payment_status"] == "failed"
    ].copy()

    feature_columns = [
        "payment_id",
        "customer_id",
        "subscription_id",
        "amount",
        "currency",
        "payment_method",
        "payment_status",
        "failure_reason",
        "retry_count",
        "subscription_status",
        "subscription_age_days",
        "subscription_retry_count",
        "customer_age_days",
        "lifetime_value",
        "successful_payment_count",
        "failed_payment_count",
        "previous_recovery_attempts",
        "previous_recovery_successes",
        "recovery_eligible",
        "recovered",
    ]

    return ml_df[
        feature_columns
    ].copy()


# ============================================================
# Validation
# ============================================================

def validate_dataset(
    raw_df: pd.DataFrame,
    ml_df: pd.DataFrame,
) -> None:

    assert len(raw_df) == NUM_PAYMENTS

    assert (
        raw_df["payment_id"].nunique()
        == NUM_PAYMENTS
    )

    assert (
        raw_df["amount"].min()
        >= 199
    )

    assert (
        raw_df["amount"].max()
        <= 50_000
    )

    assert set(
        ml_df["payment_status"].unique()
    ) == {"failed"}

    forbidden_columns = {
        "recovered_amount",
        "time_to_recovery_hours",
        "recovery_probability_ground_truth",
    }

    assert not (
        forbidden_columns
        & set(ml_df.columns)
    )

    assert (
        ml_df["recovered"]
        .isin([0, 1])
        .all()
    )

    assert (
        ml_df["recovery_eligible"]
        .isin([0, 1])
        .all()
    )

    # Ineligible cases must never be recovered.
    assert (
        ml_df.loc[
            ml_df["recovery_eligible"] == 0,
            "recovered",
        ]
        == 0
    ).all()

    print(
        "Dataset validation: PASSED"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print(
        "Generating ReviveAI synthetic dataset..."
    )

    print(
        f"Random seed: {RANDOM_SEED}"
    )

    print(
        f"Customers: {NUM_CUSTOMERS:,}"
    )

    print(
        f"Payments: {NUM_PAYMENTS:,}"
    )

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    customers = (
        generate_customers()
    )

    payments = (
        generate_payments(
            customers
        )
    )

    raw_df = (
        generate_recovery_data(
            payments,
            customers,
        )
    )

    ml_df = (
        create_ml_dataset(
            raw_df
        )
    )

    validate_dataset(
        raw_df,
        ml_df,
    )

    raw_df.to_csv(
        RAW_FILE,
        index=False,
    )

    ml_df.to_csv(
        ML_FILE,
        index=False,
    )

    print()
    print(
        "Dataset generation complete."
    )

    print()
    print(
        "Raw dataset:"
    )

    print(
        f"  {RAW_FILE}"
    )

    print()
    print(
        "ML dataset:"
    )

    print(
        f"  {ML_FILE}"
    )

    print()
    print(
        f"Raw records: {len(raw_df):,}"
    )

    print(
        "Failed-payment records:"
        f" {len(ml_df):,}"
    )

    print()

    print(
        "Recovery-eligible cases:",
        int(
            ml_df[
                "recovery_eligible"
            ].sum()
        ),
    )

    print(
        "Recovered cases:",
        int(
            ml_df[
                "recovered"
            ].sum()
        ),
    )


if __name__ == "__main__":
    main()