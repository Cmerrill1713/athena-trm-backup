"""
Orchestrator Smoke Tests
========================
Agent-agnostic capability testing
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from router import run_capability


def test_summarize_path():
    """Test summarize capability"""
    record = {
        "id": "TCK-1",
        "subject": "Delayed shipment",
        "body": "Vendor replied with new dates",
        "sla_mins_left": 180
    }

    res = run_capability("summarize", record, {"max_tokens": 256})
    out = res["output"]

    assert out.get("tldr"), "Should have tldr"
    assert isinstance(out.get("facts"), list), "Should have facts list"
    assert out.get("next_action"), "Should have next_action"

    print(f"✅ Summarize test passed")
    print(f"   TLDR: {out['tldr']}")


def test_plan_path():
    """Test plan capability"""
    record = {
        "id": "TCK-2",
        "subject": "QA failure",
        "body": "Board fails AOI on U15",
        "sla_mins_left": 60
    }

    res = run_capability("plan", record, {})
    out = res["output"]

    assert out.get("next_action"), "Should have next_action"
    assert isinstance(out.get("actions"), list), "Should have actions list"

    print(f"✅ Plan test passed")
    print(f"   Next action: {out['next_action']}")


def test_trace_structure():
    """Test that trace is properly structured"""
    record = {"id": "TCK-3", "subject": "Test", "body": "Trace test"}
    res = run_capability("summarize", record, {})

    trace = res["trace"]

    assert "trace_id" in trace, "Should have trace_id"
    assert "capability" in trace, "Should have capability"
    assert "duration_ms" in trace, "Should have duration"
    assert "events" in trace, "Should have events"
    assert len(trace["events"]) > 0, "Should have logged events"

    print(f"✅ Trace test passed")
    print(f"   Trace ID: {trace['trace_id']}")
    print(f"   Duration: {trace['duration_ms']}ms")
    print(f"   Events: {len(trace['events'])}")


if __name__ == "__main__":
    print("\n🧪 Orchestrator Smoke Tests")
    print("=" * 50)

    try:
        test_summarize_path()
        test_plan_path()
        test_trace_structure()

        print("\n🎉 ALL SMOKE TESTS PASSED!")
        print("\n✅ Orchestrator is working correctly")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
