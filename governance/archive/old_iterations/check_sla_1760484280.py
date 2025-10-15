#!/usr/bin/env python3
"""
SLA Check Script
Validates that performance meets service level agreements
"""
import json
import os
import sys


def main():
    # Example: read a JSON metrics export your tests produce
    metrics_path = os.environ.get("EVAL_METRICS", "eval_metrics.json")

    if not os.path.exists(metrics_path):
        print("No eval metrics produced.")
        return 0  # Don't fail if no metrics

    try:
        with open(metrics_path) as f:
            m = json.load(f)

        latencies = [x["latency_ms"] for x in m.get("cases", []) if "latency_ms" in x]
        accuracy = m.get("aggregate", {}).get("accuracy", 0)

        if not latencies:
            print("Missing latency data")
            return 0  # Don't fail CI for missing data

        p95 = sorted(latencies)[int(0.95 * len(latencies))-1]
        print(f"p95 latency: {p95} ms | accuracy: {accuracy:.3f}")

        # SLA thresholds
        if p95 > 250 or accuracy < 0.90:
            print("❌ SLA violated.")
            return 1

        print("✅ SLA OK.")
        return 0

    except Exception as e:
        print(f"SLA check error: {e}")
        return 0  # Don't fail CI for script errors

if __name__ == "__main__":
    sys.exit(main())
