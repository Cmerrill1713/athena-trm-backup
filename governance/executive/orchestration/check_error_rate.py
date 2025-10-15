#!/usr/bin/env python3
"""
Quick Error Rate Check
======================
Validates error budget (<1%)
"""

import sqlite3
import sys
from pathlib import Path


def check_error_rate(db_path: str = "state/telemetry.sqlite", threshold: float = 0.01):
    """
    Check error rate from telemetry database

    Args:
        db_path: Path to telemetry database
        threshold: Max acceptable error rate (default 1%)

    Returns:
        True if under threshold
    """
    if not Path(db_path).exists():
        print("⚠️  Telemetry database not found (no traces yet)")
        return True

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total traces
    cursor.execute("SELECT COUNT(*) FROM traces")
    total = cursor.fetchone()[0]

    if total == 0:
        print("ℹ️  No traces yet")
        return True

    # Error traces (timeout or error in raw_json)
    cursor.execute("""
        SELECT COUNT(*) FROM traces
        WHERE raw_json LIKE '%timeout%'
           OR raw_json LIKE '%error%'
           OR raw_json LIKE '%failed%'
    """)
    errors = cursor.fetchone()[0]

    conn.close()

    # Calculate rate
    error_rate = errors / total if total > 0 else 0

    print("📊 Error Rate Check")
    print(f"   Total traces: {total}")
    print(f"   Errors: {errors}")
    print(f"   Rate: {error_rate*100:.2f}%")
    print(f"   Threshold: {threshold*100:.2f}%")

    if error_rate <= threshold:
        print("   ✅ PASS: Error rate under budget")
        return True
    else:
        print(f"   ❌ FAIL: Error rate exceeds {threshold*100:.1f}%")
        return False


if __name__ == "__main__":
    passed = check_error_rate()
    sys.exit(0 if passed else 1)
