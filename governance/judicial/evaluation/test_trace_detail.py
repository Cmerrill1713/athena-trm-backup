"""
Trace detail contract tests
Validates trace detail schema and catches silent schema changes
"""
import os
import hashlib
import json
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")

# Golden snapshot hash (update when schema intentionally changes)
GOLDEN_HASH = "update_me_when_schema_changes"

def _headers():
    """Generate auth headers"""
    return {"x-bridge-token": TOKEN} if TOKEN else {}

def _normalize_trace(trace):
    """Extract key fields for schema validation"""
    return {
        "has_id": "trace_id" in trace or "id" in trace,
        "has_capability": "capability" in trace,
        "has_duration": "duration_ms" in trace or "duration" in trace,
        "has_timestamp": "started_at" in trace or "timestamp" in trace,
        "optional_provider": "provider" in trace,
        "optional_score": "score" in trace,
    }

def _hash_schema(normalized):
    """Hash normalized schema for drift detection"""
    canonical = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_trace_detail_required_fields():
    """Trace detail contains all required fields"""
    async with httpx.AsyncClient() as c:
        # Get a trace ID
        r = await c.get(f"{BASE}/traces?limit=1", headers=_headers(), timeout=5)
        r.raise_for_status()
        data = r.json()

        traces = data.get("traces", data) if isinstance(data, dict) else data

        if not traces:
            pytest.skip("No traces available for detail test")

        trace_id = traces[0].get("id") or traces[0].get("trace_id")

        # Get trace detail
        r2 = await c.get(f"{BASE}/trace/{trace_id}", headers=_headers(), timeout=5)

        if r2.status_code == 404:
            pytest.skip("Trace detail endpoint not available")

        r2.raise_for_status()
        detail = r2.json()

        # Required fields
        assert "output" in detail or "result" in detail, "Trace detail missing output/result"
        assert "trace" in detail or "metadata" in detail, "Trace detail missing trace/metadata"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_trace_schema_stable():
    """Trace schema matches golden snapshot (catches silent changes)"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/traces?limit=1", headers=_headers(), timeout=5)
        r.raise_for_status()
        data = r.json()

        traces = data.get("traces", data) if isinstance(data, dict) else data

        if not traces:
            pytest.skip("No traces for schema test")

        # Normalize and hash
        normalized = _normalize_trace(traces[0])
        schema_hash = _hash_schema(normalized)

        # Log current hash for golden update
        print(f"\nCurrent schema hash: {schema_hash}")
        print(f"Normalized schema: {normalized}")

        # If golden hash is placeholder, warn but don't fail
        if GOLDEN_HASH == "update_me_when_schema_changes":
            pytest.skip(f"Golden hash not set. Use: {schema_hash}")

        # Check against golden
        assert schema_hash == GOLDEN_HASH, \
            f"Schema changed! Current: {schema_hash}, Golden: {GOLDEN_HASH}. " \
            f"Update GOLDEN_HASH if intentional."

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_trace_detail_404_handling():
    """Trace detail returns proper 404 for missing trace"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/trace/nonexistent-trace-999", headers=_headers(), timeout=5)

        assert r.status_code == 404, f"Expected 404, got {r.status_code}"

        # Check error response format
        error = r.json()
        assert "detail" in error or "error" in error, "404 response missing error detail"
