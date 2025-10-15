# tools/eval_api.py
import glob
import json
import os
import sqlite3
import time
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

EVDB = os.environ.get("EVAL_DB", "./state/eval.sqlite")
FIXTURES = os.environ.get("EVAL_FIXTURES", "./eval/fixtures/*.json")

app = FastAPI(title="NeuroForge Eval", version="1.0")

def _ensure_db():
    os.makedirs("./state", exist_ok=True)
    with sqlite3.connect(EVDB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS eval_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL,
            capability TEXT,
            fixture TEXT,
            composite REAL,
            p50_latency REAL,
            passed INTEGER,
            raw_json TEXT
        )""")

def _score(capability: str, out: Dict[str,Any], expected: Dict[str,Any]) -> Dict[str,float]:
    # lightweight: correctness (tldr non-empty + next_action match if provided),
    # structure (facts >= expected min), latency
    s_corr = 1.0 if out.get("tldr") else 0.0
    if expected.get("next_action"):
        s_corr = 1.0 if out.get("next_action")==expected["next_action"] else 0.5
    s_struct = 1.0 if len(out.get("facts",[])) >= expected.get("min_facts", 2) else 0.5
    lat = out.get("metrics",{}).get("latency_ms", 0)
    s_lat = 1.0 if lat <= expected.get("max_latency_ms", 1500) else 0.5
    comp = 0.5*s_corr + 0.3*s_struct + 0.2*s_lat
    return {"composite": comp, "corr": s_corr, "struct": s_struct, "lat": s_lat, "latency_ms": lat}

class EvalRequest(BaseModel):
    capability: str
    limit: int = 0  # 0 = all
    warm_memory: bool = True
    params: Dict[str,Any] = {}

@app.post("/eval/run")
def eval_run(req: EvalRequest):
    _ensure_db()
    files = sorted(glob.glob(FIXTURES))
    if req.limit > 0:
        files = files[:req.limit]

    results = []
    for fp in files:
        try:
            fx = json.load(open(fp))
            record = fx["record"]
            expected = fx.get("expected", {})

            # Placeholder: Replace with your actual capability runner
            # res = run_capability(req.capability, record, req.params)
            # For now, mock a response
            out = {
                "tldr": "Mock response",
                "facts": ["fact1", "fact2"],
                "next_action": expected.get("next_action", "review"),
                "metrics": {"latency_ms": 500}
            }

            sc = _score(req.capability, out, expected)
            results.append({"fixture": os.path.basename(fp), "score": sc, "output": out})

            with sqlite3.connect(EVDB) as c:
                c.execute(
                    "INSERT INTO eval_runs(ts, capability, fixture, composite, p50_latency, passed, raw_json) VALUES (?,?,?,?,?,?,?)",
                    (time.time(), req.capability, os.path.basename(fp), sc["composite"], sc["latency_ms"], int(sc["composite"]>=0.7), json.dumps({"out": out, "score": sc}))
                )
        except Exception as e:
            print(f"Error processing {fp}: {e}")
            continue

    passed = sum(1 for r in results if r["score"]["composite"]>=0.7)
    return {"capability": req.capability, "total": len(results), "passed": passed, "results": results}

@app.get("/eval/fixtures")
def list_fixtures():
    return {"fixtures": [os.path.basename(f) for f in sorted(glob.glob(FIXTURES))]}

@app.get("/eval/history")
def eval_history(capability: str = None, limit: int = 50):
    """Get evaluation history"""
    _ensure_db()
    query = "SELECT * FROM eval_runs"
    params = ()

    if capability:
        query += " WHERE capability=?"
        params = (capability,)

    query += " ORDER BY ts DESC LIMIT ?"
    params = params + (limit,)

    rows = _rows(query, params)
    return {"history": [dict(r) for r in rows]}

@app.get("/health")
def health():
    return {"ok": True, "service": "eval_api", "fixtures_pattern": FIXTURES}

