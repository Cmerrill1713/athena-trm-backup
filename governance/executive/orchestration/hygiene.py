"""
Memory Hygiene Utilities
========================
Deduplication and pinning for vector store
"""

from typing import Callable
from .vector_store import _STORE


def dedupe(ns: str):
    """
    Remove duplicate texts from namespace

    Args:
        ns: Namespace name
    """
    if ns not in _STORE:
        return

    seen = set()
    out = []

    for text, ts in _STORE[ns]:
        if text in seen:
            continue
        seen.add(text)
        out.append((text, ts))

    _STORE[ns] = out


def pin(ns: str, predicate: Callable[[str], bool]):
    """
    Pin items matching predicate to the end (survive pruning)

    Args:
        ns: Namespace name
        predicate: Function that returns True for items to pin
    """
    if ns not in _STORE:
        return

    pins = []
    rest = []

    for text, ts in _STORE[ns]:
        if predicate(text):
            pins.append((text, ts))
        else:
            rest.append((text, ts))

    # Pinned items go to the end (most recent position)
    _STORE[ns] = rest + pins
