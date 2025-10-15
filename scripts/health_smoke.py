#!/usr/bin/env python3
"""
Health smoke test for NeuroForge bridge
Catches regressions in interop contract
"""
import sys
import httpx
import time

BASE = "http://127.0.0.1:8014"

def get(path):
    """Make GET request with timeout"""
    return httpx.get(BASE + path, timeout=3)

def main():
    """Run smoke tests"""
    try:
        # Test health endpoint
        r = get("/health")
        r.raise_for_status()
        health = r.json()
        assert "uat" in health and "athena" in health, "Missing health fields"
        print(f"✅ Health: {health['status']}")

        # Test traces endpoint
        t = get("/traces")
        t.raise_for_status()
        traces = t.json()
        assert isinstance(traces, (list, dict)), "Invalid traces response"
        print(f"✅ Traces: {len(traces.get('traces', traces)) if isinstance(traces, dict) else len(traces)} items")

        # Test root endpoint
        root = get("/")
        root.raise_for_status()
        info = root.json()
        assert "service" in info, "Missing service info"
        print(f"✅ Root: {info['service']}")

        print(f"\n🎉 All smoke tests passed at {int(time.time())}")
        return 0
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
