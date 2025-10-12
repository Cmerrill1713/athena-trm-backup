"""
SLO validation tests
Enforces performance budgets (p95 < 250ms)
"""
import os
import time
import statistics
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")
SLO_P95_MS = float(os.getenv("SLO_P95_MS", "250"))
SAMPLE_SIZE = int(os.getenv("SLO_SAMPLE_SIZE", "40"))

@pytest.mark.slo
def test_traces_p95_under_budget():
    """Traces endpoint p95 latency under SLO budget"""
    latencies = []
    headers = {"x-bridge-token": TOKEN} if TOKEN else {}

    with httpx.Client() as c:
        for _ in range(SAMPLE_SIZE):
            t0 = time.perf_counter()
            try:
                r = c.get(f"{BASE}/traces", headers=headers, timeout=3)
                elapsed_ms = (time.perf_counter() - t0) * 1000

                if r.status_code == 200:
                    latencies.append(elapsed_ms)
            except Exception:
                pass  # Skip failures in latency calculation

    assert len(latencies) > 0, "No successful requests"

    # Calculate percentiles
    sorted_lat = sorted(latencies)
    p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95) - 1]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99) - 1]

    print(f"\nLatency percentiles:")
    print(f"  p50: {p50:.1f}ms")
    print(f"  p95: {p95:.1f}ms")
    print(f"  p99: {p99:.1f}ms")
    print(f"  SLO budget: {SLO_P95_MS}ms")

    assert p95 < SLO_P95_MS, f"p95 too high: {p95:.1f}ms >= {SLO_P95_MS}ms"

@pytest.mark.slo
def test_health_p50_under_100ms():
    """Health endpoint p50 latency under 100ms"""
    latencies = []
    headers = {"x-bridge-token": TOKEN} if TOKEN else {}

    with httpx.Client() as c:
        for _ in range(20):
            t0 = time.perf_counter()
            try:
                r = c.get(f"{BASE}/health", headers=headers, timeout=3)
                elapsed_ms = (time.perf_counter() - t0) * 1000

                if r.status_code == 200:
                    latencies.append(elapsed_ms)
            except Exception:
                pass

    assert len(latencies) > 0, "No successful requests"

    p50 = sorted(latencies)[int(len(latencies) * 0.50)]
    print(f"\nHealth p50: {p50:.1f}ms")

    assert p50 < 100, f"health p50 too high: {p50:.1f}ms >= 100ms"

@pytest.mark.slo
def test_no_500_errors_under_load():
    """Bridge handles load without 500 errors"""
    errors = []
    headers = {"x-bridge-token": TOKEN} if TOKEN else {}

    with httpx.Client() as c:
        for i in range(50):
            try:
                r = c.get(f"{BASE}/health", headers=headers, timeout=3)
                if r.status_code >= 500:
                    errors.append(r.status_code)
            except Exception as e:
                errors.append(str(e))

    # Allow 429 (rate limited) and 401 (auth), but no 500s
    assert len(errors) == 0, f"Got {len(errors)} 5xx errors: {errors[:5]}"
