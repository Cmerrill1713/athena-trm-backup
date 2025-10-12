"""
Agent-Agnostic Provider Registry
=================================
Routes by capability, not by agent/model name
"""

from typing import Dict, List, TypedDict


class ProviderSpec(TypedDict, total=False):
    """Provider specification"""
    name: str            # free-form label; not used for routing decisions
    entry: str           # "module:function" that implements the capability
    caps: List[str]      # capabilities supported, e.g., ["summarize", "plan"]


# Provider Registry - Populate at runtime or via config
# Routes by capability, completely agent-agnostic
REGISTRY: Dict[str, List[ProviderSpec]] = {
    "summarize": [
        {"name": "summ_capability_stub", "entry": "providers.capability_stub:run", "caps": ["summarize"]},
    ],
    "plan": [
        {"name": "plan_capability_stub", "entry": "providers.capability_stub:run", "caps": ["plan"]},
    ],
    "generate": [
        {"name": "gen_capability_stub", "entry": "providers.capability_stub:run", "caps": ["generate"]},
    ],
}


def register_provider(capability: str, spec: ProviderSpec):
    """Dynamically register a provider"""
    if capability not in REGISTRY:
        REGISTRY[capability] = []
    REGISTRY[capability].append(spec)


def get_providers(capability: str) -> List[ProviderSpec]:
    """Get all providers for a capability"""
    return REGISTRY.get(capability, [])


def list_capabilities() -> List[str]:
    """List all registered capabilities"""
    return list(REGISTRY.keys())
