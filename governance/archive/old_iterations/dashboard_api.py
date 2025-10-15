# tools/dashboard_api.py
import json
import os
import sqlite3
import time
from typing import List, Tuple

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

DB = os.environ.get("TELEMETRY_DB", "./state/telemetry.sqlite")
BANDIT = os.environ.get("BANDIT_STATE", "./state/bandit.json")

app = FastAPI(title="NeuroForge Grafana-Lite", version="1.0")

def _rows(q: str, params: Tuple=()) -> List[sqlite3.Row]:
    if not os.path.exists(DB):
        return []
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        return list(c.execute(q, params))

def _percentile(p: float, xs: List[float]) -> float:
    if not xs: return 0
    xs_sorted = sorted(xs)
    k = max(0, min(len(xs_sorted)-1, int(round((p/100.0)*(len(xs_sorted)-1)))))
    return float(xs_sorted[k])

@app.get("/metrics/latency")
def metrics_latency(capability: str = Query(...), hours: int = 24):
    cutoff = time.time() - hours*3600
    rows = _rows(
        "SELECT duration_ms, raw_json FROM traces WHERE capability=? AND started_at>=?",
        (capability, cutoff)
    )
    # prefer per-output latency if present; else trace duration
    lats = []
    for r in rows:
        try:
            raw = json.loads(r["raw_json"])
            out = json.loads(r["raw_json"])  # same blob; keep simple
            # pull latency from last event output metrics if present
            events = raw.get("events", [])
            latency = None
            for e in reversed(events):
                data = e.get("data", {})
                for k in ("score","subs","provider"): pass
                # fall back to trace duration if no metrics on output
            latency = raw.get("duration_ms", r["duration_ms"])
            lats.append(float(latency))
        except Exception:
            lats.append(float(r["duration_ms"]))
    return {
        "capability": capability,
        "count": len(lats),
        "p50": _percentile(50, lats),
        "p95": _percentile(95, lats),
        "samples": lats[-200:],  # tail for sparkline
    }

@app.get("/metrics/winrates")
def metrics_winrates(capability: str):
    if not os.path.exists(BANDIT):
        return {"capability": capability, "providers": {}}
    with open(BANDIT, "r") as f:
        state = json.load(f)
    provs = state.get(capability, {})
    out = {}
    for name, s in provs.items():
        wins, losses = s.get("wins",1), s.get("losses",1)
        samples = s.get("samples", 0)
        out[name] = {
            "win_rate": wins / max(1, (wins+losses)),
            "samples": samples,
            "promotable": bool(s.get("promotable", False)),
        }
    return {"capability": capability, "providers": out}

@app.get("/metrics/shadow-delta")
def metrics_shadow_delta(capability: str, hours: int = 24):
    cutoff = time.time() - hours*3600
    rows = _rows(
        "SELECT raw_json FROM traces WHERE capability=? AND started_at>=?",
        (capability, cutoff)
    )
    deltas = []
    for r in rows:
        try:
            raw = json.loads(r["raw_json"])
            primary = next((e for e in raw.get("events",[]) if e["label"]=="primary_result"), None)
            shadow = next((e for e in raw.get("events",[]) if e["label"]=="shadow_result"), None)
            if primary and shadow:
                deltas.append(float(shadow["data"]["score"] - primary["data"]["score"]))
        except Exception:
            pass
    return {
        "capability": capability,
        "count": len(deltas),
        "mean_delta": (sum(deltas)/len(deltas)) if deltas else 0.0,
        "wins_shadow": sum(1 for d in deltas if d>0),
        "wins_primary": sum(1 for d in deltas if d<=0),
        "deltas_tail": deltas[-200:],
    }

# minimal HTML dashboard
@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html><html><head>
<meta charset="utf-8"/><title>NeuroForge Grafana-Lite</title>
<style>body{font-family:system-ui,Segoe UI,Arial;margin:24px} .row{display:flex;gap:24px;flex-wrap:wrap} .card{border:1px solid #ddd;border-radius:8px;padding:16px;flex:1;min-width:320px}</style>
</head><body>
<h1>NeuroForge Grafana-Lite</h1>
<div style="margin-bottom:12px">
<label>Capability: <input id="cap" value="summarize"></label>
<button onclick="loadAll()">Load</button>
</div>
<div class="row">
  <div class="card"><h3>Latency (p50/p95)</h3><pre id="lat"></pre></div>
  <div class="card"><h3>Win Rates</h3><pre id="win"></pre></div>
  <div class="card"><h3>Shadow Δ (shadow - primary)</h3><pre id="shad"></pre></div>
</div>
<script>
async function loadAll(){
  const cap = document.getElementById('cap').value || 'summarize';
  const lat = await fetch(`/metrics/latency?capability=${cap}`).then(r=>r.json());
  const win = await fetch(`/metrics/winrates?capability=${cap}`).then(r=>r.json());
  const shd = await fetch(`/metrics/shadow-delta?capability=${cap}`).then(r=>r.json());
  document.getElementById('lat').textContent = JSON.stringify(lat, null, 2);
  document.getElementById('win').textContent = JSON.stringify(win, null, 2);
  document.getElementById('shad').textContent = JSON.stringify(shd, null, 2);
}
loadAll();
</script>
</body></html>
"""

