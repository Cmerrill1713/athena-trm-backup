"""
Thompson Sampling Bandit + Promotion Guard
==========================================
Multi-armed bandit for capability provider selection
WITH persistence and thread safety
"""

import json
import os
import threading
from collections import defaultdict
from random import random
from typing import Dict, Any


# Persistent state path
_STATE_PATH = os.environ.get("BANDIT_STATE", "./state/bandit.json")
_lock = threading.Lock()


def _load() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Load bandit state from disk"""
    if not os.path.exists(_STATE_PATH):
        os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
        return {}
    try:
        with open(_STATE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(state: Dict) -> None:
    """Save bandit state to disk (atomic write)"""
    os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
    tmp = _STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, _STATE_PATH)


# State: state[capability][provider] = {"wins", "losses", "samples", "promotable"}
_state = defaultdict(lambda: defaultdict(lambda: {
    "wins": 1,
    "losses": 1,
    "samples": 0,
    "promotable": False
}))

# Hydrate from disk if exists
_loaded = _load()
for cap, providers in _loaded.items():
    for name, s in providers.items():
        _state[cap][name] = s


def choose_arm(capability: str, providers):
    """
    Select provider using Thompson sampling (exploration + exploitation)
    Thread-safe with lock

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
    best_score = -1.0

    with _lock:
        for provider in providers:
            state = _state[capability][provider["name"]]

            # Thompson sampling: estimate from beta distribution
            wins = state["wins"]
            losses = state["losses"]
            estimate = wins / max(1, (wins + losses))

            # Add exploration bonus
            draw = estimate + 0.05 * random()

            if draw > best_score:
                best_provider = provider
                best_score = draw

    return best_provider


def reward(capability: str, provider_name: str, composite_score: float, promote_min_samples: int = 5):
    """
    Update provider statistics based on performance
    Thread-safe and persists to disk

    Args:
        capability: Capability name
        provider_name: Provider name
        composite_score: Score (0.0-1.0)
        promote_min_samples: Minimum samples before promotion eligible
    """
    with _lock:
        state = _state[capability][provider_name]
        state["samples"] += 1

        # Threshold: 0.7+ is a "win"
        if composite_score >= 0.7:
            state["wins"] += 1
        else:
            state["losses"] += 1

        # Promotion eligibility
        state["promotable"] = state["samples"] >= promote_min_samples

        # Persist to disk
        _save(_state)


def get_stats(capability: str) -> Dict[str, Dict[str, Any]]:
    """
    Get bandit statistics for a capability
    Thread-safe

    Args:
        capability: Capability name

    Returns:
        Stats dict {provider_name: {wins, losses, samples, win_rate, promotable}}
    """
    with _lock:
        stats = {}
        for name, vals in _state[capability].items():
            stats[name] = {
                "wins": vals["wins"],
                "losses": vals["losses"],
                "samples": vals["samples"],
                "win_rate": vals["wins"] / max(1, vals["wins"] + vals["losses"]),
                "promotable": vals["promotable"]
            }
        return stats


def get_all_stats() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Get all bandit statistics across all capabilities"""
    with _lock:
        return {cap: dict(providers) for cap, providers in _state.items()}


def reset_stats():
    """Reset all bandit statistics (for testing)"""
    with _lock:
        _state.clear()
        if os.path.exists(_STATE_PATH):
            os.remove(_STATE_PATH)
