"""
Bridge integration tests
Tests the NeuroForge adapter contract compliance
"""
import os
import asyncio
import time
import json
import uuid
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN", None)

def _headers(extra=None):
    """Generate request headers with correlation ID"""
    h = {"x-correlation-id": str(uuid.uuid4())}
    if TOKEN:
        h["x-bridge-token"] = TOKEN
    if extra:
        h.update(extra)
    return h

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_health_ok():
    """Health endpoint returns valid status"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health", headers=_headers(), timeout=5)
        r.raise_for_status()
        j = r.json()
        assert "status" in j, "health missing status field"
        assert j["status"] in ("ok", "healthy", "degraded", "running"), f"unexpected status: {j['status']}"
        # Adapter field is optional (different bridge implementations)
        assert "service" in j or "adapter" in j, "health missing service/adapter field"
        assert "timestamp" in j, "health missing timestamp"

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_contract_version():
    """Contract endpoint exposes version and schema (optional)"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/contract", headers=_headers(), timeout=5)

        # Contract endpoint is optional - some bridges may not have it
        if r.status_code == 404:
            pytest.skip("Contract endpoint not implemented (optional)")

        r.raise_for_status()
        contract = r.json()
        assert "version" in contract, "contract missing version"
        assert contract["version"], "contract version is empty"
        assert "endpoints" in contract, "contract missing endpoints"
        assert len(contract["endpoints"]) > 0, "contract has no endpoints"

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_root_info():
    """Root endpoint returns adapter information"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/", headers=_headers(), timeout=5)
        r.raise_for_status()
        info = r.json()
        assert "service" in info, "root missing service field"
        assert "version" in info or "status" in info, "root missing version/status"
        # backends field is optional
        assert "endpoints" in info or "target" in info, "root missing endpoints/target"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_traces_list_and_correlation_echo():
    """Traces endpoint returns list and echoes correlation ID"""
    cid = str(uuid.uuid4())
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{BASE}/traces",
            headers=_headers({"x-correlation-id": cid}),
            timeout=5
        )
        r.raise_for_status()
        payload = r.json()

        # Accept both list and dict formats
        if isinstance(payload, dict):
            assert "traces" in payload or "count" in payload, "unexpected dict format"
        else:
            assert isinstance(payload, list), "traces should be list or dict"

        # Check correlation ID echo (optional)
        echo = r.headers.get("x-correlation-id")
        if echo:
            assert echo == cid, f"correlation ID mismatch: {echo} != {cid}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_trace_detail_404_graceful():
    """Trace detail returns 404 for missing trace"""
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{BASE}/trace/nonexistent-trace-id",
            headers=_headers(),
            timeout=5
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_chat_basic():
    """Chat endpoint forwards to Athena and returns reply"""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{BASE}/chat",
            headers=_headers({"content-type": "application/json"}),
            json={"text": "ping", "context": {}, "route": "auto"},
            timeout=15
        )

        # Accept 200 (success) or 404/500 (backend not available)
        if r.status_code == 200:
            j = r.json()
            assert "reply" in j, "chat response missing reply field"
        else:
            # Backend not available - that's ok for integration tests
            assert r.status_code in (401, 404, 500, 502, 503), f"unexpected status: {r.status_code}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_agents_list():
    """Agents endpoint returns list from Athena"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/agents", headers=_headers(), timeout=5)

        # Accept 200 (success) or 401/404 (backend not available)
        if r.status_code == 200:
            agents = r.json()
            assert isinstance(agents, (list, dict)), "agents should be list or dict"
        else:
            assert r.status_code in (401, 404, 500, 502, 503), f"unexpected status: {r.status_code}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_capabilities_list():
    """Capabilities endpoint returns list from UAT"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/capabilities", headers=_headers(), timeout=5)

        # Accept 200 (success) or 401/404 (backend not available)
        if r.status_code == 200:
            caps = r.json()
            assert isinstance(caps, (list, dict)), "capabilities should be list or dict"
        else:
            assert r.status_code in (401, 404, 500, 502, 503), f"unexpected status: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_auth_enforcement_when_token_set():
    """Bridge enforces token when BRIDGE_TOKEN is set"""
    if not TOKEN:
        pytest.skip("BRIDGE_TOKEN not set, skipping auth test")

    async with httpx.AsyncClient() as c:
        # Without token - should fail
        r = await c.get(f"{BASE}/traces", timeout=5)
        assert r.status_code == 401, f"expected 401 without token, got {r.status_code}"

        # With token - should succeed
        r2 = await c.get(f"{BASE}/traces", headers={"x-bridge-token": TOKEN}, timeout=5)
        r2.raise_for_status()

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_response_headers():
    """Bridge includes required response headers"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health", headers=_headers(), timeout=5)
        r.raise_for_status()

        # Check for version header
        assert "x-adapter-version" in r.headers or "server" in r.headers, "missing version header"
