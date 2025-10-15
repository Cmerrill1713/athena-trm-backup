"""
Dynamic Provider Loader
=======================
Loads provider callables from module:function strings
"""

import importlib
from typing import Callable


def load_callable(entry: str) -> Callable:
    """
    Load a callable from module:function string

    Args:
        entry: String in format "module.submodule:function"

    Returns:
        Callable function

    Example:
        fn = load_callable("providers.my_provider:run")
        result = fn(capability_input)
    """
    if ":" not in entry:
        raise ValueError(f"Invalid entry format: {entry}. Expected 'module:function'")

    mod_name, fn_name = entry.split(":", 1)

    try:
        mod = importlib.import_module(mod_name)
    except ImportError as e:
        raise ImportError(f"Cannot import module '{mod_name}': {e}")

    try:
        fn = getattr(mod, fn_name)
    except AttributeError:
        raise AttributeError(f"Module '{mod_name}' has no function '{fn_name}'")

    return fn
