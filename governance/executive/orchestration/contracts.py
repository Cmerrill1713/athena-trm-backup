"""
Capability IO Contract - Agent-Agnostic Interface
=================================================
Enforces strict typing for capability inputs and outputs
"""

from typing import TypedDict, List, Dict, Any, Optional


class CapabilityInput(TypedDict, total=False):
    """Standard input contract for any capability"""
    capability: str            # e.g., "summarize", "plan", "generate"
    record: Dict[str, Any]     # CRM-like dict (id, subject, body, etc.)
    context: List[str]         # retrieved snippets
    params: Dict[str, Any]     # temp, max_tokens, tool hints, etc.
    meta: Dict[str, Any]       # trace_id, user_id, policy_version, prompt_hash


class CapabilityOutput(TypedDict, total=False):
    """Standard output contract for any capability"""
    tldr: str
    facts: List[str]
    next_action: str
    actions: List[Dict[str, Any]]       # [{type, value}]
    metrics: Dict[str, Any]             # {"latency_ms":..., "tokens":..., "model_id":...}
    safety: Dict[str, Any]              # {"pii": False, "policy_hits": []}
    raw: Optional[str]                  # provider raw output for audit
