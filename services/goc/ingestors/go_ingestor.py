#!/usr/bin/env python3
"""
Go Code Ingestor for Graph-of-Code
Uses gopls references and call hierarchy.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class GoIngestor:
    """Ingests Go files to build symbol graph."""
    
    def __init__(self, graph_db):
        self.graph_db = graph_db
    
    def ingest_files(self, files: List[str], project_root: str = None) -> Dict[str, int]:
        """Ingest multiple Go files."""
        logger.info(f"TODO: Implement Go ingestion for {len(files)} files")
        logger.info("  Approach: Use gopls references and call hierarchy")
        logger.info("  See: https://pkg.go.dev/golang.org/x/tools/gopls")
        
        return {
            "symbols_added": 0,
            "dependencies_added": 0
        }

