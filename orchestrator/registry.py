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
        {"name": "statistical_planner", "entry": "providers.statistical_rollout:run", "caps": ["plan", "simulation"]},
    ],
    "generate": [
        {"name": "gen_capability_stub", "entry": "providers.capability_stub:run", "caps": ["generate"]},
    ],
    # Research-based capabilities (autonomous implementations)
    "decision_making": [
        {"name": "contextual_thompson", "entry": "providers.contextual_thompson_sampling:select_provider", "caps": ["bandit", "context_aware"]},
    ],
    "prompt_optimization": [
        {"name": "adaptive_prompts", "entry": "providers.adaptive_prompts:optimize_prompt", "caps": ["rl", "prompt_tuning"]},
    ],
    "uncertainty": [
        {"name": "mc_dropout_estimator", "entry": "providers.uncertainty_estimation:estimate_uncertainty", "caps": ["confidence", "risk"]},
    ],
    "meta_learning": [
        {"name": "maml_adapter", "entry": "providers.meta_learning:adapt_to_task", "caps": ["few_shot", "transfer"]},
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


def unregister_provider(capability: str, name: str) -> None:
    """Remove a provider from registry"""
    if capability in REGISTRY:
        REGISTRY[capability] = [p for p in REGISTRY[capability] if p["name"] != name]


def list_providers(capability: str) -> List[ProviderSpec]:
    """Get all providers for a specific capability"""
    return list(REGISTRY.get(capability, []))


def list_capabilities() -> List[str]:
    """List all registered capabilities"""
    return list(REGISTRY.keys())
