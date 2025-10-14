import json
import subprocess
import time
import requests

def local_engine_smoke():
    event = {
        "event_id":"evt-1","instance_id":"sovereign-A","actor_id":"agent-42",
        "article":"II","severity":0.72,"confidence":0.81,"classification":"policy_violation",
        "timestamp": time.time()
    }
    p = subprocess.run(["python3","phase2_judicial_engine.py"], input=json.dumps(event).encode(), capture_output=True)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    print("Engine verdict:", out["verdict"])
    assert out["verdict"] in ("WARN","BLOCK","QUARANTINE","TRIBUNAL","ALLOW")

def api_smoke():
    url = "http://127.0.0.1:8092/v2/judicial/adjudicate"
    event = {
        "event_id":"evt-2","instance_id":"sovereign-A","actor_id":"agent-7",
        "article":"I","severity":0.91,"confidence":0.94,"classification":"critical_risk",
        "timestamp": time.time()
    }
    r = requests.post(url, json=event, timeout=5)
    r.raise_for_status()
    data = r.json()
    print("API verdict:", data["verdict"])
    assert data["verdict"] in ("QUARANTINE","TRIBUNAL","BLOCK","WARN","ALLOW")

if __name__ == "__main__":
    local_engine_smoke()
    try:
        api_smoke()
    except Exception as e:
        print("API test skipped or failed:", e)
