#!/usr/bin/env python3
"""
Athena Dev Daemon (athena-devd)
Editor-agnostic coding copilot that automatically gathers context
"""
import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import git

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Athena Dev Daemon",
    description="Editor-agnostic coding copilot with auto-context",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local only, safe
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration
# ============================================================================

class Config:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        config_path = repo_root / ".athena" / "config.yml"
        
        if config_path.exists():
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            logger.warning("No .athena/config.yml found, using defaults")
            self.config = {}
        
        # Parse config
        self.http_port = self.config.get("server", {}).get("http_port", 8765)
        self.max_snippets = self.config.get("context", {}).get("max_snippets", 8)
        self.max_lines = self.config.get("context", {}).get("max_lines_per_snippet", 300)
        self.recent_days = self.config.get("context", {}).get("recent_days", 90)
        self.athena_url = self.config.get("athena", {}).get("api_url", "http://localhost:8080/v1/chat/completions")
        
        logger.info(f"Config loaded from {config_path if config_path.exists() else 'defaults'}")

# ============================================================================
# File Watcher
# ============================================================================

class CodeChangeHandler(FileSystemEventHandler):
    """Watch for code changes and trigger re-indexing"""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.last_index = datetime.now()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Only reindex if enough time has passed (debounce)
        if (datetime.now() - self.last_index).seconds < 5:
            return
        
        if any(event.src_path.endswith(ext) for ext in ['.py', '.go', '.rs', '.js', '.ts']):
            logger.info(f"Code changed: {event.src_path}")
            # TODO: Incremental reindex
            self.last_index = datetime.now()

# ============================================================================
# Context Indexer
# ============================================================================

class ContextIndexer:
    """Gathers code context using ripgrep, ctags, and semantic search"""
    
    def __init__(self, repo_root: Path, config: Config):
        self.repo_root = repo_root
        self.config = config
        self.git_repo = None
        
        try:
            self.git_repo = git.Repo(repo_root)
        except:
            logger.warning("Not a git repo or git not available")
    
    def ripgrep_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Exact text search using ripgrep"""
        try:
            result = subprocess.run(
                ["rg", "--json", "--max-count", str(max_results), query, str(self.repo_root)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            matches = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        import json
                        data = json.loads(line)
                        if data.get("type") == "match":
                            matches.append({
                                "path": data["data"]["path"]["text"],
                                "line": data["data"]["line_number"],
                                "text": data["data"]["lines"]["text"],
                                "score": 1.0,  # Exact match
                                "reason": "exact match"
                            })
                    except:
                        pass
            
            return matches[:max_results]
        except Exception as e:
            logger.error(f"Ripgrep failed: {e}")
            return []
    
    def get_file_snippet(self, filepath: str, start_line: int, end_line: int) -> str:
        """Extract code snippet from file"""
        try:
            full_path = self.repo_root / filepath
            if not full_path.exists():
                return ""
            
            with open(full_path, 'r') as f:
                lines = f.readlines()
                snippet_lines = lines[max(0, start_line-1):min(len(lines), end_line)]
                return ''.join(snippet_lines)
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return ""
    
    def get_recently_changed_files(self, days: int = 90) -> List[str]:
        """Get files changed in last N days"""
        if not self.git_repo:
            return []
        
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            commits = list(self.git_repo.iter_commits(since=since, max_count=100))
            
            changed_files = set()
            for commit in commits:
                for item in commit.stats.files:
                    changed_files.add(item)
            
            return list(changed_files)
        except Exception as e:
            logger.error(f"Git history failed: {e}")
            return []
    
    def rank_and_merge(self, candidates: List[Dict], active_file: Optional[str] = None) -> List[Dict]:
        """Rank and merge context candidates"""
        recent_files = set(self.get_recently_changed_files(self.config.recent_days))
        
        for candidate in candidates:
            score = candidate.get("score", 0.5)
            filepath = candidate.get("path", "")
            
            # Freshness boost
            if filepath in recent_files:
                score += 0.3
            
            # Locality boost (same folder as active file)
            if active_file and filepath:
                active_dir = os.path.dirname(active_file)
                candidate_dir = os.path.dirname(filepath)
                if active_dir == candidate_dir:
                    score += 0.2
                elif active_dir.split('/')[0] == candidate_dir.split('/')[0]:  # Same service
                    score += 0.1
            
            candidate["final_score"] = score
        
        # Sort by score and limit
        candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return candidates[:self.config.max_snippets]

# ============================================================================
# API Models
# ============================================================================

class AssistRequest(BaseModel):
    repoRoot: str
    file: str
    cursor: Optional[Dict[str, int]] = None
    selection: Optional[Dict[str, int]] = None
    visibleFiles: List[str] = []
    diagnostics: List[Dict[str, Any]] = []
    git: Optional[Dict[str, Any]] = None
    testOutput: Optional[str] = None
    intent: str = "explain-and-fix"
    query: Optional[str] = None

class AssistResponse(BaseModel):
    snippets: List[Dict[str, Any]]
    summary: str
    nextActions: List[Dict[str, Any]] = []
    citations: List[str] = []

# ============================================================================
# Global State
# ============================================================================

repo_root = Path(os.getenv("ATHENA_REPO_ROOT", os.getcwd()))
config = Config(repo_root)
indexer = ContextIndexer(repo_root, config)

# Start file watcher
observer = Observer()
handler = CodeChangeHandler(indexer)
observer.schedule(handler, str(repo_root), recursive=True)
observer.start()
logger.info(f"👀 Watching {repo_root} for changes")

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/healthz")
async def health():
    """Health check for adapters"""
    return {
        "status": "healthy",
        "service": "athena-devd",
        "repo": str(repo_root),
        "watchers": "active",
        "port": config.http_port
    }

@app.post("/ctx/suggest")
async def suggest_context(request: AssistRequest):
    """Return ranked code snippets (no LLM call)"""
    
    # Extract query from selection or diagnostics
    query_text = request.query or ""
    if request.diagnostics:
        query_text += " " + " ".join([d.get("msg", "") for d in request.diagnostics])
    
    # Search with ripgrep
    matches = indexer.ripgrep_search(query_text, max_results=20)
    
    # Rank and merge
    ranked = indexer.rank_and_merge(matches, request.file)
    
    # Format as snippets
    snippets = []
    for match in ranked:
        filepath = match["path"]
        line = match.get("line", 1)
        
        # Get context around the match
        snippet_text = indexer.get_file_snippet(filepath, line - 20, line + 20)
        
        snippets.append({
            "path": filepath,
            "start": max(1, line - 20),
            "end": line + 20,
            "text": snippet_text,
            "why": match.get("reason", "relevant match"),
            "score": match.get("final_score", 0.5)
        })
    
    return {
        "snippets": snippets,
        "query": query_text
    }

@app.post("/assist", response_model=AssistResponse)
async def assist(request: AssistRequest, http_request: Request):
    """Full assistance: context + LLM answer with governance, tracing, rate limiting, and REP awareness"""
    
    logger.info(f"Assist request for {request.file}, intent: {request.intent}")
    
    # Import all governance, tracing, rate limiting, REP awareness
    from governance_middleware import governance_gate, capture_editor_context, estimate_plan, emit_audit_event
    from tracing import ensure_trace, create_span
    from events_state import emit_ctx_requested, emit_ctx_served, update_user_state
    from rate_limiter import check_rate_limit, release_rate_limit
    from rep_awareness import adapt_to_clustering, apply_rep_strategy
    import time
    
    start_time = time.time()
    
    # Extract user for rate limiting
    user_id = "christian"  # TODO: Extract from auth token
    
    try:
        # 0a. Rate Limiting: Check before processing
        await check_rate_limit(user_id, "/assist")
    
    # 0. Tracing: Ensure we have a trace ID
    trace_id = ensure_trace(dict(http_request.headers))
    
    with create_span(trace_id, "dev.assist") as span:
        # 1. Governance: Check authorization before spending
        ctx = capture_editor_context(request, http_request)
        decision = estimate_plan(request)
        
        span.set_attribute("user", ctx.get("user"))
        span.set_attribute("file", ctx.get("file"))
        span.set_attribute("intent", ctx.get("intent"))
        
        try:
            gov_result = await governance_gate("dev.assist", decision, ctx)
            span.set_attribute("governance.approved", True)
            span.set_attribute("governance.decision_id", gov_result.get("decision_id"))
        except Exception as e:
            span.set_attribute("governance.approved", False)
            logger.error(f"Governance denied: {e}")
            raise
        
        # 2. Events: Emit context requested
        await emit_ctx_requested(ctx, decision, trace_id)
        
        # 3. REP Awareness: Adapt to clustering
        rep_strategy = await adapt_to_clustering()
        adjusted_config = await apply_rep_strategy(rep_strategy, config)
        
        span.set_attribute("rep.strategy", rep_strategy["strategy"])
        span.set_attribute("rep.clustering_factor", rep_strategy.get("clustering_factor", 0.0))
        
        # 4. Gather context (with REP-adjusted config)
        ctx_response = await suggest_context(request)
        snippets = ctx_response["snippets"]
        
        # Apply REP topK limit if needed
        if adjusted_config.get("max_snippets"):
            snippets = snippets[:adjusted_config["max_snippets"]]
        
        span.set_attribute("snippets.count", len(snippets))
    
    # 2. Build prompt with context
    context_text = "# Relevant Code Context:\n\n"
    citations = []
    
    for i, snippet in enumerate(snippets, 1):
        context_text += f"## Context {i}: {snippet['path']}:{snippet['start']}-{snippet['end']}\n"
        context_text += f"# Why: {snippet['why']}\n"
        context_text += f"```\n{snippet['text']}\n```\n\n"
        citations.append(f"{snippet['path']}:{snippet['start']}-{snippet['end']}")
    
    # 3. Build user query
    user_query = f"Intent: {request.intent}\n"
    if request.query:
        user_query += f"Query: {request.query}\n"
    if request.file:
        user_query += f"Current file: {request.file}\n"
    if request.selection:
        user_query += f"Selected lines: {request.selection.get('start')}-{request.selection.get('end')}\n"
    if request.diagnostics:
        user_query += f"\nErrors:\n"
        for diag in request.diagnostics:
            user_query += f"  - {diag.get('file')}:{diag.get('line')} - {diag.get('msg')}\n"
    if request.testOutput:
        user_query += f"\nTest failures:\n{request.testOutput[:500]}\n"
    
    # 4. Call Athena
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            athena_request = {
                "model": "athena-dev",
                "messages": [
                    {"role": "system", "content": context_text},
                    {"role": "user", "content": user_query}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = await client.post(config.athena_url, json=athena_request)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("latency_ms", latency_ms)
            
            # 5. Events: Emit context served
            await emit_ctx_served(trace_id, len(snippets), latency_ms)
            
            # 6. State: Update user activity in etcd
            await update_user_state(ctx.get("user", "unknown"), {
                "files": [request.file],
                "intent": request.intent,
                "latency_ms": latency_ms,
                "snippets_count": len(snippets),
                "total_requests": 1  # TODO: Track cumulative
            })
            
            # 7. Audit: Emit completion event
            await emit_audit_event("athena.dev.assist.completed", {
                "trace_id": trace_id,
                "user": ctx.get("user"),
                "latency_ms": latency_ms,
                "snippets_count": len(snippets),
                "success": True
            })
            
            return AssistResponse(
                snippets=snippets,
                summary=answer,
                citations=citations,
                nextActions=[]  # TODO: Parse answer for suggested actions
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (rate limits, governance denials)
        raise
    
    except Exception as e:
        logger.error(f"Athena call failed: {e}")
        
        # Audit failure
        await emit_audit_event("athena.dev.assist.failed", {
            "trace_id": trace_id,
            "user": ctx.get("user", "unknown"),
            "error": str(e)
        })
        
        raise HTTPException(status_code=500, detail=f"Athena unavailable: {str(e)}")
    
    finally:
        # Always release rate limit slot
        release_rate_limit(user_id)

@app.post("/index/rebuild")
async def rebuild_index():
    """Force rebuild of code index"""
    logger.info("Rebuilding code index...")
    # TODO: Implement full reindex
    return {"status": "rebuilding", "message": "Index rebuild started"}

if __name__ == "__main__":
    import uvicorn
    
    port = config.http_port
    host = config.config.get("server", {}).get("host", "127.0.0.1")
    
    logger.info("=" * 60)
    logger.info("🤖 Athena Dev Daemon Starting")
    logger.info("=" * 60)
    logger.info(f"📍 Repo: {repo_root}")
    logger.info(f"🌐 HTTP: http://{host}:{port}")
    logger.info(f"👀 Watching for code changes")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")

