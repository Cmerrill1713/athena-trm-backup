#!/usr/bin/env python3
"""
SLO check: p95 latency < 250ms, all requests succeed
Run before merge to catch performance regressions
"""
import sys
import time
import httpx

BASE = "http://127.0.0.1:8014"
TARGET_P95_MS = 250
SAMPLE_SIZE = 30

def main():
    """Run SLO checks"""
    latencies = []
    failures = 0

    print(f"Running {SAMPLE_SIZE} requests to {BASE}/traces...")

    for i in range(SAMPLE_SIZE):
        try:
            start = time.perf_counter()
            r = httpx.get(f"{BASE}/traces", timeout=2)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if r.status_code == 200:
                latencies.append(elapsed_ms)
                if i % 10 == 0:
                    print(f"  {i+1}/{SAMPLE_SIZE}: {elapsed_ms:.0f}ms")
            else:
                failures += 1
                print(f"  {i+1}/{SAMPLE_SIZE}: FAILED {r.status_code}")
        except Exception as e:
            failures += 1
            print(f"  {i+1}/{SAMPLE_SIZE}: ERROR {e}")

    if not latencies:
        print("\n❌ No successful requests!")
        return 1

    # Calculate p95
    sorted_lat = sorted(latencies)
    p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95) - 1]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99) - 1]

    print("\nResults:")
    print(f"  Success rate: {len(latencies)}/{SAMPLE_SIZE} ({len(latencies)*100//SAMPLE_SIZE}%)")
    print(f"  p50: {p50:.0f}ms")
    print(f"  p95: {p95:.0f}ms")
    print(f"  p99: {p99:.0f}ms")

    # Check SLOs
    if failures > 0:
        print(f"\n❌ SLO FAILED: {failures} failed requests")
        return 1

    if p95 > TARGET_P95_MS:
        print(f"\n❌ SLO FAILED: p95 {p95:.0f}ms > {TARGET_P95_MS}ms")
        return 1

    print(f"\n✅ SLO passed: p95={p95:.0f}ms < {TARGET_P95_MS}ms, 100% success rate")
    return 0

if __name__ == "__main__":
    sys.exit(main())
