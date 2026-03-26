"""
Print a readable RAGAS report from `data/eval/results/ragas_results.json`.

Usage:
  python scripts/print_ragas_report.py
  python scripts/print_ragas_report.py --file data/eval/results/ragas_results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print summary and per-sample RAGAS metrics")
    parser.add_argument(
        "--file",
        default="data/eval/results/ragas_results.json",
        help="Path to ragas results JSON",
    )
    parser.add_argument(
        "--show-rows",
        action="store_true",
        help="Print per-row metrics in addition to summary",
    )
    return parser.parse_args()


def fmt(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return str(value)


def print_summary(summary: Dict[str, Any]) -> None:
    if not summary:
        print("No summary metrics found.")
        return

    print("=== RAGAS Summary ===")
    for key in sorted(summary.keys()):
        print(f"- {key}: {fmt(summary[key])}")


def row_metric_keys(row: Dict[str, Any]) -> List[str]:
    preferred = [
        "faithfulness",
        "answer_relevancy",
        "answer_relevance",
        "context_precision",
        "context_recall",
    ]
    return [key for key in preferred if key in row]


def print_rows(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("No per-row metrics found.")
        return

    print("\n=== Per-Sample Metrics ===")
    for index, row in enumerate(rows, start=1):
        print(f"\nRow {index}")

        if row.get("question"):
            print(f"  question: {row['question']}")

        keys = row_metric_keys(row)
        if not keys:
            print("  (No known metric keys in this row)")
            continue

        for key in keys:
            print(f"  {key}: {fmt(row[key])}")


def main() -> None:
    args = parse_args()
    result_path = Path(args.file)

    if not result_path.exists():
        print(f"File not found: {result_path}")
        print("Run evaluator first:")
        print("python scripts/evaluate_ragas.py --dataset data/eval/ragas_eval_dataset.json --api-base http://127.0.0.1:8000")
        raise SystemExit(1)

    with result_path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    summary = payload.get("summary", {})
    rows = payload.get("rows", [])

    print_summary(summary)
    if args.show_rows:
        print_rows(rows)


if __name__ == "__main__":
    main()
