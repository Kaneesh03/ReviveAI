"""
scripts/benchmark_throughput.py

ReviveAI — Deterministic Batch Throughput Benchmark.
Measures execution duration, error count, and throughput (payments/second)
using the existing RecoveryBatchProcessor.

Run from backend directory:
    python scripts/benchmark_throughput.py
"""
from __future__ import annotations

import os
import sys
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.recovery.batch import RecoveryBatchProcessor

DEMO_BATCH_IDS = [
    "pay_002610",  # eligible -> temp failure -> recovered
    "pay_000041",  # eligible -> temp failure -> recovered
    "pay_000039",  # eligible -> network error -> recovered
    "pay_000012",  # eligible -> insufficient funds -> failed
    "pay_000016",  # blocked -> payment_method_issue
    "pay_000049",  # blocked -> repeated_failure
    "pay_000116",  # blocked -> unknown_failure
    "pay_000040",  # blocked -> halted subscription
    "pay_000062",  # blocked -> retry limit exceeded
]


def run_single_benchmark(payment_ids: list[str]) -> dict[str, float | int]:
    processor = RecoveryBatchProcessor()
    
    start_time = time.perf_counter()
    batch_result = processor.process(payment_ids)
    elapsed_time = time.perf_counter() - start_time

    total_payments = len(batch_result.items)
    error_count = sum(1 for item in batch_result.items if item.error is not None)
    successful_processing = total_payments - error_count
    throughput = total_payments / elapsed_time if elapsed_time > 0 else 0.0

    return {
        "total_payments": total_payments,
        "successful_processing": successful_processing,
        "errors": error_count,
        "elapsed_time": elapsed_time,
        "throughput": throughput,
    }


def run_multi_iteration_benchmark(payment_ids: list[str], iterations: int = 10) -> dict[str, float | int]:
    processor = RecoveryBatchProcessor()
    total_evaluations = len(payment_ids) * iterations
    total_errors = 0

    start_time = time.perf_counter()
    for _ in range(iterations):
        res = processor.process(payment_ids)
        total_errors += sum(1 for item in res.items if item.error is not None)
    total_time = time.perf_counter() - start_time

    successful_processing = total_evaluations - total_errors
    throughput = total_evaluations / total_time if total_time > 0 else 0.0
    avg_batch_time = total_time / iterations if iterations > 0 else 0.0

    return {
        "iterations": iterations,
        "total_payments": total_evaluations,
        "successful_processing": successful_processing,
        "errors": total_errors,
        "total_time": total_time,
        "avg_batch_time": avg_batch_time,
        "throughput": throughput,
    }


def main():
    # Warm-up run
    _ = run_single_benchmark(DEMO_BATCH_IDS)

    # 1. Single batch measurement
    single_res = run_single_benchmark(DEMO_BATCH_IDS)

    # 2. Multi-iteration stability measurement
    multi_res = run_multi_iteration_benchmark(DEMO_BATCH_IDS, iterations=15)

    print("========================================")
    print("REVIVEAI THROUGHPUT BENCHMARK")
    print("========================================")
    print(f"Payments Processed: {single_res['total_payments']}")
    print(f"Successful Processing: {single_res['successful_processing']}")
    print(f"Errors: {single_res['errors']}")
    print(f"Execution Time: {single_res['elapsed_time']:.4f} seconds")
    print(f"Throughput: {single_res['throughput']:.2f} payments/second")
    print("========================================")
    print("\n----------------------------------------")
    print("EXTENDED STABILITY BENCHMARK (15 Iterations)")
    print("----------------------------------------")
    print(f"Benchmark Iterations: {multi_res['iterations']}")
    print(f"Total Payment Evaluations: {multi_res['total_payments']}")
    print(f"Successful Processing: {multi_res['successful_processing']}")
    print(f"Errors: {multi_res['errors']}")
    print(f"Total Execution Time: {multi_res['total_time']:.4f} seconds")
    print(f"Average Batch Time: {multi_res['avg_batch_time']:.4f} seconds")
    print(f"Sustained Throughput: {multi_res['throughput']:.2f} payments/second")
    print("----------------------------------------")


if __name__ == "__main__":
    main()
