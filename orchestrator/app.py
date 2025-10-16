import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Import AGI Core metrics if available
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agi_core.evaluation_metrics import get_metrics_collector
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    get_metrics_collector = None

APP_PORT = int(os.getenv("ORCH_PORT", "8000"))

# Use local paths by default, Docker paths when in container
BASE_DIR = Path(__file__).parent.parent
DEFAULT_STATE = str(BASE_DIR / "state" / "exec_state.json")
DEFAULT_LEDGER = str(BASE_DIR / "state" / "ledger" / "actions.log")

STATE_PATH = Path(os.getenv("EXEC_STATE_PATH", DEFAULT_STATE))
LEDGER_PATH = Path(os.getenv("ACTION_LEDGER_PATH", DEFAULT_LEDGER))

# Ensure directories exist (with error handling)
try:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    # If can't create (e.g., read-only filesystem), use temp dir
    import tempfile
    temp_dir = Path(tempfile.gettempdir()) / "orchestrator"
    temp_dir.mkdir(parents=True, exist_ok=True)
    STATE_PATH = temp_dir / "exec_state.json"
    LEDGER_PATH = temp_dir / "actions.log"

# ---- Metrics ----
VERDICTS = Counter("governance_verdicts_total", "Count of judicial verdicts", ["verdict_type"])
ACTIONS = Counter("governance_actions_total", "Count of exec actions taken", ["action"])
ECE_GAUGE = Gauge("governance_ece_post", "ECE reported with verdict")
ENTROPY_DRIFT_GAUGE = Gauge("governance_entropy_drift", "System entropy drift")
VIOL_DELTA = Gauge("governance_violation_rate_delta", "Violation rate delta")
LAT_P95_DELTA = Gauge("governance_latency_p95_delta", "Latency p95 delta")
SVC_UP = Gauge("governance_orchestrator_up", "Orchestrator liveness")

app = FastAPI(title="Governance Orchestrator", version="1.0.0")

# ---- Models ----
class ExecState(BaseModel):
    safe_version: str = "v1.8.0"
    current_version: str = "v1.9.0-canary"
    promotions_frozen_until: Optional[float] = None
    freeze_promotions: bool = False
    rollback_in_progress: bool = False
    quarantine_active: bool = False
    quarantine_percentage: float = 0.0
    require_human_review: bool = False
    last_updated: float = 0.0

class VerdictRequest(BaseModel):
    task_id: str
    verdict: str
    ece_estimate: Optional[float] = None
    entropy_drift: Optional[float] = None
    violation_rate_delta: Optional[float] = None
    latency_p95_delta: Optional[float] = None
    actions: Optional[List[str]] = None
    autoheal: Optional[Dict[str, Any]] = None
    fix_confidence: Optional[float] = None
    calibrated_conf: Optional[float] = None  # For SOFT_FAIL verdicts
    meta: Optional[Dict[str, Any]] = None
    
    @validator('verdict')
    def verdict_must_be_valid(cls, v):
        if v not in ['PASS', 'SOFT_FAIL', 'HARD_FAIL']:
            raise ValueError('verdict must be PASS, SOFT_FAIL, or HARD_FAIL')
        return v

# ---- State Management ----
def load_state() -> ExecState:
    """Load execution state from disk"""
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text())
            return ExecState(**data)
        except Exception as e:
            print(f"Warning: Failed to load state: {e}, using defaults")
    
    # Default state
    return ExecState()

def save_state(state: ExecState) -> None:
    """Save execution state to disk atomically"""
    state.last_updated = time.time()
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state.dict(), indent=2))
    tmp.replace(STATE_PATH)

def ledger_append(record: Dict[str, Any]) -> None:
    """Append to idempotence ledger with hash"""
    try:
        h = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        record["hash"] = h
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER_PATH.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        # Log but don't fail if ledger unavailable
        print(f"Warning: Failed to append to ledger: {e}")

# ---- Action Logic ----
def apply_verdict(verdict: VerdictRequest, state: ExecState) -> List[str]:
    """
    Apply verdict to state and return actions taken
    
    Business logic:
    - HARD_FAIL: Rollback to safe version, freeze promotions
    - SOFT_FAIL: Quarantine, maybe autoheal
    - PASS: Promote if not frozen
    """
    actions_taken = []
    
    if verdict.verdict == "HARD_FAIL":
        # Rollback to safe version
        if state.current_version != state.safe_version:
            state.current_version = state.safe_version
            state.rollback_in_progress = False  # Completed
            actions_taken.append("ROLLBACK")
        
        # Freeze promotions for 1 hour
        state.freeze_promotions = True
        state.promotions_frozen_until = time.time() + 3600
        actions_taken.append("FREEZE_PROMOTIONS")
    
    elif verdict.verdict == "SOFT_FAIL":
        # Quarantine - don't promote but don't rollback
        state.quarantine_active = True
        state.quarantine_percentage = 0.10  # Quarantine 10% of traffic
        actions_taken.append("QUARANTINE")
        
        # If high fix confidence, attempt autoheal
        if verdict.fix_confidence and verdict.fix_confidence > 0.8:
            actions_taken.append("AUTOHEAL_ATTEMPT")
        else:
            # Low confidence - require human review
            state.require_human_review = True
            actions_taken.append("RETRY_OR_HUMAN")
    
    elif verdict.verdict == "PASS":
        # Check if promotions are frozen
        if state.freeze_promotions:
            if state.promotions_frozen_until and time.time() > state.promotions_frozen_until:
                # Unfreeze
                state.freeze_promotions = False
                state.promotions_frozen_until = None
        
        # Promote if not frozen
        if not state.freeze_promotions:
            # Mark current as safe
            state.safe_version = state.current_version
            actions_taken.append("PROMOTE")
        else:
            actions_taken.append("HOLD")
    
    return actions_taken

def emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit event to event bus (simplified for now)"""
    # For now, just log it
    # In production, this would publish to NATS/Redis/etc
    print(f"EVENT: {event_type} -> {json.dumps(payload, default=str)}")

# ---- Routes ----
@app.get("/health")
def health():
    """Health check endpoint"""
    SVC_UP.set(1)
    return {
        "status": "healthy",
        "service": "governance-orchestrator",
        "timestamp": time.time()
    }

@app.get("/ready")
def ready():
    """Readiness check - ensures dependencies are available"""
    try:
        # Check if state file is accessible
        if STATE_PATH.exists():
            load_state()
        
        return {
            "status": "ready",
            "service": "governance-orchestrator",
            "checks": {
                "state_file": "ok",
                "ledger_dir": "ok" if LEDGER_PATH.parent.exists() else "unavailable"
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "governance-orchestrator",
            "error": str(e),
            "timestamp": time.time()
        }, 503

@app.get("/version")
def version():
    """Version information endpoint"""
    import os
    return {
        "service": "governance-orchestrator",
        "version": os.getenv("VERSION", "1.0.0"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "timestamp": time.time()
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/state")
def read_state():
    """Get current execution state"""
    state = load_state()
    return state.dict()

@app.post("/verdict")
def post_verdict(payload: Dict[str, Any] = Body(...)):
    """
    Accept a judicial verdict and apply governance actions
    
    This is the core governance endpoint that:
    1. Validates the verdict
    2. Updates metrics
    3. Applies actions (rollback/promote/quarantine)
    4. Persists state
    5. Emits events
    6. Records to ledger
    """
    # Parse and validate
    try:
        req = VerdictRequest(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    
    # Update observability gauges
    if req.ece_estimate is not None:
        ECE_GAUGE.set(req.ece_estimate)
    if req.entropy_drift is not None:
        ENTROPY_DRIFT_GAUGE.set(req.entropy_drift)
    if req.violation_rate_delta is not None:
        VIOL_DELTA.set(req.violation_rate_delta)
    if req.latency_p95_delta is not None:
        LAT_P95_DELTA.set(req.latency_p95_delta)
    
    # Increment verdict counter
    verdict_label = req.verdict.lower().replace('_', '_')
    VERDICTS.labels(verdict_type=verdict_label).inc()
    
    # Load current state
    state = load_state()
    
    # Apply verdict logic
    actions_taken = apply_verdict(req, state)
    
    # Save updated state
    save_state(state)
    
    # Update action metrics
    for action in actions_taken:
        ACTIONS.labels(action=action).inc()
    
    # Record governance metrics to AGI Core
    if METRICS_AVAILABLE:
        try:
            metrics_collector = get_metrics_collector()
            metrics_collector.record_governance_metrics(
                verdict=req.verdict,
                metrics={
                    "task_id": req.task_id,
                    "ece_estimate": req.ece_estimate,
                    "entropy_drift": req.entropy_drift,
                    "violation_rate_delta": req.violation_rate_delta,
                    "latency_p95_delta": req.latency_p95_delta,
                    "actions_taken": actions_taken,
                    "fix_confidence": req.fix_confidence,
                    "calibrated_conf": req.calibrated_conf,
                    "current_version": state.current_version,
                    "safe_version": state.safe_version
                }
            )
        except Exception as e:
            print(f"Warning: Failed to record governance metrics: {e}")
    
    # Emit event to bus
    emit_event("exec.verdict_applied", {
        "task_id": req.task_id,
        "verdict": req.verdict,
        "actions_taken": actions_taken,
        "new_state": state.dict(),
        "ece": req.ece_estimate,
        "violation_rate_delta": req.violation_rate_delta,
        "latency_p95_delta": req.latency_p95_delta,
        "ts": time.time()
    })
    
    # Append to idempotence ledger
    ledger_append({
        "ts": time.time(),
        "task_id": req.task_id,
        "verdict": req.verdict,
        "actions_taken": actions_taken,
        "state": state.dict()
    })
    
    return {
        "status": "applied",
        "task_id": req.task_id,
        "verdict": req.verdict,
        "actions_taken": actions_taken,
        "state": state.dict(),
        "timestamp": time.time()
    }

@app.post("/verdict/replay")
def replay_verdict(sample_name: str = "sample"):
    """
    Replay a verdict from samples (good for demos and chaos drills)
    """
    sample_path = Path(f"/app/schemas/samples/{sample_name}_verdict.json")
    
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample not found: {sample_name}")
    
    sample_data = json.loads(sample_path.read_text())
    
    # Route through main verdict handler
    return post_verdict(sample_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level="info")
