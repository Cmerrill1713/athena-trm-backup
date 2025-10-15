"""
Fuzz tests for security and robustness
Tests edge cases, malformed input, unicode handling
"""
import os
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")

def _headers():
    """Generate auth headers"""
    h = {"x-bridge-token": TOKEN, "content-type": "application/json"} if TOKEN else {"content-type": "application/json"}
    return h

@pytest.mark.security
@pytest.mark.asyncio
async def test_empty_chat_input():
    """Empty chat input returns 4xx not 5xx"""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{BASE}/chat",
            headers=_headers(),
            json={"text": ""},
            timeout=5
        )

        # Should return 400/422 (validation error) not 500
        if r.status_code >= 400:
            assert r.status_code < 500, f"Empty input caused 500 error: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_huge_chat_input():
    """Huge chat input is rejected gracefully"""
    async with httpx.AsyncClient() as c:
        # 10MB of text
        huge_text = "A" * (10 * 1024 * 1024)

        r = await c.post(
            f"{BASE}/chat",
            headers=_headers(),
            json={"text": huge_text},
            timeout=10
        )

        # Should reject (413 payload too large or 400 validation error)
        # Not 500 internal error
        if r.status_code >= 400:
            assert r.status_code in (400, 413, 422, 429), \
                f"Huge input caused unexpected error: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_unicode_chat_input():
    """Unicode and emoji in chat input handled correctly"""
    test_inputs = [
        "Hello 👋 世界",
        "Emoji: 🚀🎉✅❌",
        "Greek: Ελληνικά",
        "Arabic: مرحبا",
        "Math: ∑∫∂√",
        "Mixed: Hello世界🌍",
    ]

    async with httpx.AsyncClient() as c:
        for text in test_inputs:
            r = await c.post(
                f"{BASE}/chat",
                headers=_headers(),
                json={"text": text},
                timeout=10
            )

            # Should handle or reject gracefully (not 500)
            if r.status_code >= 400:
                assert r.status_code < 500, \
                    f"Unicode '{text[:20]}...' caused 500 error: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_attempts():
    """SQL injection attempts don't cause errors"""
    injection_attempts = [
        "'; DROP TABLE traces; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
    ]

    async with httpx.AsyncClient() as c:
        for attempt in injection_attempts:
            r = await c.post(
                f"{BASE}/chat",
                headers=_headers(),
                json={"text": attempt},
                timeout=10
            )

            # Should either succeed or return 4xx validation error
            # Never 500
            if r.status_code >= 400:
                assert r.status_code < 500, \
                    f"SQL injection attempt caused 500: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_xss_attempts():
    """XSS attempts are handled safely"""
    xss_attempts = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<iframe src='javascript:alert(1)'>",
    ]

    async with httpx.AsyncClient() as c:
        for attempt in xss_attempts:
            r = await c.post(
                f"{BASE}/chat",
                headers=_headers(),
                json={"text": attempt},
                timeout=10
            )

            # Should handle safely (not 500)
            if r.status_code >= 400:
                assert r.status_code < 500, \
                    f"XSS attempt caused 500: {r.status_code}"

@pytest.mark.security
@pytest.mark.asyncio
async def test_malformed_json():
    """Malformed JSON is rejected with 400 not 500"""
    async with httpx.AsyncClient() as c:
        # Send malformed JSON
        r = await c.post(
            f"{BASE}/chat",
            headers={"x-bridge-token": TOKEN, "content-type": "application/json"} if TOKEN else {"content-type": "application/json"},
            content=b'{"text": "incomplete',
            timeout=5
        )

        # Should return 400/422 (bad request), not 500
        assert r.status_code in (400, 422), \
            f"Malformed JSON caused unexpected error: {r.status_code}"
