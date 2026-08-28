from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


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

MODEL_DIR = (
    BACKEND_DIR
    / "ml"
    / "models"
)

MODEL_FILE = (
    MODEL_DIR
    / "recovery_model.joblib"
)


# ============================================================
# Target
# ============================================================

TARGET = "recovered"


# ============================================================
# Features
# ============================================================

CATEGORICAL_FEATURES = [
    "currency",
    "payment_method",
    "failure_reason",
    "subscription_status",
]


NUMERICAL_FEATURES = [
    "amount",
    "retry_count",
    "subscription_age_days",
    "subscription_retry_count",
    "customer_age_days",
    "lifetime_value",
    "successful_payment_count",
    "failed_payment_count",
    "previous_recovery_attempts",
    "previous_recovery_successes",
]


FEATURES = (
    CATEGORICAL_FEATURES
    + NUMERICAL_FEATURES
)


# ============================================================
# Main training function
# ============================================================

def main() -> None:

    print("=" * 70)
    print("REVIVEAI RECOVERY MODEL TRAINING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print("\nLoading dataset...")

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    print(
        f"Dataset shape: {df.shape}"
    )

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    required_columns = set(
        FEATURES + [TARGET]
    )

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    # --------------------------------------------------------
    # Prepare features and target
    # --------------------------------------------------------

    X = df[FEATURES].copy()

    y = df[TARGET].copy()

    print(
        f"Features: {len(FEATURES)}"
    )

    print(
        f"Target: {TARGET}"
    )

    # --------------------------------------------------------
    # Target distribution
    # --------------------------------------------------------

    print("\nTarget distribution:")

    target_counts = (
        y.value_counts()
        .sort_index()
    )

    for label, count in target_counts.items():

        percentage = (
            count
            / len(y)
            * 100
        )

        label_name = (
            "Not recovered"
            if label == 0
            else "Recovered"
        )

        print(
            f"  {label_name:<18}"
            f"{count:>8,}"
            f" ({percentage:>6.2f}%)"
        )

    # --------------------------------------------------------
    # Train/test split
    # --------------------------------------------------------

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
        f"\nTraining records: {len(X_train):,}"
    )

    print(
        f"Testing records:  {len(X_test):,}"
    )

    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numerical",
                StandardScaler(),
                NUMERICAL_FEATURES,
            ),
        ]
    )

    # --------------------------------------------------------
    # Logistic Regression
    # --------------------------------------------------------

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    # --------------------------------------------------------
    # Pipeline
    # --------------------------------------------------------

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print(
        "\nTraining Logistic Regression..."
    )

    pipeline.fit(
        X_train,
        y_train,
    )

    print(
        "Training complete."
    )

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )

    probabilities = pipeline.predict_proba(
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

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("MODEL EVALUATION")
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
    # Save model
    # --------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        MODEL_FILE,
    )

    print(
        f"\nModel saved to:"
    )

    print(
        MODEL_FILE
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("MODEL TRAINING: COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()