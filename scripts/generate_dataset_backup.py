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

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"

RAW_DIR = OUTPUT_DIR / "raw"
PROCESSED_DIR = OUTPUT_DIR / "processed"

RAW_FILE = RAW_DIR / "payment_events.csv"
ML_FILE = PROCESSED_DIR / "recovery_training.csv"


# ============================================================
# Random generator
# ============================================================

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Helper functions
# ============================================================

def sigmoid(value: float) -> float:
    """Convert a value into a probability between 0 and 1."""
    return 1 / (1 + np.exp(-value))


def choose_payment_method() -> str:
    return rng.choice(
        ["card", "upi", "netbanking", "wallet"],
        p=[0.40, 0.40, 0.15, 0.05],
    )


def choose_failure_reason() -> str:
    return rng.choice(
        [
            "temporary_bank_failure",
            "insufficient_funds",
            "payment_method_issue",
            "network_error",
            "repeated_failure",
            "unknown_failure",
        ],
        p=[0.22, 0.24, 0.16, 0.16, 0.12, 0.10],
    )


def failure_is_permanent(reason: str) -> bool:
    return reason in {
        "payment_method_issue",
        "repeated_failure",
        "unknown_failure",
    }


# ============================================================
# Generate customers
# ============================================================

def generate_customers() -> pd.DataFrame:
    customer_ids = [
        f"cust_{i:05d}"
        for i in range(1, NUM_CUSTOMERS + 1)
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
            "successful_payment_count": successful_payment_count,
            "failed_payment_count": failed_payment_count,
        }
    )

    return customers


# ============================================================
# Generate payments
# ============================================================

def generate_payments(customers: pd.DataFrame) -> pd.DataFrame:
    customer_indexes = rng.integers(
        0,
        len(customers),
        size=NUM_PAYMENTS,
    )

    selected_customers = customers.iloc[
        customer_indexes
    ].reset_index(drop=True)

    payment_ids = [
        f"pay_{i:06d}"
        for i in range(1, NUM_PAYMENTS + 1)
    ]

    customer_ids = selected_customers["customer_id"]

    amounts = np.round(
        rng.lognormal(
            mean=np.log(2_500),
            sigma=0.75,
            size=NUM_PAYMENTS,
        ),
        2,
    )

    amounts = np.clip(amounts, 199, 50_000)

    payment_status = rng.choice(
        ["success", "failed"],
        size=NUM_PAYMENTS,
        p=[0.70, 0.30],
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
            failure_reasons.append(None)

    retry_counts = []

    for status, reason in zip(
        payment_status,
        failure_reasons,
    ):
        if status == "success":
            retry_counts.append(0)

        elif reason == "repeated_failure":
            retry_counts.append(
                int(rng.integers(1, 4))
            )

        else:
            retry_counts.append(
                int(rng.integers(0, 3))
            )

    subscription_ids = [
        f"sub_{customer_id}"
        for customer_id in customer_ids
    ]

    subscription_statuses = rng.choice(
        ["active", "pending", "halted"],
        size=NUM_PAYMENTS,
        p=[0.82, 0.13, 0.05],
    )

    subscription_age_days = rng.integers(
        30,
        1_200,
        size=NUM_PAYMENTS,
    )

    subscription_retry_counts = np.array(
        [
            int(rng.integers(0, 3))
            for _ in range(NUM_PAYMENTS)
        ]
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
            "subscription_status": subscription_statuses,
            "subscription_age_days": subscription_age_days,
            "subscription_retry_count": subscription_retry_counts,
        }
    )

    return payments


# ============================================================
# Generate recovery outcomes
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

        # Successful payments are not recovery cases.
        if row["payment_status"] == "success":

            recovery_eligible.append(0)
            recovery_probability.append(0.0)
            recovered.append(0)
            recovered_amount.append(0.0)
            time_to_recovery.append(0.0)
            previous_recovery_attempts.append(0)
            previous_recovery_successes.append(0)

            continue

        reason = row["failure_reason"]

        # ----------------------------------------------------
        # Previous recovery history
        # ----------------------------------------------------

        previous_attempts = int(
            rng.integers(
                0,
                max(1, int(row["retry_count"]) + 1),
            )
        )

        previous_successes = int(
            rng.integers(
                0,
                min(previous_attempts, 2) + 1,
            )
        )

        previous_recovery_attempts.append(
            previous_attempts
        )

        previous_recovery_successes.append(
            previous_successes
        )

        # ----------------------------------------------------
        # Recovery eligibility
        # ----------------------------------------------------

        eligible = (
            not failure_is_permanent(reason)
            and row["subscription_status"] != "halted"
            and row["retry_count"] < 3
            and row["amount"] <= 50_000
        )

        recovery_eligible.append(
            int(eligible)
        )

        # ----------------------------------------------------
        # Underlying recovery probability
        # ----------------------------------------------------

        score = -0.5

        # Strong customer history
        score += min(
            row["successful_payment_count"] / 20,
            1.5,
        )

        # Failed history reduces recovery chance
        score -= min(
            row["failed_payment_count"] / 10,
            1.2,
        )

        # Failure type
        if reason == "temporary_bank_failure":
            score += 1.2

        elif reason == "network_error":
            score += 0.9

        elif reason == "insufficient_funds":
            score += 0.4

        elif reason == "payment_method_issue":
            score -= 0.6

        elif reason == "repeated_failure":
            score -= 1.2

        else:
            score -= 0.4

        # Retry history
        score -= row["retry_count"] * 0.5

        # Previous successful recoveries are positive evidence
        score += previous_successes * 0.4

        # Large payments are slightly harder to recover
        if row["amount"] > 10_000:
            score -= 0.25

        # Active subscriptions are healthier
        if row["subscription_status"] == "active":
            score += 0.5

        probability = float(
            np.clip(sigmoid(score), 0.02, 0.98)
        )

        recovery_probability.append(
            round(probability, 4)
        )

        # ----------------------------------------------------
        # Generate eventual outcome
        # ----------------------------------------------------

        if eligible:
            did_recover = int(
                rng.random() < probability
            )
        else:
            did_recover = 0

        recovered.append(did_recover)

        if did_recover:
            recovered_amount.append(
                round(float(row["amount"]), 2)
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

    df["recovery_eligible"] = recovery_eligible
    df["recovery_probability_ground_truth"] = (
        recovery_probability
    )
    df["recovered"] = recovered
    df["recovered_amount"] = recovered_amount
    df["time_to_recovery_hours"] = time_to_recovery
    df["previous_recovery_attempts"] = (
        previous_recovery_attempts
    )
    df["previous_recovery_successes"] = (
        previous_recovery_successes
    )

    return df


# ============================================================
# Create decision-time ML dataset
# ============================================================

def create_ml_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:

    ml_df = df[
        df["payment_status"] == "failed"
    ].copy()

    # --------------------------------------------------------
    # IMPORTANT:
    # Do NOT include future information.
    #
    # The following columns are deliberately excluded:
    #
    # recovered
    # recovered_amount
    # time_to_recovery_hours
    # recovery_probability_ground_truth
    #
    # These represent future outcomes.
    # --------------------------------------------------------

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

    return ml_df[feature_columns].copy()


# ============================================================
# Validation
# ============================================================

def validate_dataset(
    raw_df: pd.DataFrame,
    ml_df: pd.DataFrame,
) -> None:

    assert len(raw_df) == NUM_PAYMENTS

    assert len(
        raw_df["payment_id"].unique()
    ) == NUM_PAYMENTS

    assert raw_df["amount"].min() >= 199

    assert raw_df["amount"].max() <= 50_000

    assert set(
        ml_df["payment_status"].unique()
    ) == {"failed"}

    assert "recovered_amount" not in ml_df.columns

    assert "time_to_recovery_hours" not in ml_df.columns

    assert (
        "recovery_probability_ground_truth"
        not in ml_df.columns
    )

    assert ml_df["recovered"].isin([0, 1]).all()

    print("Dataset validation: PASSED")


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("Generating ReviveAI synthetic dataset...")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Customers: {NUM_CUSTOMERS:,}")
    print(f"Payments: {NUM_PAYMENTS:,}")

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    customers = generate_customers()

    payments = generate_payments(
        customers
    )

    raw_df = generate_recovery_data(
        payments,
        customers,
    )

    ml_df = create_ml_dataset(
        raw_df
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
    print("Dataset generation complete.")
    print()
    print(f"Raw dataset:")
    print(f"  {RAW_FILE}")
    print()
    print(f"ML dataset:")
    print(f"  {ML_FILE}")
    print()
    print(f"Raw records: {len(raw_df):,}")
    print(f"Failed-payment records: {len(ml_df):,}")
    print()
    print(
        "Recovery-eligible cases:",
        int(ml_df["recovery_eligible"].sum()),
    )
    print(
        "Recovered cases:",
        int(ml_df["recovered"].sum()),
    )


if __name__ == "__main__":
    main()