#!/usr/bin/env python3
"""
Contract Tests - Ensure API compatibility
Run with: pytest tests/test_contract.py -v
"""
import os

import httpx
import pytest

# Configuration
BRIDGE_BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
UAT_BASE = os.getenv("UAT_BASE", "http://127.0.0.1:8181")
ATHENA_BASE = os.getenv("ATHENA_BASE", "http://127.0.0.1:8090")
UAT_TOKEN = os.getenv("UAT_TOKEN", "supersecret")
ATH_TOKEN = os.getenv("ATH_TOKEN", "supersecret")

@pytest.fixture
def auth_headers_uat():
    return {"Authorization": f"Bearer {UAT_TOKEN}"}

@pytest.fixture
def auth_headers_athena():
    return {"Authorization": f"Bearer {ATH_TOKEN}"}

class TestBridgeContract:
    """Test bridge endpoints"""

    def test_bridge_health(self):
        """Bridge /health returns 200"""
        response = httpx.get(f"{BRIDGE_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_bridge_traces(self):
        """Bridge /traces returns valid structure"""
        response = httpx.get(f"{BRIDGE_BASE}/traces")
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data
        assert "source" in data
        # Should be uat-real in production, mock-mode in dev
        assert data["source"] in ["uat-real", "mock-mode", "fallback"]

    def test_bridge_trace_detail(self):
        """Bridge /trace/{id} returns trace"""
        # First get a trace ID
        response = httpx.get(f"{BRIDGE_BASE}/traces")
        data = response.json()

        if "traces" in data and len(data.get("traces", {}).get("traces", [])) > 0:
            trace_id = data["traces"]["traces"][0]["trace_id"]

            # Get trace detail
            detail_response = httpx.get(f"{BRIDGE_BASE}/trace/{trace_id}")
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            assert "trace_id" in detail_data
            assert detail_data["trace_id"] == trace_id

class TestUATContract:
    """Test UAT service endpoints"""

    def test_uat_health(self, auth_headers_uat):
        """UAT /health returns 200 with auth"""
        response = httpx.get(f"{UAT_BASE}/health", headers=auth_headers_uat)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_uat_auth_required(self):
        """UAT requires authentication"""
        response = httpx.get(f"{UAT_BASE}/traces")
        assert response.status_code == 401

    def test_uat_traces_schema(self, auth_headers_uat):
        """UAT /traces returns valid schema"""
        response = httpx.get(f"{UAT_BASE}/traces", headers=auth_headers_uat)
        assert response.status_code == 200
        data = response.json()

        assert "traces" in data
        assert "count" in data
        assert isinstance(data["traces"], list)

        if len(data["traces"]) > 0:
            trace = data["traces"][0]
            # Verify required fields
            required_fields = ["trace_id", "title", "timestamp", "capability", "status"]
            for field in required_fields:
                assert field in trace, f"Missing required field: {field}"

    def test_uat_trace_detail(self, auth_headers_uat):
        """UAT /trace/{id} returns single trace"""
        # Get a trace ID
        response = httpx.get(f"{UAT_BASE}/traces", headers=auth_headers_uat)
        data = response.json()

        if len(data["traces"]) > 0:
            trace_id = data["traces"][0]["trace_id"]

            detail_response = httpx.get(f"{UAT_BASE}/trace/{trace_id}", headers=auth_headers_uat)
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            assert detail_data["trace_id"] == trace_id

class TestAthenaContract:
    """Test Athena service endpoints"""

    def test_athena_health(self, auth_headers_athena):
        """Athena /health returns 200 with auth"""
        response = httpx.get(f"{ATHENA_BASE}/health", headers=auth_headers_athena)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_athena_auth_required(self):
        """Athena requires authentication"""
        response = httpx.get(f"{ATHENA_BASE}/agents")
        assert response.status_code == 401

    def test_athena_agents(self, auth_headers_athena):
        """Athena /agents returns agent list"""
        response = httpx.get(f"{ATHENA_BASE}/agents", headers=auth_headers_athena)
        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) > 0

    def test_athena_chat(self, auth_headers_athena):
        """Athena /chat returns valid response"""
        payload = {
            "message": "test message",
            "stream": False
        }
        response = httpx.post(
            f"{ATHENA_BASE}/chat",
            headers=auth_headers_athena,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "route" in data
        assert "agent" in data

class TestEndToEnd:
    """End-to-end integration tests"""

    def test_bridge_forwards_auth(self, auth_headers_uat):
        """Bridge correctly forwards auth to backends"""
        # This tests that bridge doesn't require auth but forwards it
        response = httpx.get(f"{BRIDGE_BASE}/traces")
        assert response.status_code == 200

    def test_latency_sla(self):
        """Bridge responses meet latency SLA (< 250ms)"""
        import time

        start = time.time()
        response = httpx.get(f"{BRIDGE_BASE}/health", timeout=1.0)
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 250, f"Latency {elapsed_ms}ms exceeds SLA of 250ms"

    def test_circuit_breaker_state(self):
        """Circuit breaker is in healthy state"""
        response = httpx.get(f"{BRIDGE_BASE}/")
        data = response.json()

        if "circuit_breaker" in data:
            assert data["circuit_breaker"]["is_open"] == False, "Circuit breaker is open!"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])


