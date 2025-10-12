"""
Backend integration tests
Direct tests of UAT and Athena backends
"""
import os
import pytest
import httpx
import asyncio

UAT = os.getenv("UAT_BASE", "http://127.0.0.1:8181")
ATH = os.getenv("ATHENA_BASE", "http://127.0.0.1:8090")
UAT_T = os.getenv("UAT_TOKEN")
ATH_T = os.getenv("ATH_TOKEN")

def _auth_header(token):
    """Generate auth header if token provided"""
    return {"Authorization": f"Bearer {token}"} if token else {}

@pytest.mark.backends
@pytest.mark.asyncio
async def test_uat_health():
    """UAT health endpoint responds"""
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{UAT}/health", headers=_auth_header(UAT_T), timeout=5)
            r.raise_for_status()
            health = r.json()
            assert "status" in health or "ok" in health, "UAT health missing status"
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("UAT not available")

@pytest.mark.backends
@pytest.mark.asyncio
async def test_uat_traces():
    """UAT traces endpoint returns data"""
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{UAT}/traces", headers=_auth_header(UAT_T), timeout=5)
            r.raise_for_status()
            traces = r.json()
            assert isinstance(traces, (list, dict)), "UAT traces invalid format"
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("UAT not available")

@pytest.mark.backends
@pytest.mark.asyncio
async def test_athena_health():
    """Athena health endpoint responds"""
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{ATH}/health", headers=_auth_header(ATH_T), timeout=5)
            r.raise_for_status()
            health = r.json()
            assert "status" in health or "ok" in health, "Athena health missing status"
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Athena not available")

@pytest.mark.backends
@pytest.mark.asyncio
async def test_athena_chat():
    """Athena chat endpoint responds"""
    async with httpx.AsyncClient() as c:
        try:
            headers = _auth_header(ATH_T)
            headers["content-type"] = "application/json"
            r = await c.post(
                f"{ATH}/chat",
                headers=headers,
                json={"text": "ping"},
                timeout=10
            )
            r.raise_for_status()
            response = r.json()
            assert "reply" in response or "response" in response, "Athena chat missing reply"
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Athena not available")

@pytest.mark.backends
@pytest.mark.asyncio
async def test_athena_agents():
    """Athena agents endpoint returns list"""
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{ATH}/agents", headers=_auth_header(ATH_T), timeout=5)
            r.raise_for_status()
            agents = r.json()
            assert isinstance(agents, (list, dict)), "Athena agents invalid format"
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Athena not available")
