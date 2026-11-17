"""
scripts/evaluate_model.py

ReviveAI — ML Recovery Probability Model Evaluation.
Computes measured quality metrics (ROC-AUC and Accuracy) on a held-out test set
using the production recovery model and processed training dataset.

Run from backend directory:
    python scripts/evaluate_model.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

DATA_FILE = ROOT_DIR / "data" / "processed" / "recovery_training.csv"
MODEL_FILE = BACKEND_DIR / "ml" / "models" / "recovery_model.joblib"

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


def evaluate_recovery_model() -> dict[str, float | int]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at: {DATA_FILE}")
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Model artifact not found at: {MODEL_FILE}")

    df = pd.read_csv(DATA_FILE)
    model = joblib.load(MODEL_FILE)

    # Filter to recovery-eligible population (consistent with model scope)
    eligible = df[df["recovery_eligible"] == 1].copy()
    if len(eligible) == 0:
        raise ValueError("No recovery-eligible records found in dataset.")

    X = eligible[FEATURES]
    y = eligible["recovered"]

    # Use deterministic 80/20 train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = model.predict(X_test)

    roc_auc = float(roc_auc_score(y_test, probabilities))
    accuracy = float(accuracy_score(y_test, predictions))

    return {
        "roc_auc": roc_auc,
        "accuracy": accuracy,
        "total_eligible_samples": len(eligible),
        "test_samples": len(X_test),
        "train_samples": len(X_train),
    }


def main():
    metrics = evaluate_recovery_model()

    print("========================================")
    print("REVIVEAI MODEL EVALUATION")
    print("========================================")
    print("Metric: ROC-AUC")
    print(f"Score: {metrics['roc_auc']:.4f}")
    print(f"Evaluation Samples: {metrics['test_samples']}")
    print("Model: Recovery Probability Model")
    print(f"Supplementary Accuracy: {metrics['accuracy']:.4f}")
    print(f"Total Eligible Population: {metrics['total_eligible_samples']}")
    print("========================================")


if __name__ == "__main__":
    main()
