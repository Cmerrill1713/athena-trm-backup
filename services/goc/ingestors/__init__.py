"""
Graph-of-Code Ingestors
Language-specific code parsers for building symbol graphs.
"""

from .python_ingestor import PythonIngestor
from .swift_ingestor import SwiftIngestor
from .rust_ingestor import RustIngestor
from .go_ingestor import GoIngestor

__all__ = ["PythonIngestor", "SwiftIngestor", "RustIngestor", "GoIngestor"]

