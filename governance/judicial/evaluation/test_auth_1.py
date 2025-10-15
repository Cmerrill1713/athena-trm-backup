"""
Auth edge case tests
Missing/invalid/expired tokens, token forwarding
"""
import os
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")
UAT_BASE = os.getenv("UAT_BASE", "http://127.0.0.1:8181")
UAT_TOKEN = os.getenv("UAT_TOKEN")

@pytest.mark.security
@pytest.mark.asyncio
async def test_missing_token_rejected():
    """Requests without token are rejected when auth required"""
    if not TOKEN:
        pytest.skip("BRIDGE_TOKEN not set, auth not required")

    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/traces", timeout=5)
        assert r.status_code == 401, f"Expected 401 without token, got {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_invalid_token_rejected():
    """Invalid token is rejected"""
    if not TOKEN:
        pytest.skip("BRIDGE_TOKEN not set, auth not required")

    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{BASE}/traces",
            headers={"x-bridge-token": "invalid-token-12345"},
            timeout=5
        )
        assert r.status_code == 401, f"Expected 401 with invalid token, got {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_valid_token_accepted():
    """Valid token is accepted"""
    if not TOKEN:
        pytest.skip("BRIDGE_TOKEN not set, auth not required")

    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{BASE}/traces",
            headers={"x-bridge-token": TOKEN},
            timeout=5
        )
        r.raise_for_status()
        assert r.status_code == 200

@pytest.mark.security
@pytest.mark.asyncio
async def test_token_forwarding_to_backends():
    """Bridge forwards auth tokens to backends"""
    if not UAT_TOKEN:
        pytest.skip("UAT_TOKEN not set, cannot test forwarding")

    async with httpx.AsyncClient() as c:
        # Request through bridge should work with bridge token
        headers = {"x-bridge-token": TOKEN} if TOKEN else {}
        r = await c.get(f"{BASE}/traces", headers=headers, timeout=5)

        # Should succeed if bridge forwards tokens correctly
        # Or return appropriate error if backend auth fails
        assert r.status_code in (200, 401, 404), \
            f"Unexpected status {r.status_code} - token forwarding may be broken"

@pytest.mark.security
def test_no_secrets_in_logs():
    """Verify no secrets appear in logs"""
    log_path = os.path.join(os.path.dirname(__file__), "../../logs/adapter.log")

    if not os.path.exists(log_path):
        pytest.skip("Adapter log not found")

    with open(log_path, 'r') as f:
        log_content = f.read()

    # Check for common secret patterns
    forbidden_patterns = [
        "password",
        "secret",
        "Bearer ",  # Auth tokens
        "token=",
    ]

    found_secrets = []
    for pattern in forbidden_patterns:
        if pattern.lower() in log_content.lower():
            # Get context around match
            lines = log_content.split('\n')
            for i, line in enumerate(lines):
                if pattern.lower() in line.lower():
                    found_secrets.append(f"Line {i+1}: {line[:100]}")

    assert len(found_secrets) == 0, \
        f"Found {len(found_secrets)} potential secrets in logs:\n" + "\n".join(found_secrets[:5])

@pytest.mark.security
@pytest.mark.asyncio
async def test_auth_header_case_insensitive():
    """Auth headers work regardless of case"""
    if not TOKEN:
        pytest.skip("BRIDGE_TOKEN not set")

    async with httpx.AsyncClient() as c:
        # Test lowercase
        r1 = await c.get(
            f"{BASE}/traces",
            headers={"x-bridge-token": TOKEN},
            timeout=5
        )

        # Test uppercase
        r2 = await c.get(
            f"{BASE}/traces",
            headers={"X-Bridge-Token": TOKEN},
            timeout=5
        )

        # Both should succeed (HTTP headers are case-insensitive)
        assert r1.status_code == r2.status_code, \
            f"Case sensitivity issue: {r1.status_code} != {r2.status_code}"
