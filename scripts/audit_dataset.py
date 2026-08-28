from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT_DIR / "data" / "raw" / "payment_events.csv"
ML_FILE = ROOT_DIR / "data" / "processed" / "recovery_training.csv"


# ============================================================
# Expected schema
# ============================================================

RAW_REQUIRED_COLUMNS = {
    "payment_id",
    "customer_id",
    "subscription_id",
    "amount",
    "currency",
    "payment_method",
    "payment_status",
    "failure_reason",
    "retry_count",
    "created_at",
    "subscription_status",
    "subscription_age_days",
    "subscription_retry_count",
    "customer_age_days",
    "lifetime_value",
    "successful_payment_count",
    "failed_payment_count",
    "recovery_eligible",
    "recovery_probability_ground_truth",
    "recovered",
    "recovered_amount",
    "time_to_recovery_hours",
    "previous_recovery_attempts",
    "previous_recovery_successes",
}


ML_REQUIRED_COLUMNS = {
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
}


# These columns represent future information.
# They must NOT exist in the ML dataset.

FORBIDDEN_ML_COLUMNS = {
    "recovered_amount",
    "time_to_recovery_hours",
    "recovery_probability_ground_truth",
}


VALID_PAYMENT_STATUSES = {
    "success",
    "failed",
}


VALID_PAYMENT_METHODS = {
    "card",
    "upi",
    "netbanking",
    "wallet",
}


VALID_SUBSCRIPTION_STATUSES = {
    "active",
    "pending",
    "halted",
}


VALID_FAILURE_REASONS = {
    "temporary_bank_failure",
    "insufficient_funds",
    "payment_method_issue",
    "network_error",
    "repeated_failure",
    "unknown_failure",
}


# ============================================================
# Formatting helpers
# ============================================================

def money(value: float) -> str:
    return f"₹{value:,.2f}"


def print_header(title: str) -> None:
    print()
    print(f"[{title}]")
    print("-" * 70)


def print_pass(message: str) -> None:
    print(f"PASS   {message}")


def print_fail(message: str) -> None:
    print(f"FAIL   {message}")


# ============================================================
# File validation
# ============================================================

def validate_files() -> bool:

    print_header("FILE VALIDATION")

    passed = True

    if RAW_FILE.exists():
        print_pass(f"Raw dataset found: {RAW_FILE.name}")
    else:
        print_fail(f"Raw dataset missing: {RAW_FILE}")
        passed = False

    if ML_FILE.exists():
        print_pass(f"ML dataset found: {ML_FILE.name}")
    else:
        print_fail(f"ML dataset missing: {ML_FILE}")
        passed = False

    return passed


# ============================================================
# Schema validation
# ============================================================

def validate_schema(
    raw: pd.DataFrame,
    ml: pd.DataFrame,
) -> bool:

    print_header("SCHEMA VALIDATION")

    passed = True

    missing_raw = RAW_REQUIRED_COLUMNS - set(raw.columns)

    if missing_raw:
        print_fail(
            "Raw dataset missing columns: "
            + ", ".join(sorted(missing_raw))
        )
        passed = False
    else:
        print_pass("Raw dataset contains all required columns.")

    missing_ml = ML_REQUIRED_COLUMNS - set(ml.columns)

    if missing_ml:
        print_fail(
            "ML dataset missing columns: "
            + ", ".join(sorted(missing_ml))
        )
        passed = False
    else:
        print_pass("ML dataset contains all required columns.")

    leakage_columns = (
        FORBIDDEN_ML_COLUMNS.intersection(
            ml.columns
        )
    )

    if leakage_columns:

        print_fail(
            "Future-information columns found in ML dataset: "
            + ", ".join(sorted(leakage_columns))
        )

        passed = False

    else:
        print_pass(
            "ML dataset contains no forbidden future-outcome columns."
        )

    return passed


# ============================================================
# Basic dataset information
# ============================================================

def show_dataset_size(
    raw: pd.DataFrame,
    ml: pd.DataFrame,
) -> None:

    print_header("DATASET SIZE")

    print(f"Raw records: {len(raw):,}")
    print(f"ML records:  {len(ml):,}")
    print(f"Raw columns: {len(raw.columns)}")
    print(f"ML columns:  {len(ml.columns)}")


# ============================================================
# Payment status analysis
# ============================================================

def analyze_payment_status(
    raw: pd.DataFrame,
) -> None:

    print_header("PAYMENT STATUS")

    status_counts = raw["payment_status"].value_counts()

    for status, count in status_counts.items():

        percentage = (
            count / len(raw) * 100
        )

        print(
            f"{status:<10}"
            f"{count:>8,}"
            f" ({percentage:>6.2f}%)"
        )


# ============================================================
# Failure analysis
# ============================================================

def analyze_failure_reasons(
    ml: pd.DataFrame,
) -> None:

    print_header("FAILURE REASONS")

    failure_counts = (
        ml["failure_reason"]
        .value_counts()
    )

    for reason, count in failure_counts.items():

        percentage = (
            count / len(ml) * 100
        )

        print(
            f"{reason:<30}"
            f"{count:>8,}"
            f" ({percentage:>6.2f}%)"
        )


# ============================================================
# Revenue analysis
# ============================================================

def analyze_revenue(
    raw: pd.DataFrame,
    ml: pd.DataFrame,
) -> dict:

    print_header("REVENUE")

    total_revenue = raw["amount"].sum()

    failed = raw[
        raw["payment_status"] == "failed"
    ]

    failed_revenue = failed["amount"].sum()

    eligible = ml[
        ml["recovery_eligible"] == 1
    ]

    eligible_revenue = eligible["amount"].sum()

    recovered = ml[
        ml["recovered"] == 1
    ]

    recovered_revenue = recovered["amount"].sum()

    print(
        f"Total payment value:   "
        f"{money(total_revenue)}"
    )

    print(
        f"Failed payment value:  "
        f"{money(failed_revenue)}"
    )

    print(
        f"Eligible revenue:      "
        f"{money(eligible_revenue)}"
    )

    print(
        f"Recovered revenue:     "
        f"{money(recovered_revenue)}"
    )

    return {
        "total_revenue": total_revenue,
        "failed_revenue": failed_revenue,
        "eligible_revenue": eligible_revenue,
        "recovered_revenue": recovered_revenue,
    }


# ============================================================
# Recovery analysis
# ============================================================

def analyze_recovery(
    ml: pd.DataFrame,
) -> None:

    print_header("RECOVERY")

    eligible = ml[
        ml["recovery_eligible"] == 1
    ]

    recovered = ml[
        ml["recovered"] == 1
    ]

    eligible_count = len(eligible)
    recovered_count = len(recovered)

    eligible_revenue = eligible["amount"].sum()
    recovered_revenue = recovered["amount"].sum()

    if eligible_count > 0:

        case_recovery_rate = (
            recovered_count
            / eligible_count
            * 100
        )

    else:

        case_recovery_rate = 0.0

    if eligible_revenue > 0:

        revenue_recovery_rate = (
            recovered_revenue
            / eligible_revenue
            * 100
        )

    else:

        revenue_recovery_rate = 0.0

    print(
        f"Eligible cases:        "
        f"{eligible_count:,}"
    )

    print(
        f"Recovered cases:       "
        f"{recovered_count:,}"
    )

    print(
        f"Case recovery rate:    "
        f"{case_recovery_rate:.2f}%"
    )

    print(
        f"Revenue recovery rate: "
        f"{revenue_recovery_rate:.2f}%"
    )


# ============================================================
# Recovery by failure reason
# ============================================================

def analyze_recovery_by_reason(
    raw: pd.DataFrame,
    ml: pd.DataFrame,
) -> None:

    print_header("RECOVERY BY FAILURE REASON")

    grouped = (
        ml.groupby("failure_reason")
        .agg(
            cases=("payment_id", "count"),
            eligible=("recovery_eligible", "sum"),
            recovered=("recovered", "sum"),
            revenue=("amount", "sum"),
        )
        .reset_index()
    )

    # The raw dataset contains future outcome fields.
    # Therefore recovered revenue is calculated from RAW data.

    raw_failed = raw[
        raw["payment_status"] == "failed"
    ].copy()

    recovered_by_reason = (
        raw_failed[
            raw_failed["recovered"] == 1
        ]
        .groupby("failure_reason")[
            "recovered_amount"
        ]
        .sum()
    )

    grouped["recovered_revenue"] = (
        grouped["failure_reason"]
        .map(recovered_by_reason)
        .fillna(0.0)
    )

    grouped["recovery_rate"] = (
        grouped["recovered"]
        / grouped["eligible"].replace(0, pd.NA)
        * 100
    )

    for _, row in grouped.iterrows():

        if pd.isna(row["recovery_rate"]):
            rate = "N/A"
        else:
            rate = (
                f"{row['recovery_rate']:.2f}%"
            )

        print()
        print(row["failure_reason"])

        print(
            f"  Cases:             "
            f"{int(row['cases']):,}"
        )

        print(
            f"  Eligible:          "
            f"{int(row['eligible']):,}"
        )

        print(
            f"  Recovered:         "
            f"{int(row['recovered']):,}"
        )

        print(
            f"  Recovery rate:     "
            f"{rate}"
        )

        print(
            f"  Revenue:           "
            f"{money(row['revenue'])}"
        )

        print(
            f"  Recovered revenue: "
            f"{money(row['recovered_revenue'])}"
        )


# ============================================================
# Customer behavior
# ============================================================

def analyze_customer_behavior(
    ml: pd.DataFrame,
) -> None:

    print_header("CUSTOMER BEHAVIOR")

    print(
        "Average successful payments: "
        f"{ml['successful_payment_count'].mean():.2f}"
    )

    print(
        "Average failed payments:     "
        f"{ml['failed_payment_count'].mean():.2f}"
    )

    print(
        "Average lifetime value:      "
        f"{money(ml['lifetime_value'].mean())}"
    )

    print(
        "Average payment amount:      "
        f"{money(ml['amount'].mean())}"
    )


# ============================================================
# Ground truth probability
# ============================================================

def analyze_ground_truth_probability(
    raw: pd.DataFrame,
) -> None:

    print_header(
        "GROUND-TRUTH RECOVERY PROBABILITY"
    )

    failed = raw[
        raw["payment_status"] == "failed"
    ]

    probability = (
        failed[
            "recovery_probability_ground_truth"
        ]
    )

    print(
        f"Minimum: "
        f"{probability.min():.4f}"
    )

    print(
        f"Maximum: "
        f"{probability.max():.4f}"
    )

    print(
        f"Mean:    "
        f"{probability.mean():.4f}"
    )


# ============================================================
# Data quality checks
# ============================================================

def run_data_quality_checks(
    raw: pd.DataFrame,
    ml: pd.DataFrame,
) -> bool:

    print_header("DATA QUALITY CHECKS")

    checks = []

    # --------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------

    checks.append(
        (
            "Duplicate payment IDs",
            raw["payment_id"].duplicated().sum() == 0,
            raw["payment_id"].duplicated().sum(),
        )
    )

    checks.append(
        (
            "Duplicate ML payment IDs",
            ml["payment_id"].duplicated().sum() == 0,
            ml["payment_id"].duplicated().sum(),
        )
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    checks.append(
        (
            "Missing payment IDs",
            raw["payment_id"].isna().sum() == 0,
            raw["payment_id"].isna().sum(),
        )
    )

    checks.append(
        (
            "Missing customer IDs",
            raw["customer_id"].isna().sum() == 0,
            raw["customer_id"].isna().sum(),
        )
    )

    checks.append(
        (
            "Missing amounts",
            raw["amount"].isna().sum() == 0,
            raw["amount"].isna().sum(),
        )
    )

    # --------------------------------------------------------
    # Amount checks
    # --------------------------------------------------------

    negative_amounts = (
        raw["amount"] < 0
    ).sum()

    checks.append(
        (
            "Negative amounts",
            negative_amounts == 0,
            negative_amounts,
        )
    )

    zero_amounts = (
        raw["amount"] <= 0
    ).sum()

    checks.append(
        (
            "Zero/negative amounts",
            zero_amounts == 0,
            zero_amounts,
        )
    )

    # --------------------------------------------------------
    # Label checks
    # --------------------------------------------------------

    invalid_recovery = (
        ~ml["recovered"].isin([0, 1])
    ).sum()

    checks.append(
        (
            "Invalid recovery labels",
            invalid_recovery == 0,
            invalid_recovery,
        )
    )

    invalid_eligibility = (
        ~ml["recovery_eligible"].isin([0, 1])
    ).sum()

    checks.append(
        (
            "Invalid eligibility labels",
            invalid_eligibility == 0,
            invalid_eligibility,
        )
    )

    # --------------------------------------------------------
    # Payment status
    # --------------------------------------------------------

    invalid_status = (
        ~raw["payment_status"]
        .isin(VALID_PAYMENT_STATUSES)
    ).sum()

    checks.append(
        (
            "Invalid payment statuses",
            invalid_status == 0,
            invalid_status,
        )
    )

    # --------------------------------------------------------
    # Payment methods
    # --------------------------------------------------------

    invalid_methods = (
        ~raw["payment_method"]
        .isin(VALID_PAYMENT_METHODS)
    ).sum()

    checks.append(
        (
            "Invalid payment methods",
            invalid_methods == 0,
            invalid_methods,
        )
    )

    # --------------------------------------------------------
    # Subscription status
    # --------------------------------------------------------

    invalid_subscription_status = (
        ~raw["subscription_status"]
        .isin(VALID_SUBSCRIPTION_STATUSES)
    ).sum()

    checks.append(
        (
            "Invalid subscription statuses",
            invalid_subscription_status == 0,
            invalid_subscription_status,
        )
    )

    # --------------------------------------------------------
    # Failure reasons
    # --------------------------------------------------------

    failed_rows = raw[
        raw["payment_status"] == "failed"
    ]

    invalid_failure_reasons = (
        ~failed_rows["failure_reason"]
        .isin(VALID_FAILURE_REASONS)
    ).sum()

    checks.append(
        (
            "Invalid failure reasons",
            invalid_failure_reasons == 0,
            invalid_failure_reasons,
        )
    )

    # --------------------------------------------------------
    # Success payment failure reason
    # --------------------------------------------------------

    success_rows = raw[
        raw["payment_status"] == "success"
    ]

    success_with_failure_reason = (
        success_rows["failure_reason"]
        .notna()
        .sum()
    )

    checks.append(
        (
            "Successful payments with failure reason",
            success_with_failure_reason == 0,
            success_with_failure_reason,
        )
    )

    # --------------------------------------------------------
    # Recovery amount
    # --------------------------------------------------------

    invalid_recovered_amount = (
        (
            (raw["recovered"] == 1)
            & (
                raw["recovered_amount"]
                <= 0
            )
        )
    ).sum()

    checks.append(
        (
            "Recovered cases with zero amount",
            invalid_recovered_amount == 0,
            invalid_recovered_amount,
        )
    )

    # --------------------------------------------------------
    # Recovery consistency
    # --------------------------------------------------------

    recovered_without_eligibility = (
        (
            (raw["recovered"] == 1)
            & (raw["recovery_eligible"] == 0)
        )
    ).sum()

    checks.append(
        (
            "Recovered cases marked ineligible",
            recovered_without_eligibility == 0,
            recovered_without_eligibility,
        )
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    all_passed = True

    for name, passed, value in checks:

        if passed:
            print_pass(
                f"{name:<45} {value}"
            )

        else:
            print_fail(
                f"{name:<45} {value}"
            )

            all_passed = False

    return all_passed


# ============================================================
# Leakage check
# ============================================================

def run_leakage_check(
    ml: pd.DataFrame,
) -> bool:

    print_header("DATA LEAKAGE CHECK")

    leakage_columns = (
        FORBIDDEN_ML_COLUMNS
        .intersection(ml.columns)
    )

    if leakage_columns:

        print_fail(
            "Future information detected:"
        )

        for column in sorted(leakage_columns):
            print(f"  - {column}")

        return False

    print_pass(
        "No forbidden future-outcome columns found."
    )

    print(
        "The ML dataset contains only "
        "decision-time information plus the target."
    )

    return True


# ============================================================
# Target distribution
# ============================================================

def analyze_target_distribution(
    ml: pd.DataFrame,
) -> None:

    print_header("ML TARGET DISTRIBUTION")

    counts = (
        ml["recovered"]
        .value_counts()
        .sort_index()
    )

    total = len(ml)

    for label, count in counts.items():

        percentage = (
            count / total * 100
        )

        label_name = (
            "Not recovered"
            if label == 0
            else "Recovered"
        )

        print(
            f"{label_name:<20}"
            f"{count:>8,}"
            f" ({percentage:>6.2f}%)"
        )


# ============================================================
# Eligibility distribution
# ============================================================

def analyze_eligibility_distribution(
    ml: pd.DataFrame,
) -> None:

    print_header("RECOVERY ELIGIBILITY")

    eligible_count = (
        ml["recovery_eligible"]
        .sum()
    )

    ineligible_count = (
        len(ml) - eligible_count
    )

    eligible_percentage = (
        eligible_count
        / len(ml)
        * 100
    )

    print(
        f"Eligible:     "
        f"{eligible_count:,}"
        f" ({eligible_percentage:.2f}%)"
    )

    print(
        f"Ineligible:   "
        f"{ineligible_count:,}"
        f" ({100 - eligible_percentage:.2f}%)"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print()
    print("=" * 70)
    print("REVIVEAI DATASET QUALITY AUDIT")
    print("=" * 70)

    # --------------------------------------------------------
    # File validation
    # --------------------------------------------------------

    if not validate_files():

        print()
        print("=" * 70)
        print("DATASET AUDIT: FAILED")
        print("=" * 70)

        return

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    try:

        raw = pd.read_csv(RAW_FILE)
        ml = pd.read_csv(ML_FILE)

    except Exception as error:

        print()
        print("ERROR: Could not read dataset files.")
        print(f"Reason: {error}")

        print()
        print("=" * 70)
        print("DATASET AUDIT: FAILED")
        print("=" * 70)

        return

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    show_dataset_size(
        raw,
        ml,
    )

    # --------------------------------------------------------
    # Schema
    # --------------------------------------------------------

    schema_passed = validate_schema(
        raw,
        ml,
    )

    if not schema_passed:

        print()
        print("=" * 70)
        print("DATASET AUDIT: FAILED")
        print("=" * 70)

        return

    # --------------------------------------------------------
    # Analysis
    # --------------------------------------------------------

    analyze_payment_status(raw)

    analyze_failure_reasons(ml)

    analyze_revenue(
        raw,
        ml,
    )

    analyze_recovery(ml)

    analyze_recovery_by_reason(
        raw,
        ml,
    )

    analyze_customer_behavior(ml)

    analyze_ground_truth_probability(raw)

    analyze_target_distribution(ml)

    analyze_eligibility_distribution(ml)

    # --------------------------------------------------------
    # Quality checks
    # --------------------------------------------------------

    quality_passed = run_data_quality_checks(
        raw,
        ml,
    )

    # --------------------------------------------------------
    # Leakage check
    # --------------------------------------------------------

    leakage_passed = run_leakage_check(
        ml,
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()
    print("=" * 70)

    if quality_passed and leakage_passed:

        print("DATASET AUDIT: PASSED")

    else:

        print("DATASET AUDIT: FAILED")

    print("=" * 70)


if __name__ == "__main__":
    main()