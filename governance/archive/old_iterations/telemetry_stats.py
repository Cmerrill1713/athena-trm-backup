#!/usr/bin/env python3
"""
Telemetry Statistics Extractor
===============================
Analyzes telemetry database for performance metrics
"""

import os
import sqlite3
import json
import time


DB = os.environ.get("TELEMETRY_DB", "./orchestrator/state/telemetry.sqlite")
OUTPUT = "./state/telemetry_stats.json"


def fetch(query, args=()):
    """Execute query and return results"""
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute(query, args)]


def percentile(values, p):
    """Calculate percentile"""
    if not values:
        return None
    v2 = sorted(values)
    i = max(0, int(round((len(v2) - 1) * p)))
    return v2[i]


def main():
    os.makedirs("./state", exist_ok=True)

    if not os.path.exists(DB):
        print(f"⚠️  No telemetry DB at {DB}, writing placeholder")
        with open(OUTPUT, "w") as f:
            json.dump({"warning": "no telemetry db"}, f, indent=2)
        return

    # Fetch last 1000 traces
    rows = fetch("""
        SELECT capability, duration_ms, started_at, raw_json
        FROM traces
        ORDER BY started_at DESC
        LIMIT 1000
    """)

    # Extract durations
    durations = [r["duration_ms"] for r in rows if r.get("duration_ms") is not None]

    # By capability
    by_cap = {}
    for r in rows:
        cap = r["capability"]
        dur = r.get("duration_ms")
        if dur is not None:
            by_cap.setdefault(cap, []).append(dur)

    # Calculate stats
    stats = {
        "generated_at": int(time.time()),
        "count": len(rows),
        "p50": percentile(durations, 0.50),
        "p95": percentile(durations, 0.95),
        "p99": percentile(durations, 0.99),
        "by_capability": {}
    }

    for cap, durs in by_cap.items():
        clean_durs = [d for d in durs if d is not None]
        stats["by_capability"][cap] = {
            "count": len(durs),
            "p50": percentile(clean_durs, 0.50),
            "p95": percentile(clean_durs, 0.95)
        }

    # Write output
    with open(OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"✅ Telemetry stats written to {OUTPUT}")
    print(f"   Traces analyzed: {len(rows)}")
    print(f"   p50: {stats['p50']}ms, p95: {stats['p95']}ms, p99: {stats['p99']}ms")


if __name__ == "__main__":
    main()
