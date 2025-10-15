#!/usr/bin/env python3
"""
Athena Service
Provides chat, agents, and orchestration endpoints
"""
import asyncio
import json
import logging
import os
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "qwen2.5:7b")

# Add path for common imports (4 levels up: athena -> universal-ai-tools -> AI-Projects -> GitHub)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from common.ops import (
    add_health_endpoints,
    attach_guardrails,
    install_graceful_shutdown,
    wire_tracing,
)
from common.secrets import load_secret

try:
    from bandit.policy import bandit_policy, choose_prompt_variant, record_feedback
except ImportError:
    # Stub if bandit not available
    bandit_policy = None
    choose_prompt_variant = lambda: "control"
    record_feedback = lambda v, r: None
from judge import evaluate_and_save

# Bandit metrics
try:
    from prometheus_client import Counter, Gauge, Histogram
    bandit_trials = Counter("bandit_trials_total", "Bandit variant trials", ["variant"])
    bandit_wins = Counter("bandit_wins_total", "Bandit variant wins", ["variant"])
    bandit_selection_time = Histogram("bandit_selection_seconds", "Time to select bandit variant", buckets=[0.001, 0.005, 0.01, 0.05, 0.1])
    feedback_received = Counter("bandit_feedback_total", "Feedback events received", ["signal_type"])

    # Evaluation metrics
    judge_runs = Counter("judge_runs_total", "LLM judge evaluation runs", ["evaluator"])
    judge_scores = Gauge("judge_score_last", "Last judge score", ["metric"])

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    bandit_trials = bandit_wins = bandit_selection_time = feedback_received = None
    judge_runs = judge_scores = None

# Bandit configuration
USE_BANDIT = os.getenv("BANDIT_ENABLED", "false").lower() == "true"

# Unleash client for feature flags (simplified - in production use Unleash SDK)
def unleash_is_enabled(flag_name: str, user_id: str = None) -> bool:
    """Simple Unleash feature flag check (replace with proper SDK in production)"""
    # For now, check environment variable
    flag_env = os.getenv(f"UNLEASH_{flag_name.replace('.', '_').upper()}", "false")
    return flag_env.lower() == "true"


def render_prompt(variant_name: str, user_text: str, context: str = "") -> str:
    """Render a prompt template with user input and context."""
    try:
        template = bandit_policy.get_variant_template(variant_name)
        if not template:
            # Fallback to baseline
            template = bandit_policy.get_variant_template("v1_baseline") or ""

        # Simple template rendering (in production, use Jinja2)
        prompt = template.replace("{{user}}", user_text).replace("{{context}}", context)
        return prompt
    except Exception as e:
        logger.error("Prompt rendering failed", error=str(e), variant=variant_name)
        return f"You are Athena. Be helpful. Context: {context} User: {user_text}"


def save_interaction(user_text: str, reply_text: str, prompt_variant: str,
                    model_version: str, latency_ms: int, trace_id: str = None) -> str:
    """Save interaction to database for feedback correlation."""
    try:
        interaction_id = str(uuid.uuid4())
        # Note: In production, you'd want proper DB connection pooling
        # For now, we'll log the interaction for later processing
        logger.info("interaction_saved", {
            "interaction_id": interaction_id,
            "prompt_variant": prompt_variant,
            "model_version": model_version,
            "latency_ms": latency_ms,
            "trace_id": trace_id
        })
        return interaction_id
    except Exception as e:
        logger.error("Failed to save interaction", error=str(e))
        return str(uuid.uuid4())  # Return a UUID even on failure

app = FastAPI(title="Athena Service", version="1.0.0")

# Tier 4: Production hardening
add_health_endpoints(app)  # /live, /ready
wire_tracing(app, service_name="athena")  # OTLP tracing
attach_guardrails(
    app,
    per_ip_rate=os.getenv("RATE_LIMIT", "100/minute"),
    max_body_mb=int(os.getenv("MAX_BODY_MB", "5")),
    request_timeout_s=int(os.getenv("REQ_TIMEOUT_S", "30"))
)
install_graceful_shutdown(app, drain_seconds=int(os.getenv("DRAIN_S", "5")))

# Auth configuration (keychain-first, env fallback)
ATH_TOKEN = load_secret("ath_token", "ATH_TOKEN", "supersecret")
UAT_BASE = os.environ.get("UAT_BASE", "http://127.0.0.1:8181")

# Available agents
_agents = [
    {
        "id": "chat-agent",
        "name": "Chat Agent",
        "capabilities": ["chat", "conversation"],
        "status": "active"
    },
    {
        "id": "rag-agent",
        "name": "RAG Agent",
        "capabilities": ["retrieval", "knowledge"],
        "status": "active"
    },
    {
        "id": "code-agent",
        "name": "Code Agent",
        "capabilities": ["code", "analysis"],
        "status": "active"
    },
    {
        "id": "prompt-engineer",
        "name": "Prompt Engineer",
        "capabilities": ["prompt-optimization", "system-prompts", "context-adaptation"],
        "status": "active"
    },
    {
        "id": "research-agent",
        "name": "Research Agent",
        "capabilities": ["paper-discovery", "algorithm-extraction", "autonomous-implementation"],
        "status": "active"
    }
]

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.replace("Bearer ", "")
    if token != ATH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    return token

class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    route: str
    agent: str
    timestamp: str
    latency_ms: float
    metadata: Optional[Dict[str, Any]] = {}

class RunTestsRequest(BaseModel):
    suite: Optional[str] = "integration"
    markers: Optional[str] = ""
    verbose: bool = False
    maxfail: int = 1
    env: Optional[Dict[str, str]] = {}

class ToolCallRequest(BaseModel):
    tool: str
    params: Dict[str, Any]

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "athena",
        "timestamp": datetime.utcnow().isoformat(),
        "agents_available": len(_agents)
    }

async def call_ollama_llm(prompt: str, model: str = None, context: str = "") -> str:
    """
    Call Ollama LLM for real AI responses
    """
    model = model or DEFAULT_MODEL

    # Build full prompt with context if provided
    full_prompt = prompt
    if context:
        full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "No response from LLM")
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return f"LLM error: HTTP {response.status_code}"

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"LLM unavailable: {str(e)}"

@app.get("/agents")
async def get_agents(token: str = Depends(verify_token)):
    """Get available agents"""
    return {
        "agents": _agents,
        "count": len(_agents),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """Chat endpoint with routing"""
    start = time.time()

    # Select agent based on request
    agent_id = request.agent or "chat-agent"
    agent = next((a for a in _agents if a["id"] == agent_id), _agents[0])

    # Use the sophisticated routing system with RAG as default
    try:
        # Import the advanced routing system
        from src.core.routing.router_prompt import heuristic_route

        from src.api.trm_router import trm_route

        # Use TRM routing for intelligent decision making
        route_policy = trm_route(request.message, request.context or {})

        # Determine route based on policy
        if route_policy.rag.enabled:
            route = "rag-agent"
        elif route_policy.route == "code":
            route = "code-agent"
        elif route_policy.route == "reasoning_big":
            route = "reasoning-agent"
        else:
            route = "chat-agent"

        # Get RAG context if enabled
        rag_context = ""
        if route == "rag-agent":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    rag_response = await client.post(
                        "http://127.0.0.1:8015/api/rag/query",
                        json={"query": request.message, "k": route_policy.rag.k}
                    )
                    if rag_response.status_code == 200:
                        rag_data = rag_response.json()
                        if rag_data.get("hits"):
                            contexts = [hit.get("text", "") for hit in rag_data["hits"][:3]]
                            rag_context = "\n\n".join(contexts)
            except Exception as e:
                print(f"RAG query failed: {e}")

        logger.info(f"🧠 TRM routed to: {route} (RAG: {route_policy.rag.enabled}, k={route_policy.rag.k})")

    except ImportError as e:
        print(f"TRM router not available: {e}")
        # Fallback to heuristic routing with RAG as default
        message_lower = request.message.lower()

        # RAG should be considered for most substantive queries
        should_use_rag = True
        simple_patterns = ["hello", "hi", "hey", "thanks", "bye", "ok", "yes", "no", "how are you", "what's up"]

        # Only skip RAG for simple greetings or very short messages
        if any(pattern in message_lower for pattern in simple_patterns) or len(request.message.strip().split()) <= 2:
            should_use_rag = False

        if "code" in message_lower or "function" in message_lower or "debug" in message_lower:
            route = "code-agent"
        elif should_use_rag:
            route = "rag-agent"  # Default to RAG for most substantive queries
        else:
            route = "chat-agent"

        rag_context = ""

    # BANDIT PROMPT OPTIMIZATION
    # Select and render prompt variant using Thompson Sampling
    prompt_variant = "v1_baseline"  # Safe fallback
    bandit_enabled = USE_BANDIT and unleash_is_enabled("prompt.bandit.enabled")

    if bandit_enabled:
        try:
            selection_start = time.perf_counter()
            prompt_variant = choose_prompt_variant()
            selection_time = time.perf_counter() - selection_start

            # Record metrics
            if METRICS_AVAILABLE:
                bandit_trials.labels(variant=prompt_variant).inc()
                bandit_selection_time.observe(selection_time)

            logger.info("bandit_selected", variant=prompt_variant, user_id=token[:8] if token else None)
        except Exception as e:
            logger.error("bandit_selection_failed", error=str(e))
            prompt_variant = "v1_baseline"

    # Render the prompt with context and user input
    full_prompt = render_prompt(prompt_variant, request.message, rag_context)

    # Generate response
    if request.stream:
        async def generate():
            # Get LLM response using the bandit-selected prompt
            llm_response = await call_ollama_llm(prompt=full_prompt)

            # Stream the response word by word
            words = llm_response.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                await asyncio.sleep(0.05)  # Smooth streaming
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Call real LLM using the bandit-selected prompt
        llm_response = await call_ollama_llm(prompt=full_prompt)

        latency_ms = (time.time() - start) * 1000

        # Save interaction for feedback correlation
        interaction_id = save_interaction(
            user_text=request.message,
            reply_text=llm_response,
            prompt_variant=prompt_variant,
            model_version=DEFAULT_MODEL,
            latency_ms=int(latency_ms)
        )

        # LLM SELF-EVALUATION (post-generation quality assessment)
        eval_metrics = None
        if EVAL_ENABLED:
            try:
                # Evaluate response quality
                eval_metrics = await evaluate_and_save(
                    user_text=request.message,
                    reply_text=llm_response,
                    interaction_id=interaction_id,
                    context=rag_context
                )

                # Record evaluation metrics
                if METRICS_AVAILABLE and eval_metrics:
                    judge_runs.labels(evaluator="llm-judge:v1").inc()
                    judge_scores.labels(metric="helpfulness").set(eval_metrics["helpfulness"])
                    judge_scores.labels(metric="factuality").set(eval_metrics["factuality"])
                    judge_scores.labels(metric="clarity").set(eval_metrics["clarity"])

            except Exception as e:
                logger.error("Evaluation failed", error=str(e), interaction_id=interaction_id)

        # Calculate provisional reward (positive for fast, error-free responses)
        provisional_reward = max(0.0, 1.0 - min(latency_ms, 3000)/3000.0) * 0.1

        # Add evaluation-based reward component (if available)
        if eval_metrics:
            # Normalize eval scores (1-10) to reward component (-0.5 to +0.5)
            eval_score = (eval_metrics["helpfulness"] + eval_metrics["factuality"] + eval_metrics["clarity"]) / 3.0
            eval_reward = (eval_score - 5.5) / 9.0  # Center at 5.5, scale to -0.5..+0.5
            provisional_reward += 0.25 * eval_reward  # Small weight for evaluation

        # Record provisional win for bandit (only if bandit was enabled)
        if bandit_enabled and METRICS_AVAILABLE and provisional_reward > 0:
            bandit_wins.labels(variant=prompt_variant).inc()

        response = ChatResponse(
            response=llm_response,
            route=route,
            agent=agent["id"],
            timestamp=datetime.utcnow().isoformat(),
            latency_ms=latency_ms,
            metadata={
                "rag_used": route == "rag-agent",
                "context_length": len(rag_context) if rag_context else 0,
                "model": DEFAULT_MODEL,
                "llm_backend": "ollama",
                "prompt_variant": prompt_variant,
                "interaction_id": interaction_id,
                "bandit_enabled": USE_BANDIT and unleash_is_enabled("prompt.bandit.enabled"),
                "eval_enabled": EVAL_ENABLED,
                "eval_scores": eval_metrics
            }
        )

        # Log completion with evaluation data
        logger.info("chat_completed", {
            "variant": prompt_variant,
            "latency_ms": int(latency_ms),
            "interaction_id": interaction_id,
            "provisional_reward": provisional_reward,
            "bandit_enabled": bandit_enabled,
            "eval_enabled": EVAL_ENABLED,
            "eval_helpfulness": eval_metrics.get("helpfulness") if eval_metrics else None,
            "eval_factuality": eval_metrics.get("factuality") if eval_metrics else None,
            "eval_clarity": eval_metrics.get("clarity") if eval_metrics else None
        })

        return response

@app.get("/capabilities")
async def get_capabilities(token: str = Depends(verify_token)):
    """Get service capabilities"""
    return {
        "service": "athena",
        "version": "1.0.0",
        "capabilities": [
            "chat",
            "streaming",
            "routing",
            "agents",
            "tool_calls",
            "test_execution"
        ],
        "endpoints": {
            "chat": "POST /chat",
            "agents": "GET /agents",
            "health": "GET /health",
            "capabilities": "GET /capabilities",
            "run_tests": "POST /run_tests",
            "tool_call": "POST /tool_call"
        }
    }

@app.post("/run_tests")
async def run_tests(
    request: RunTestsRequest,
    token: str = Depends(verify_token)
):
    """Run pytest tests and return structured results"""

    # Navigate to the GitHub root directory (3 levels up from athena/api.py)
    # api.py -> athena -> universal-ai-tools -> AI-Projects -> GitHub
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    # Build pytest command (use python3 -m pytest for correct environment)
    cmd_parts = ["python3", "-m", "pytest", "tests/"]

    if request.markers:
        # Convert comma-separated markers to 'or' expression for pytest
        markers_expr = " or ".join(m.strip() for m in request.markers.split(","))
        cmd_parts.extend(["-m", markers_expr])

    cmd_parts.extend([
        f"--maxfail={request.maxfail}",
        "--disable-warnings",
        "-q" if not request.verbose else "-v",
        "--json-report",
        "--json-report-file=pytest_report.json"
    ])

    # Keep as list for proper subprocess handling
    cmd = " ".join(cmd_parts)  # For logging only

    try:
        # Build environment with caller-provided tokens/bases
        env = os.environ.copy()

        # Merge caller-provided env (UAT/ATH/BRIDGE tokens, bases, etc.)
        if request.env:
            for k, v in request.env.items():
                if isinstance(v, str):
                    env[k] = v

        # Run pytest with list (not split string) to preserve arguments
        proc = subprocess.run(
            cmd_parts,  # Use list directly instead of shlex.split(cmd)
            cwd=workspace_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=900  # 15 min for full suite
        )

        # Try to read JSON report
        report = {}
        report_path = os.path.join(workspace_root, "pytest_report.json")
        report_exists = False
        try:
            with open(report_path) as f:
                report = json.load(f)
                report_exists = True
        except Exception as e:
            report = {"error": f"Failed to read report: {str(e)}"}

        # Parse output for summary
        stdout_lines = proc.stdout.split('\n')
        summary = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }

        for line in stdout_lines:
            if "passed" in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "passed" in part.lower() and i > 0:
                            summary["passed"] = int(parts[i-1])
                except:
                    pass
            if "failed" in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "failed" in part.lower() and i > 0:
                            summary["failed"] = int(parts[i-1])
                except:
                    pass

        # Build response with full transparency (receipts not vibes)
        response_data = {
            "ok": proc.returncode == 0,
            "cmd": cmd,
            "args": cmd_parts,  # Exact args passed to pytest
            "cwd": workspace_root,
            "python": sys.executable,  # Which Python Athena is using
            "env_used": {  # Environment variables actually used
                k: env.get(k, "(not set)")
                for k in ["BRIDGE_BASE", "UAT_BASE", "ATHENA_BASE",
                         "UAT_TOKEN", "ATH_TOKEN", "BRIDGE_TOKEN",
                         "PYTEST_ADDOPTS", "PYTHONPATH"]
            },
            "summary": summary,
            "stdout": proc.stdout[-2000:],  # tail
            "stderr": proc.stderr[-2000:],
            "report": report,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add artifact path if report exists (for CI artifact upload)
        if report_exists:
            response_data["artifact_path"] = report_path

        # Return non-200 status if tests failed (makes CI stricter)
        if proc.returncode != 0:
            return JSONResponse(
                status_code=422,  # Unprocessable Entity - tests ran but failed
                content=response_data
            )

        return response_data

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Tests timeout after 10 minutes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@app.post("/tool_call")
async def tool_call(
    request: ToolCallRequest,
    token: str = Depends(verify_token)
):
    """Execute tool calls - allows Athena to perform actions"""

    tool = request.tool
    params = request.params

    # Define available tools
    if tool == "run_command":
        # Run a shell command (restricted to safe commands)
        cmd = params.get("command", "")
        allowed_commands = ["pytest", "ls", "cat", "grep", "find", "echo", "pwd"]

        # Check if command starts with allowed prefix
        if not any(cmd.strip().startswith(allowed) for allowed in allowed_commands):
            raise HTTPException(status_code=403, detail=f"Command not allowed: {cmd}")

        try:
            result = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Command timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif tool == "read_file":
        # Read a file
        file_path = params.get("path", "")
        max_lines = params.get("max_lines", 100)

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()[:max_lines]
            return {
                "success": True,
                "content": "".join(lines),
                "lines_read": len(lines),
                "path": file_path
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    elif tool == "list_directory":
        # List directory contents
        dir_path = params.get("path", ".")

        try:
            items = os.listdir(dir_path)
            return {
                "success": True,
                "items": items,
                "count": len(items),
                "path": dir_path
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")


