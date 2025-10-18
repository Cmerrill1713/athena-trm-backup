#!/usr/bin/env python3
"""
Rust Code Ingestor for Graph-of-Code  
Uses rust-analyzer symbol index.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class RustIngestor:
    """Ingests Rust files to build symbol graph."""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
    
    def ingest_files(self, files: List[str], project_root: str = None) -> Dict[str, int]:
        """Ingest multiple Rust files."""
        logger.info(f"TODO: Implement Rust ingestion for {len(files)} files")
        logger.info("  Approach: Use rust-analyzer symbol dump")
        logger.info("  See: https://rust-analyzer.github.io/")
        
        return {
            "symbols_added": 0,
            "dependencies_added": 0
        }

