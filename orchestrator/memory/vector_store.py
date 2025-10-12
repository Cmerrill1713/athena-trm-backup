"""
Toy Local Vector Store
======================
Simple in-memory search with TTL and max items
Upgrade to proper embeddings later
"""

import time
from typing import List, Tuple


# Storage: namespace -> [(text, timestamp)]
_STORE: dict[str, List[Tuple[str, int]]] = {}

# TTL configuration: namespace -> ttl_seconds
_TTL: dict[str, int] = {}

# Max items: namespace -> max_count
_MAX: dict[str, int] = {}


def configure_namespace(ns: str, ttl_secs: int = 0, max_items: int = 0):
    """
    Configure namespace with TTL and/or max items

    Args:
        ns: Namespace name
        ttl_secs: Time-to-live in seconds (0 = no TTL)
        max_items: Maximum items to keep (0 = unlimited)
    """
    if ttl_secs:
        _TTL[ns] = ttl_secs
    if max_items:
        _MAX[ns] = max_items


def upsert(ns: str, texts: List[str]):
    """
    Insert texts into namespace

    Args:
        ns: Namespace name
        texts: List of text strings to store
    """
    arr = _STORE.setdefault(ns, [])
    now = int(time.time())

    for text in texts:
        arr.append((text, now))

    _prune(ns)


def search(ns: str, query: str, k: int = 5) -> List[str]:
    """
    Search for texts matching query

    Args:
        ns: Namespace name
        query: Query string
        k: Number of results to return

    Returns:
        List of matching texts
    """
    _prune(ns)
    items = _STORE.get(ns, [])

    if not items:
        return []

    # Ultra-simplistic scoring: keyword count
    # TODO: Replace with real embeddings (sentence-transformers)
    query_lower = query.lower()
    scored = [(text.lower().count(query_lower), text) for (text, _) in items]
    scored.sort(reverse=True, key=lambda x: x[0])

    # Return best matches, or fallback to recent items if no matches
    matches = [text for _, text in scored[:k] if _ > 0]
    if matches:
        return matches
    else:
        # No keyword matches, return most recent
        return [text for (text, _) in items[-k:]]


def _prune(ns: str):
    """Prune namespace based on TTL and max items"""
    if ns not in _STORE:
        return

    items = _STORE[ns]

    # TTL pruning
    ttl = _TTL.get(ns, 0)
    if ttl:
        now = int(time.time())
        items = [(text, ts) for (text, ts) in items if now - ts <= ttl]

    # Max items cap
    cap = _MAX.get(ns, 0)
    if cap and len(items) > cap:
        items = items[-cap:]  # Keep most recent

    _STORE[ns] = items


def get_namespace_stats(ns: str) -> dict:
    """Get statistics for a namespace"""
    _prune(ns)
    items = _STORE.get(ns, [])

    if not items:
        return {"count": 0}

    now = int(time.time())
    ages = [now - ts for (_, ts) in items]

    return {
        "count": len(items),
        "oldest_age_secs": max(ages) if ages else 0,
        "newest_age_secs": min(ages) if ages else 0,
        "avg_age_secs": sum(ages) // len(ages) if ages else 0,
    }


def clear_namespace(ns: str):
    """Clear all items in namespace"""
    if ns in _STORE:
        _STORE[ns] = []
