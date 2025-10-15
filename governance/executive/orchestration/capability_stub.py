"""
Example Capability Provider
===========================
Stub implementation - replace with your actual providers
"""

from typing import Dict, Any


def run(capability_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example provider that respects the capability contract

    Args:
        capability_input: CapabilityInput dict

    Returns:
        CapabilityOutput dict
    """
    cap = capability_input.get("capability", "unknown")
    rec = capability_input.get("record", {})
    ctx = capability_input.get("context", [])
    params = capability_input.get("params", {})

    # This stub just echoes structured output
    # Replace with your actual provider runtime (LLM call, agent invocation, etc.)

    tldr = f"{cap.upper()} :: {rec.get('subject', '(no subject)')}"
    facts = [f"context#{i+1}: {c[:64]}" for i, c in enumerate(ctx[:3])]
    next_action = "review" if cap != "plan" else "execute_plan"
    actions = [{"type": "append_note", "value": f"Ran {cap} with params={params}"}]

    return {
        "tldr": tldr,
        "facts": facts,
        "next_action": next_action,
        "actions": actions,
        "metrics": {"latency_ms": 120, "model_id": "provider_stub"},
        "safety": {"pii": False, "policy_hits": []},
        "raw": ""
    }
