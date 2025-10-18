#!/usr/bin/env python3
"""
Graph-of-Code (GoC) Service
Builds symbol dependency graphs for impact analysis and test coverage queries.

Supports: Swift, Rust, Go, Python
Endpoints:
  - POST /ingest - Ingest code files
  - GET /impact?symbol=X - Find what breaks if symbol X changes
  - GET /tests?file=Y - Find which tests cover file Y
  - GET /graph - Export full dependency graph
  - GET /health - Service health
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

class IngestRequest(BaseModel):
    """Request to ingest code files."""
    files: List[str]
    language: str
    project_root: Optional[str] = None


class ImpactResponse(BaseModel):
    """Response for impact analysis query."""
    symbol: str
    direct_dependents: List[str]
    transitive_dependents: List[str]
    affected_files: List[str]
    affected_tests: List[str]
    impact_score: float
    timestamp: str


class TestCoverageResponse(BaseModel):
    """Response for test coverage query."""
    file: str
    direct_tests: List[str]
    indirect_tests: List[str]
    coverage_score: float
    timestamp: str


class GraphNode(BaseModel):
    """Node in the dependency graph."""
    symbol: str
    kind: str  # function, class, method, variable, etc.
    file: str
    line: int
    language: str


class GraphEdge(BaseModel):
    """Edge in the dependency graph."""
    source: str
    target: str
    edge_type: str  # calls, imports, inherits, implements, etc.
    weight: float


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

class GraphDatabase:
    """SQLite database for storing the code graph."""
    
    def __init__(self, db_path: str = "services/goc/state/graph.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS symbols (
                symbol TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                file TEXT NOT NULL,
                line INTEGER NOT NULL,
                language TEXT NOT NULL,
                signature TEXT,
                docstring TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source) REFERENCES symbols(symbol),
                FOREIGN KEY (target) REFERENCES symbols(symbol),
                UNIQUE(source, target, edge_type)
            );
            
            CREATE TABLE IF NOT EXISTS tests (
                test_name TEXT PRIMARY KEY,
                file TEXT NOT NULL,
                line INTEGER NOT NULL,
                language TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS test_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                coverage_type TEXT NOT NULL,  -- direct, indirect
                FOREIGN KEY (test_name) REFERENCES tests(test_name),
                FOREIGN KEY (symbol) REFERENCES symbols(symbol),
                UNIQUE(test_name, symbol, coverage_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_dependencies_source ON dependencies(source);
            CREATE INDEX IF NOT EXISTS idx_dependencies_target ON dependencies(target);
            CREATE INDEX IF NOT EXISTS idx_test_coverage_symbol ON test_coverage(symbol);
            CREATE INDEX IF NOT EXISTS idx_test_coverage_test ON test_coverage(test_name);
        """)
        
        self.conn.commit()
        logger.info(f"✅ Graph database initialized: {self.db_path}")
    
    def add_symbol(self, symbol: str, kind: str, file: str, line: int, 
                   language: str, signature: str = "", docstring: str = ""):
        """Add or update a symbol in the graph."""
        self.conn.execute("""
            INSERT INTO symbols (symbol, kind, file, line, language, signature, docstring)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                kind=excluded.kind,
                file=excluded.file,
                line=excluded.line,
                language=excluded.language,
                signature=excluded.signature,
                docstring=excluded.docstring,
                updated_at=CURRENT_TIMESTAMP
        """, (symbol, kind, file, line, language, signature, docstring))
        self.conn.commit()
    
    def add_dependency(self, source: str, target: str, edge_type: str, weight: float = 1.0):
        """Add a dependency edge to the graph."""
        try:
            self.conn.execute("""
                INSERT INTO dependencies (source, target, edge_type, weight)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source, target, edge_type) DO UPDATE SET
                    weight=excluded.weight
            """, (source, target, edge_type, weight))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Dependency references non-existent symbol, skip
            logger.warning(f"Skipped dependency {source} -> {target}: symbol not found")
    
    def get_direct_dependents(self, symbol: str) -> List[str]:
        """Get symbols that directly depend on the given symbol."""
        cursor = self.conn.execute("""
            SELECT DISTINCT source FROM dependencies WHERE target = ?
        """, (symbol,))
        return [row[0] for row in cursor.fetchall()]
    
    def get_transitive_dependents(self, symbol: str, max_depth: int = 10) -> Set[str]:
        """Get all symbols that transitively depend on the given symbol."""
        visited = set()
        queue = [symbol]
        depth = 0
        
        while queue and depth < max_depth:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            dependents = self.get_direct_dependents(current)
            queue.extend([d for d in dependents if d not in visited])
            depth += 1
        
        visited.discard(symbol)  # Remove the original symbol
        return visited
    
    def get_affected_files(self, symbols: Set[str]) -> List[str]:
        """Get files that contain the given symbols."""
        if not symbols:
            return []
        
        placeholders = ','.join('?' * len(symbols))
        cursor = self.conn.execute(f"""
            SELECT DISTINCT file FROM symbols WHERE symbol IN ({placeholders})
        """, tuple(symbols))
        return [row[0] for row in cursor.fetchall()]
    
    def get_tests_for_symbols(self, symbols: Set[str]) -> List[str]:
        """Get tests that cover the given symbols."""
        if not symbols:
            return []
        
        placeholders = ','.join('?' * len(symbols))
        cursor = self.conn.execute(f"""
            SELECT DISTINCT test_name FROM test_coverage
            WHERE symbol IN ({placeholders})
        """, tuple(symbols))
        return [row[0] for row in cursor.fetchall()]
    
    def get_symbol_count(self) -> int:
        """Get total number of symbols in the graph."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM symbols")
        return cursor.fetchone()[0]
    
    def get_dependency_count(self) -> int:
        """Get total number of dependencies in the graph."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM dependencies")
        return cursor.fetchone()[0]


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

SYMBOLS_TOTAL = Gauge('goc_symbols_total', 'Total symbols in graph')
DEPENDENCIES_TOTAL = Gauge('goc_dependencies_total', 'Total dependencies in graph')
INGEST_DURATION = Histogram('goc_ingest_duration_seconds', 'Ingest operation latency')
IMPACT_QUERIES = Counter('goc_impact_queries_total', 'Impact queries served')
TEST_QUERIES = Counter('goc_test_queries_total', 'Test coverage queries served')

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Graph-of-Code Service",
    description="Symbol dependency graph for impact analysis",
    version="1.0.0"
)

# Global graph database
graph_db: GraphDatabase

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    global graph_db
    
    logger.info("=" * 60)
    logger.info("🚀 Graph-of-Code Service Starting")
    logger.info("=" * 60)
    
    # Initialize database
    graph_db = GraphDatabase()
    
    # Update metrics
    SYMBOLS_TOTAL.set(graph_db.get_symbol_count())
    DEPENDENCIES_TOTAL.set(graph_db.get_dependency_count())
    
    logger.info(f"✅ Service initialized")
    logger.info(f"   Symbols: {graph_db.get_symbol_count()}")
    logger.info(f"   Dependencies: {graph_db.get_dependency_count()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    if graph_db and graph_db.conn:
        graph_db.conn.close()
    logger.info("🛑 Graph-of-Code Service stopped")


@app.get("/")
async def root():
    """Service info."""
    return {
        "service": "Graph-of-Code (GoC)",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "symbol_graph",
            "impact_analysis",
            "test_coverage",
            "multi_language"
        ],
        "supported_languages": ["swift", "rust", "go", "python"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "goc",
        "symbols": graph_db.get_symbol_count(),
        "dependencies": graph_db.get_dependency_count(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/impact")
async def impact_analysis(
    symbol: str = Query(..., description="Symbol to analyze"),
    max_depth: int = Query(10, description="Maximum traversal depth")
) -> ImpactResponse:
    """
    Analyze the impact of changing a symbol.
    Returns all dependents and affected files/tests.
    """
    IMPACT_QUERIES.inc()
    
    # Get direct dependents
    direct = set(graph_db.get_direct_dependents(symbol))
    
    # Get transitive dependents
    transitive = graph_db.get_transitive_dependents(symbol, max_depth)
    transitive.difference_update(direct)  # Remove direct from transitive
    
    # Get affected files
    all_affected = direct.union(transitive)
    all_affected.add(symbol)
    affected_files = graph_db.get_affected_files(all_affected)
    
    # Get affected tests
    affected_tests = graph_db.get_tests_for_symbols(all_affected)
    
    # Calculate impact score (0-1, based on # of dependents)
    impact_score = min(1.0, len(all_affected) / 100.0)
    
    return ImpactResponse(
        symbol=symbol,
        direct_dependents=sorted(list(direct)),
        transitive_dependents=sorted(list(transitive)),
        affected_files=sorted(affected_files),
        affected_tests=sorted(affected_tests),
        impact_score=impact_score,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/tests")
async def test_coverage(
    file: str = Query(..., description="File to check coverage for")
) -> TestCoverageResponse:
    """
    Find which tests cover a given file.
    Returns direct and indirect test coverage.
    """
    TEST_QUERIES.inc()
    
    # Get symbols in the file
    cursor = graph_db.conn.execute("""
        SELECT symbol FROM symbols WHERE file = ?
    """, (file,))
    symbols = {row[0] for row in cursor.fetchall()}
    
    # Get tests that directly cover these symbols
    direct_tests = set(graph_db.get_tests_for_symbols(symbols))
    
    # Get tests that indirectly cover (via dependencies)
    indirect_tests = set()
    for symbol in symbols:
        deps = graph_db.get_transitive_dependents(symbol, max_depth=5)
        tests = set(graph_db.get_tests_for_symbols(deps))
        indirect_tests.update(tests)
    
    indirect_tests.difference_update(direct_tests)
    
    # Calculate coverage score
    total_symbols = len(symbols)
    covered_symbols = len([s for s in symbols if graph_db.get_tests_for_symbols({s})])
    coverage_score = covered_symbols / total_symbols if total_symbols > 0 else 0.0
    
    return TestCoverageResponse(
        file=file,
        direct_tests=sorted(list(direct_tests)),
        indirect_tests=sorted(list(indirect_tests)),
        coverage_score=coverage_score,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Update gauges
    SYMBOLS_TOTAL.set(graph_db.get_symbol_count())
    DEPENDENCIES_TOTAL.set(graph_db.get_dependency_count())
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ingest")
@INGEST_DURATION.time()
async def ingest_code(request: IngestRequest):
    """
    Ingest code files and build the symbol graph.
    Delegates to language-specific ingestors.
    """
    logger.info(f"📥 Ingesting {len(request.files)} {request.language} files")
    
    # Import ingestor based on language
    ingestor = None
    if request.language == "swift":
        from ingestors.swift_ingestor import SwiftIngestor
        ingestor = SwiftIngestor(graph_db)
    elif request.language == "python":
        from ingestors.python_ingestor import PythonIngestor
        ingestor = PythonIngestor(graph_db)
    elif request.language == "rust":
        from ingestors.rust_ingestor import RustIngestor
        ingestor = RustIngestor(graph_db)
    elif request.language == "go":
        from ingestors.go_ingestor import GoIngestor
        ingestor = GoIngestor(graph_db)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
    
    # Ingest files
    try:
        stats = ingestor.ingest_files(request.files, project_root=request.project_root)
        
        # Update metrics
        SYMBOLS_TOTAL.set(graph_db.get_symbol_count())
        DEPENDENCIES_TOTAL.set(graph_db.get_dependency_count())
        
        logger.info(f"✅ Ingested {stats['symbols_added']} symbols, {stats['dependencies_added']} dependencies")
        
        return {
            "status": "success",
            "language": request.language,
            "files_processed": len(request.files),
            "symbols_added": stats['symbols_added'],
            "dependencies_added": stats['dependencies_added'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("GOC_PORT", "8200"))
    host = os.getenv("GOC_HOST", "127.0.0.1")
    
    logger.info(f"Starting Graph-of-Code service on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

