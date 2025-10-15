"""
Pagination and cursor tests
Ensures no overlap, stable ordering, clean last-page handling
"""
import os
import pytest
import httpx

BASE = os.getenv("BRIDGE_BASE", "http://127.0.0.1:8014")
TOKEN = os.getenv("BRIDGE_TOKEN")

def _headers():
    """Generate auth headers"""
    return {"x-bridge-token": TOKEN} if TOKEN else {}

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pagination_no_overlap():
    """Paginated traces have no overlap between pages"""
    async with httpx.AsyncClient() as c:
        # Get first page
        r1 = await c.get(f"{BASE}/traces?limit=10", headers=_headers(), timeout=5)
        r1.raise_for_status()
        data1 = r1.json()

        # Handle both list and dict formats
        if isinstance(data1, dict):
            traces1 = data1.get("traces", [])
        else:
            traces1 = data1

        if len(traces1) < 10:
            pytest.skip("Not enough traces for pagination test")

        # Get second page (if cursor supported)
        cursor = r1.headers.get("x-next-cursor")
        if cursor:
            r2 = await c.get(f"{BASE}/traces?limit=10&cursor={cursor}", headers=_headers(), timeout=5)
            r2.raise_for_status()
            data2 = r2.json()
            traces2 = data2.get("traces", data2) if isinstance(data2, dict) else data2

            # Check no overlap
            ids1 = {t.get("id", t.get("trace_id")) for t in traces1}
            ids2 = {t.get("id", t.get("trace_id")) for t in traces2}
            overlap = ids1 & ids2
            assert len(overlap) == 0, f"Found {len(overlap)} overlapping traces"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_traces_ordered_newest_first():
    """Traces are ordered by timestamp descending (newest first)"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/traces?limit=20", headers=_headers(), timeout=5)
        r.raise_for_status()
        data = r.json()

        traces = data.get("traces", data) if isinstance(data, dict) else data

        if len(traces) < 2:
            pytest.skip("Not enough traces for ordering test")

        # Check timestamps are non-increasing
        timestamps = [t.get("started_at", t.get("timestamp", 0)) for t in traces]

        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i+1], \
                f"Traces not ordered: trace[{i}]={timestamps[i]} < trace[{i+1}]={timestamps[i+1]}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_limit_parameter_respected():
    """Limit parameter controls number of results"""
    async with httpx.AsyncClient() as c:
        for limit in [5, 10, 20]:
            r = await c.get(f"{BASE}/traces?limit={limit}", headers=_headers(), timeout=5)
            r.raise_for_status()
            data = r.json()

            traces = data.get("traces", data) if isinstance(data, dict) else data

            # Should return at most 'limit' traces
            assert len(traces) <= limit, f"Got {len(traces)} traces, expected max {limit}"

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_last_page_clean():
    """Last page returns empty or proper end-of-list indicator"""
    async with httpx.AsyncClient() as c:
        # Get with very high offset to simulate last page
        r = await c.get(f"{BASE}/traces?limit=10&offset=9999", headers=_headers(), timeout=5)
        r.raise_for_status()
        data = r.json()

        traces = data.get("traces", data) if isinstance(data, dict) else data

        # Should return empty list or small list
        assert isinstance(traces, list), "Last page should return list"
        assert len(traces) == 0 or isinstance(data, dict) and "has_more" in data, \
            "Last page should be empty or indicate has_more=false"
