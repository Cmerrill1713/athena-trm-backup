"""
Thompson Sampling Bandit + Promotion Guard
==========================================
Multi-armed bandit for capability provider selection
"""

from collections import defaultdict
from random import random
from typing import Dict, List, Any


# State keyed by (capability, provider_name)
# Format: {"wins": int, "losses": int, "samples": int, "promotable": bool}
_state = defaultdict(lambda: {"wins": 1, "losses": 1, "samples": 0, "promotable": False})


def choose_arm(capability: str, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select provider using Thompson sampling (exploration + exploitation)

    Args:
        capability: Capability name
        providers: List of ProviderSpec dicts

    Returns:
        Selected provider
    """
    if not providers:
        raise ValueError(f"No providers available for capability: {capability}")

    if len(providers) == 1:
        return providers[0]

    best_provider = None
    best_score = -1

    for provider in providers:
        state = _state[(capability, provider["name"])]

        # Thompson sampling: sample from beta distribution (approximated)
        # estimate = wins / (wins + losses)
        estimate = state["wins"] / (state["wins"] + state["losses"])

        # Add exploration bonus (random draw)
        draw = estimate + 0.05 * random()

        if draw > best_score:
            best_provider = provider
            best_score = draw

    return best_provider


def reward(capability: str, provider_name: str, composite_score: float, promote_min_samples: int = 5):
    """
    Update provider statistics based on performance

    Args:
        capability: Capability name
        provider_name: Provider name
        composite_score: Score (0.0-1.0)
        promote_min_samples: Minimum samples before promotion eligible
    """
    state = _state[(capability, provider_name)]
    state["samples"] += 1

    # Threshold: 0.7+ is a "win"
    if composite_score >= 0.7:
        state["wins"] += 1
    else:
        state["losses"] += 1

    # Promotion eligibility: only after enough samples
    state["promotable"] = state["samples"] >= promote_min_samples


def get_stats(capability: str = None) -> Dict[str, Any]:
    """
    Get bandit statistics

    Args:
        capability: Optional capability filter

    Returns:
        Statistics dict
    """
    if capability:
        # Filter by capability
        stats = {}
        for (cap, provider), state in _state.items():
            if cap == capability:
                stats[provider] = {
                    "wins": state["wins"],
                    "losses": state["losses"],
                    "samples": state["samples"],
                    "win_rate": state["wins"] / (state["wins"] + state["losses"]),
                    "promotable": state["promotable"]
                }
        return stats
    else:
        # All stats
        stats = {}
        for (cap, provider), state in _state.items():
            key = f"{cap}::{provider}"
            stats[key] = {
                "wins": state["wins"],
                "losses": state["losses"],
                "samples": state["samples"],
                "win_rate": state["wins"] / (state["wins"] + state["losses"]),
                "promotable": state["promotable"]
            }
        return stats


def reset_stats():
    """Reset all bandit statistics (for testing)"""
    _state.clear()
