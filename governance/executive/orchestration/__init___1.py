"""
Memory Module
=============
Vector store and hygiene utilities
"""

from .vector_store import configure_namespace, upsert, search
from .hygiene import dedupe, pin

__all__ = [
    "configure_namespace",
    "upsert",
    "search",
    "dedupe",
    "pin",
]
