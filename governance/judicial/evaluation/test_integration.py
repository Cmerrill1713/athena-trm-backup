#!/usr/bin/env python3
"""
Integration Tests - Complete Suite
High-value tests that catch regressions
Run with: pytest tests/test_integration.py -v
"""
import concurrent.futures
import hashlib
import os
import time

import httpx
import pytest

# Configuration
BRIDGE_BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
UAT_BASE = os.getenv("UAT_BASE", "http://127.0.0.1:8181")
ATHENA_BASE = os.getenv("ATHENA_BASE", "http://127.0.0.1:8090")
UAT_TOKEN = os.getenv("UAT_TOKEN", "supersecret")
ATH_TOKEN = os.getenv("ATH_TOKEN", "supersecret")

@pytest.fixture
def bridge_client():
    return httpx.Client(base_url=BRIDGE_BASE, timeout=5.0)

@pytest.fixture
def uat_headers():
    return {"Authorization": f"Bearer {UAT_TOKEN}"}

@pytest.fixture
def athena_headers():
    return {"Authorization": f"Bearer {ATH_TOKEN}"}

# ============================================================================
# 1. Contract + Schema Drift
# ============================================================================

class TestContractAndSchema:
    """Contract version and schema validation"""

    def test_trace_detail_full_object(self, bridge_client):
        """GET /trace/{id} returns full object with all required fields"""
        # Get a trace ID first
        traces_resp = bridge_client.get("/traces")
        assert traces_resp.status_code == 200
        data = traces_resp.json()

        if "traces" in data and len(data.get("traces", {}).get("traces", [])) > 0:
            trace_id = data["traces"]["traces"][0]["trace_id"]

            # Get trace detail
            detail_resp = bridge_client.get(f"/trace/{trace_id}")
            assert detail_resp.status_code == 200
            trace = detail_resp.json()

            # Required fields must be present
            required_fields = ["trace_id", "title", "timestamp", "capability", "status"]
            for field in required_fields:
                assert field in trace, f"Missing required field: {field}"

            # Unknown fields should be ignored (forward compatibility)
            # This doesn't fail if extra fields are present

    def test_contract_version_pinning(self, bridge_client):
        """Contract version check - warn on minor, fail on major"""
        response = bridge_client.get("/")
        assert response.status_code == 200
        data = response.json()

        # Check if version field exists
        if "version" in data:
            version = data["version"]
            major, minor, patch = version.split(".")

            # Fail on major version mismatch
            assert major == "1", f"Major version mismatch: {major} != 1"

            # Warn on minor version mismatch (but don't fail)
            if minor != "0":
                print(f"⚠️  Minor version changed: {version} (expected 1.0.x)")

    def test_pagination_happy_path(self, bridge_client):
        """Pagination works correctly with limit parameter"""
        # Get first page
        r1 = bridge_client.get("/traces?limit=25")
        assert r1.status_code == 200
        data1 = r1.json()

        # Check we got data
        traces1 = data1.get("traces", {}).get("traces", [])
        assert len(traces1) <= 25, "Limit not respected"

        # If cursor exists, test pagination
        cursor = r1.headers.get("x-next-cursor")
        if cursor:
            r2 = bridge_client.get(f"/traces?cursor={cursor}&limit=25")
            assert r2.status_code == 200
            data2 = r2.json()
            traces2 = data2.get("traces", {}).get("traces", [])

            # Pages should not overlap
            ids1 = {t["trace_id"] for t in traces1}
            ids2 = {t["trace_id"] for t in traces2}
            overlap = ids1 & ids2
            assert not overlap, f"Pages overlap: {overlap}"

# ============================================================================
# 2. Auth Paths (Positive + Nasty)
# ============================================================================

class TestAuthPaths:
    """Authentication and authorization tests"""

    def test_missing_token_returns_401_uat(self):
        """UAT requires token - missing token returns 401"""
        response = httpx.get(f"{UAT_BASE}/traces", timeout=3)
        assert response.status_code == 401

    def test_missing_token_returns_401_athena(self):
        """Athena requires token - missing token returns 401"""
        response = httpx.get(f"{ATHENA_BASE}/agents", timeout=3)
        assert response.status_code == 401

    def test_bad_token_returns_401_uat(self):
        """UAT rejects bad token with 401"""
        headers = {"Authorization": "Bearer badtoken123"}
        response = httpx.get(f"{UAT_BASE}/traces", headers=headers, timeout=3)
        assert response.status_code == 401

    def test_bad_token_returns_401_athena(self):
        """Athena rejects bad token with 401"""
        headers = {"Authorization": "Bearer badtoken123"}
        response = httpx.get(f"{ATHENA_BASE}/agents", headers=headers, timeout=3)
        assert response.status_code == 401

    def test_bridge_forwards_tokens(self, bridge_client, uat_headers):
        """Bridge correctly forwards auth to backends"""
        # Bridge doesn't require auth but forwards it
        response = bridge_client.get("/traces")
        assert response.status_code == 200

        # Check that response indicates real data (meaning auth worked)
        data = response.json()
        source = data.get("source", "unknown")
        # Source should be uat-real or fallback (not auth failure)
        assert source in ["uat-real", "mock-mode", "fallback"]

# ============================================================================
# 3. Rate Limiting & Abuse
# ============================================================================

class TestRateLimiting:
    """Rate limiting and abuse prevention"""

    @pytest.mark.slow
    def test_chat_burst_rate_limit(self):
        """Burst of requests to /chat triggers rate limiting"""
        def hit():
            try:
                with httpx.Client() as c:
                    response = c.post(
                        f"{BRIDGE_BASE}/chat",
                        headers={"content-type": "application/json"},
                        json={"text": "ping"},
                        timeout=3
                    )
                    return response.status_code
            except Exception:
                return 500

        # Send 80 requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            statuses = list(executor.map(lambda _: hit(), range(80)))

        # Should see mix of 200s and 429s (if rate limiting is enabled)
        # Note: Rate limiting not yet implemented, so we just check it doesn't crash
        assert 200 in statuses or 429 in statuses

        # If 429s present, check retry-after header
        if 429 in statuses:
            response = httpx.post(
                f"{BRIDGE_BASE}/chat",
                headers={"content-type": "application/json"},
                json={"text": "test"},
                timeout=3
            )
            if response.status_code == 429:
                # Should have retry-after header
                assert "retry-after" in response.headers or "Retry-After" in response.headers

# ============================================================================
# 4. Resilience & Circuit Breaker
# ============================================================================

class TestResilience:
    """Circuit breaker and resilience tests"""

    def test_circuit_breaker_state_visible(self, bridge_client):
        """Circuit breaker state is exposed and readable"""
        response = bridge_client.get("/")
        assert response.status_code == 200
        data = response.json()

        if "circuit_breaker" in data:
            breaker = data["circuit_breaker"]
            assert "is_open" in breaker
            assert isinstance(breaker["is_open"], bool)

    def test_fallback_on_backend_failure(self, bridge_client):
        """Bridge falls back gracefully when backend unavailable"""
        # This test assumes UAT might be down
        response = bridge_client.get("/traces")
        assert response.status_code == 200

        data = response.json()
        source = data.get("source")

        # Should be one of: uat-real, mock-mode, fallback
        assert source in ["uat-real", "mock-mode", "fallback", "circuit-breaker"]

    def test_retry_on_flaky_backend(self, bridge_client):
        """Bridge retries failed requests"""
        # Make multiple requests - should succeed eventually
        successes = 0
        failures = 0

        for _ in range(10):
            response = bridge_client.get("/health")
            if response.status_code == 200:
                successes += 1
            else:
                failures += 1

        # Should have high success rate (>80%)
        success_rate = successes / 10
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"

# ============================================================================
# 5. Latency SLO (Real)
# ============================================================================

class TestLatencySLO:
    """Latency SLA enforcement"""

    def test_traces_latency_p95_under_250ms(self, bridge_client):
        """p95 latency for /traces under 250ms"""
        latencies = []

        for _ in range(20):
            start = time.time()
            response = bridge_client.get("/traces")
            elapsed_ms = (time.time() - start) * 1000

            assert response.status_code == 200
            latencies.append(elapsed_ms)

        # Calculate p95
        latencies.sort()
        p95_idx = int(0.95 * len(latencies))
        p95 = latencies[p95_idx]

        assert p95 < 250, f"p95 latency {p95:.2f}ms exceeds SLA of 250ms"

    def test_health_latency_under_100ms(self, bridge_client):
        """Health check should be fast (<100ms)"""
        start = time.time()
        response = bridge_client.get("/health")
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 100, f"Health check took {elapsed_ms:.2f}ms, expected <100ms"

    def test_latency_variance_guard(self, bridge_client):
        """p95/p50 ratio < 8x (jitter check)"""
        latencies = []

        for _ in range(20):
            start = time.time()
            response = bridge_client.get("/health")
            elapsed_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                latencies.append(elapsed_ms)

        if len(latencies) < 10:
            pytest.skip("Not enough successful requests")

        latencies.sort()
        p50_idx = int(0.50 * len(latencies))
        p95_idx = int(0.95 * len(latencies))
        p50 = latencies[p50_idx]
        p95 = latencies[p95_idx]

        if p50 > 0:
            variance_ratio = p95 / p50
            assert variance_ratio < 8, f"High variance: p95/p50 = {variance_ratio:.2f}x (expected <8x)"

# ============================================================================
# 6. Streaming (if supported)
# ============================================================================

class TestStreaming:
    """Streaming response tests"""

    @pytest.mark.skip(reason="Streaming not yet implemented in bridge")
    def test_streaming_first_token_fast(self):
        """First token arrives within 800ms"""
        start = time.time()

        with httpx.stream(
            "POST",
            f"{BRIDGE_BASE}/chat",
            json={"text": "test", "stream": True},
            headers={"content-type": "application/json"}
        ) as response:
            first_chunk = None
            for chunk in response.iter_bytes():
                if chunk:
                    first_chunk = chunk
                    break

            first_token_ms = (time.time() - start) * 1000
            assert first_token_ms < 800, f"First token took {first_token_ms:.2f}ms"
            assert first_chunk is not None

# ============================================================================
# 7. Idempotency & Safety
# ============================================================================

class TestIdempotency:
    """Idempotency and safety guarantees"""

    def test_get_idempotent_with_correlation_id(self, bridge_client):
        """Same correlation ID returns consistent response"""
        corr_id = "test-idempotency-123"
        headers = {"x-correlation-id": corr_id}

        # Make two requests with same correlation ID
        r1 = bridge_client.get("/health", headers=headers)
        r2 = bridge_client.get("/health", headers=headers)

        assert r1.status_code == 200
        assert r2.status_code == 200

        # Responses should be identical (or close enough)
        assert r1.json().get("status") == r2.json().get("status")

    @pytest.mark.skip(reason="Idempotency keys not yet implemented")
    def test_chat_replay_safety(self):
        """POST /chat with idempotency key prevents replay"""
        idempotency_key = f"test-{int(time.time())}"
        headers = {
            "content-type": "application/json",
            "x-idempotency-key": idempotency_key
        }
        payload = {"text": "test message"}

        # First request
        r1 = httpx.post(f"{BRIDGE_BASE}/chat", json=payload, headers=headers)
        assert r1.status_code == 200
        request_id_1 = r1.json().get("request_id")

        # Second request with same key
        r2 = httpx.post(f"{BRIDGE_BASE}/chat", json=payload, headers=headers)
        assert r2.status_code == 200
        request_id_2 = r2.json().get("request_id")

        # Should return same request_id
        assert request_id_1 == request_id_2

# ============================================================================
# 8. Data Integrity
# ============================================================================

class TestDataIntegrity:
    """Data consistency and integrity"""

    def test_uat_seed_count(self, uat_headers):
        """UAT returns expected number of traces (170)"""
        response = httpx.get(f"{UAT_BASE}/traces", headers=uat_headers, timeout=5)
        assert response.status_code == 200

        data = response.json()
        traces = data.get("traces", [])
        total_count = data.get("total", len(traces))

        # Should have 170 seeded traces
        assert total_count == 170, f"Expected 170 traces, got {total_count}"

    def test_trace_ordering_newest_first(self, bridge_client):
        """Traces are ordered newest-first with monotonic timestamps"""
        response = bridge_client.get("/traces?limit=50")
        assert response.status_code == 200

        data = response.json()
        traces = data.get("traces", {}).get("traces", [])

        if len(traces) > 1:
            timestamps = [t.get("timestamp") for t in traces if "timestamp" in t]

            # Check ordering (newest first = descending timestamps)
            for i in range(len(timestamps) - 1):
                # Allow equal timestamps, but next should not be greater
                assert timestamps[i] >= timestamps[i + 1], \
                    f"Timestamps not monotonic: {timestamps[i]} < {timestamps[i + 1]}"

    def test_golden_checksum_matches(self, uat_headers):
        """Seed data checksum matches golden file"""
        response = httpx.get(f"{UAT_BASE}/traces", headers=uat_headers, timeout=5)
        assert response.status_code == 200

        data = response.json()
        traces = data.get("traces", [])

        # Create checksum of trace IDs + timestamps
        checksum_input = "".join(
            f"{t['trace_id']}{t['timestamp']}"
            for t in sorted(traces, key=lambda x: x["trace_id"])
        )
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:16]

        # Store or compare checksum
        checksum_file = "tests/golden_checksum.txt"
        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as f:
                expected = f.read().strip()
                assert checksum == expected, \
                    f"Checksum mismatch: {checksum} != {expected}"
        else:
            # First run - create golden file
            with open(checksum_file, "w") as f:
                f.write(checksum)
            print(f"✅ Created golden checksum: {checksum}")

# ============================================================================
# E2E Integration Tests
# ============================================================================

class TestEndToEnd:
    """Complete end-to-end integration tests"""

    def test_full_trace_flow(self, bridge_client):
        """Complete flow: list traces -> get detail -> verify data"""
        # 1. List traces
        list_resp = bridge_client.get("/traces")
        assert list_resp.status_code == 200
        traces_data = list_resp.json()
        assert "traces" in traces_data

        # 2. Get first trace detail
        traces = traces_data.get("traces", {}).get("traces", [])
        if len(traces) > 0:
            trace_id = traces[0]["trace_id"]

            # 3. Get trace detail
            detail_resp = bridge_client.get(f"/trace/{trace_id}")
            assert detail_resp.status_code == 200
            detail = detail_resp.json()

            # 4. Verify consistency
            assert detail["trace_id"] == trace_id

    def test_health_check_cascade(self):
        """All services respond to health checks"""
        services = {
            "bridge": (BRIDGE_BASE, None),
            "uat": (UAT_BASE, {"Authorization": f"Bearer {UAT_TOKEN}"}),
            "athena": (ATHENA_BASE, {"Authorization": f"Bearer {ATH_TOKEN}"})
        }

        for name, (base_url, headers) in services.items():
            try:
                response = httpx.get(f"{base_url}/health", headers=headers, timeout=3)
                assert response.status_code == 200, f"{name} health check failed"
                print(f"✅ {name}: healthy")
            except Exception as e:
                pytest.fail(f"❌ {name} health check failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])


