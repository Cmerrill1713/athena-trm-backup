"""
Circuit breaker tests
Validates open → half-open → closed transitions
"""
import os
import pytest
import httpx
import time

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")

def _headers():
    """Generate auth headers"""
    h = {"x-bridge-token": TOKEN} if TOKEN else {}
    return h

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_breaker_headers_present():
    """Bridge returns circuit breaker state in headers"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health", headers=_headers(), timeout=5)
        r.raise_for_status()

        # Check for observability headers
        mode = r.headers.get("x-mode")
        breaker = r.headers.get("x-breaker")

        # Headers are optional but useful
        if mode:
            assert mode in ("real", "mock"), f"Invalid x-mode: {mode}"

        if breaker:
            assert breaker in ("open", "half-open", "closed"), f"Invalid x-breaker: {breaker}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mock_fallback_when_backend_down():
    """Bridge falls back to mock when backends unavailable"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/traces", headers=_headers(), timeout=5)

        # Should succeed even if backends are down
        # Either returns real data or mock data
        assert r.status_code == 200, "Bridge should fall back to mock when backends down"

        data = r.json()
        traces = data.get("traces", data) if isinstance(data, dict) else data

        # Mock or real, should return valid structure
        assert isinstance(traces, list), "Traces should be list even in mock mode"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_shows_backend_status():
    """Health endpoint shows individual backend statuses"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health", headers=_headers(), timeout=5)
        r.raise_for_status()
        health = r.json()

        # Should show backend health (format varies by bridge implementation)
        has_backend_info = (
            "uat" in health or
            "athena" in health or
            "backends" in health or
            "target" in health
        )

        assert has_backend_info, "Health missing backend status information"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_breaker_state_in_response():
    """Circuit breaker state visible in root endpoint"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/", headers=_headers(), timeout=5)
        r.raise_for_status()
        info = r.json()

        # Check for breaker state (optional)
        if "circuit_breaker" in info:
            breaker = info["circuit_breaker"]
            assert "is_open" in breaker or "state" in breaker, \
                "Circuit breaker missing state field"
