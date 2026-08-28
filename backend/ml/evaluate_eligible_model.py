from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


# ============================================================
# Paths
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
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
# Features
# ============================================================

FEATURES = [
    "amount",
    "currency",
    "payment_method",
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
]


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 70)
    print("REVIVEAI ELIGIBLE HOLDOUT EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = pd.read_csv(DATA_FILE)

    model = joblib.load(MODEL_FILE)

    # --------------------------------------------------------
    # Eligible population
    # --------------------------------------------------------

    eligible = df[
        df["recovery_eligible"] == 1
    ].copy()

    print(
        f"\nEligible cases: "
        f"{len(eligible):,}"
    )

    # --------------------------------------------------------
    # Recreate deterministic test split
    # --------------------------------------------------------

    X = eligible[FEATURES]

    y = eligible["recovered"]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    print(
        f"Training reference: "
        f"{len(X_train):,}"
    )

    print(
        f"Holdout cases:      "
        f"{len(X_test):,}"
    )

    # --------------------------------------------------------
    # Predictions on unseen holdout
    # --------------------------------------------------------

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    print("\n" + "=" * 70)
    print("UNSEEN ELIGIBLE HOLDOUT PERFORMANCE")
    print("=" * 70)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print(
        f"ROC-AUC:  {roc_auc:.4f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=[
                "Not Recovered",
                "Recovered",
            ],
            zero_division=0,
        )
    )

    print(
        "Confusion Matrix:"
    )

    print(
        confusion_matrix(
            y_test,
            predictions,
        )
    )

    # --------------------------------------------------------
    # Revenue ranking
    # --------------------------------------------------------

    test_data = X_test.copy()

    test_data["actual_recovered"] = (
        y_test.values
    )

    test_data["predicted_probability"] = (
        probabilities
    )

    test_data["expected_recovery_value"] = (
        test_data["amount"]
        * test_data["predicted_probability"]
    )

    # --------------------------------------------------------
    # Top 10%
    # --------------------------------------------------------

    top_10_count = max(
        1,
        int(
            len(test_data)
            * 0.10
        ),
    )

    top_10 = (
        test_data
        .sort_values(
            "expected_recovery_value",
            ascending=False,
        )
        .head(top_10_count)
    )

    total_actual_recovered_revenue = (
        test_data.loc[
            test_data["actual_recovered"] == 1,
            "amount",
        ]
        .sum()
    )

    top_10_actual_recovered_revenue = (
        top_10.loc[
            top_10["actual_recovered"] == 1,
            "amount",
        ]
        .sum()
    )

    revenue_capture = (
        top_10_actual_recovered_revenue
        / total_actual_recovered_revenue
        * 100
        if total_actual_recovered_revenue > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("REVENUE RANKING")
    print("=" * 70)

    print(
        f"\nTop 10% cases: "
        f"{len(top_10):,}"
    )

    print(
        "Actual recovered revenue in "
        f"top 10%: ₹"
        f"{top_10_actual_recovered_revenue:,.2f}"
    )

    print(
        "Total recovered revenue in "
        f"holdout: ₹"
        f"{total_actual_recovered_revenue:,.2f}"
    )

    print(
        f"Revenue captured by top 10%: "
        f"{revenue_capture:.2f}%"
    )

    # --------------------------------------------------------
    # Top opportunities
    # --------------------------------------------------------

    print(
        "\nTop 10 ranked opportunities:"
    )

    print(
        top_10[
            [
                "amount",
                "failure_reason",
                "predicted_probability",
                "expected_recovery_value",
                "actual_recovered",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print(
        "HOLDOUT EVALUATION: COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()