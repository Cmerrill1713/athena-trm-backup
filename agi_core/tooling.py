"""
AGI Tool Gateway - Unified tool invocation with discovery, retries and timeouts
"""
import os
import time
import httpx
import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Metrics
TOOL_CALLS = Counter("agi_tool_calls_total", "Tool invocations", ["tool", "outcome"])
CURIOSITY_ACTIONS = Counter("agi_curiosity_actions_total", "Curiosity actions", ["kind"])
MISSING_PARAMS = Counter("agi_missing_param_total", "Missing parameters", ["tool", "field"])
UNCERTAINTY_SCORE = Gauge("agi_uncertainty_score", "Current uncertainty level")
RAG_QUERIES = Counter("agi_rag_queries_total", "RAG queries executed", ["outcome"])
GRAPH_QUERIES = Counter("agi_graph_queries_total", "Graph queries executed", ["outcome"])
CONTEXT_INJECTIONS = Counter("agi_rag_context_injections_total", "RAG context injected into prompts")
SECOND_PASS = Counter("agi_second_pass_total", "Low-confidence re-planning", ["reason"])
from prometheus_client import Summary
PLAN_CONFIDENCE = Summary("agi_plan_confidence", "Planning confidence score")

@dataclass
class ToolSpec:
    """Tool specification with discovery endpoints"""
    name: str
    url: str
    schema_url: Optional[str] = None
    ping_url: Optional[str] = None
    category: str = "general"


# Map logical tool names → concrete HTTP endpoints (will be populated by discovery)
TOOL_REGISTRY: Dict[str, str] = {
    "mcp.web_search": os.getenv("TOOL_MCP_WEB_SEARCH", "http://localhost:8412/tool/web_search"),
    "mcp.fs.read": os.getenv("TOOL_MCP_FS_READ", "http://localhost:8412/tool/file_read"),
    "mcp.fs.write": os.getenv("TOOL_MCP_FS_WRITE", "http://localhost:8412/tool/file_write"),
    "mcp.fs.patch": os.getenv("TOOL_MCP_FS_PATCH", "http://localhost:8412/tool/file_apply_patch"),
    "mcp.shell": os.getenv("TOOL_MCP_SHELL", "http://localhost:8412/tool/shell"),
    
    "frontend.xcode_build": os.getenv("TOOL_FE_XCODE", "http://localhost:8413/tool/xcode_build"),
    "frontend.app_launch": os.getenv("TOOL_FE_LAUNCH", "http://localhost:8413/tool/app_launch"),
    "frontend.ui_typing_probe": os.getenv("TOOL_FE_PROBE", "http://localhost:8413/tool/ui_typing_probe"),
    "frontend.swift_frontend_reflex": os.getenv("TOOL_FE_REFLEX", "http://localhost:8413/tool/swift_frontend_reflex"),
    
    "git.commit_push_pr": os.getenv("TOOL_GIT_PR", "http://localhost:8412/tool/git_commit_push_pr"),
    "uai.chat": os.getenv("TOOL_UAI_CHAT", "http://localhost:8080/v1/chat/completions"),
    
    # System meta-tools (internal)
    "system.doctor": "internal://doctor",
    "system.tools_refresh": "internal://tools_refresh",
    
    # RAG & Graph tools (external services)
    "rag.query": os.getenv("RAG_URL", "http://localhost:8093") + "/search",
    "rag.dense_search": os.getenv("RAG_URL", "http://localhost:8093") + "/search",
    "graph.search": os.getenv("GRAPH_URL", "http://localhost:8200") + "/search",
    
    # TRM Reasoning tools (recursive reasoning microservice)
    "trm.classify": os.getenv("TRM_URL", "http://localhost:8420") + "/v1/trm/classify",
    "trm.deliberate": os.getenv("TRM_URL", "http://localhost:8420") + "/v1/trm/deliberate",
    "trm.critique": os.getenv("TRM_URL", "http://localhost:8420") + "/v1/trm/critique",
}

# Detailed tool specs with discovery metadata
TOOL_SPECS: Dict[str, ToolSpec] = {}


class ToolError(RuntimeError):
    """Tool invocation failed"""
    pass


class ToolTimeout(ToolError):
    """Tool timed out"""
    pass


async def discover_tools(candidates: list[ToolSpec]) -> Dict[str, Any]:
    """
    Discover and validate tools at runtime.
    Returns status dict with health + schema for each tool.
    """
    CURIOSITY_ACTIONS.labels(kind="discover_tools").inc()
    logger.info(f"Discovering {len(candidates)} tool candidates...")
    
    status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for tool in candidates:
            tool_status = {"name": tool.name, "url": tool.url}
            
            try:
                # Ping health if available
                if tool.ping_url:
                    resp = await client.get(tool.ping_url)
                    tool_status["healthy"] = (resp.status_code // 100) == 2
                
                # Fetch schema if available
                if tool.schema_url:
                    schema_resp = await client.get(tool.schema_url)
                    if schema_resp.status_code == 200:
                        tool_status["schema"] = schema_resp.json()
                        tool_status["healthy"] = True
                
                # Register if healthy
                if tool_status.get("healthy"):
                    TOOL_REGISTRY[tool.name] = tool.url
                    TOOL_SPECS[tool.name] = tool
                    logger.info(f"✅ Discovered tool: {tool.name}")
                
            except Exception as e:
                tool_status["healthy"] = False
                tool_status["error"] = str(e)
                logger.warning(f"⚠️  Tool {tool.name} unavailable: {e}")
            
            status[tool.name] = tool_status
    
    logger.info(f"Discovery complete: {len([s for s in status.values() if s.get('healthy')])} / {len(candidates)} tools available")
    return status


async def doctor_snapshot() -> Dict[str, Any]:
    """
    Introspect system state: services, tools, config, recent failures.
    This is the meta-tool Athena calls when uncertain.
    """
    CURIOSITY_ACTIONS.labels(kind="doctor").inc()
    logger.info("Running system doctor...")
    
    snapshot = {
        "timestamp": time.time(),
        "env": {
            "MCP_URL": os.getenv("MCP_URL", "http://localhost:8412"),
            "UAI_URL": os.getenv("UAI_URL", "http://localhost:8080"),
            "FASTVLM_URL": os.getenv("FASTVLM_URL", "http://localhost:8088"),
            "GATEWAY_URL": os.getenv("GATEWAY_URL", "http://localhost:8015"),
        },
        "services": {},
        "tools": {},
        "recent_failures": []
    }
    
    # Check service health
    services_to_check = [
        ("agi_core", "http://localhost:8100/health"),
        ("mcp", os.getenv("MCP_URL", "http://localhost:8412") + "/health"),
        ("frontend_tools", "http://localhost:8413/health"),
        ("uai", "http://localhost:8080/health"),
        ("rag", "http://localhost:8093/health"),
    ]
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in services_to_check:
            try:
                resp = await client.get(url)
                snapshot["services"][name] = {
                    "status": "up" if resp.status_code == 200 else "degraded",
                    "http_code": resp.status_code
                }
            except Exception as e:
                snapshot["services"][name] = {"status": "down", "error": str(e)}
    
    # List available tools
    snapshot["tools"] = {
        name: {"url": url, "category": TOOL_SPECS[name].category if name in TOOL_SPECS else "unknown"}
        for name, url in TOOL_REGISTRY.items()
    }
    
    # TODO: Tail recent logs for failures (would need log aggregation or file access)
    # For now, leave empty
    
    logger.info(f"Doctor snapshot: {len([s for s in snapshot['services'].values() if s.get('status') == 'up'])} / {len(services_to_check)} services up")
    return snapshot


async def call_tool(name: str, payload: dict, *, 
                   timeout_s: float = 30.0,
                   retries: int = 1,
                   backoff_s: float = 1.0) -> dict:
    """
    Call a tool with retry logic and structured error handling.
    
    Returns dict with tool response + metadata (_rt_s, _tool, _attempt)
    Raises ToolError/ToolTimeout on exhausted retries
    """
    url = TOOL_REGISTRY.get(name)
    if not url:
        TOOL_CALLS.labels(tool=name, outcome="unknown_tool").inc()
        raise ToolError(f"unknown_tool:{name}")
    
    # Handle internal meta-tools
    if url.startswith("internal://"):
        t0 = time.time()
        if name == "system.doctor":
            result = await doctor_snapshot()
        elif name == "system.tools_refresh":
            # Discover all candidates from current registry
            candidates = [
                ToolSpec(name=k, url=v, ping_url=v.replace("/tool/", "/health") if "/tool/" in v else None)
                for k, v in TOOL_REGISTRY.items()
                if not v.startswith("internal://")
            ]
            result = await discover_tools(candidates)
        else:
            raise ToolError(f"unknown_internal_tool:{name}")
        
        result["_rt_s"] = round(time.time() - t0, 3)
        result["_tool"] = name
        result["_attempt"] = 1
        TOOL_CALLS.labels(tool=name, outcome="ok").inc()
        return result
    
    logger.info(f"Calling tool: {name} @ {url} (timeout={timeout_s}s, retries={retries})")
    t0 = time.time()
    last_err = None
    
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_s)) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                # Parse response
                if "application/json" in response.headers.get("content-type", ""):
                    result = response.json()
                else:
                    result = {"raw": response.text}
                
                # Add metadata
                result["_rt_s"] = round(time.time() - t0, 3)
                result["_tool"] = name
                result["_attempt"] = attempt + 1
                
                TOOL_CALLS.labels(tool=name, outcome="ok").inc()
                
                # Track RAG/Graph usage separately
                if name == "rag.query":
                    RAG_QUERIES.labels(outcome="ok").inc()
                elif name.startswith("graph."):
                    GRAPH_QUERIES.labels(outcome="ok").inc()
                
                logger.info(f"Tool {name} succeeded in {result['_rt_s']}s (attempt {attempt+1})")
                return result
                
        except httpx.ReadTimeout:
            last_err = ToolTimeout(f"timeout:{name} after {timeout_s}s")
            logger.warning(f"Tool {name} timeout on attempt {attempt+1}")
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            last_err = ToolError(f"http_{code}:{name}")
            logger.error(f"Tool {name} HTTP {code} on attempt {attempt+1}")
        except httpx.HTTPError as e:
            last_err = ToolError(f"http_error:{name}:{type(e).__name__}")
            logger.error(f"Tool {name} HTTP error on attempt {attempt+1}: {e}")
        except Exception as e:
            last_err = ToolError(f"error:{name}:{type(e).__name__}")
            logger.error(f"Tool {name} error on attempt {attempt+1}: {e}")
        
        # Backoff before retry
        if attempt < retries:
            wait = backoff_s * (attempt + 1)
            logger.info(f"Retrying {name} in {wait}s...")
            await asyncio.sleep(wait)
    
    # All retries exhausted
    outcome = "timeout" if isinstance(last_err, ToolTimeout) else "error"
    TOOL_CALLS.labels(tool=name, outcome=outcome).inc()
    raise last_err

