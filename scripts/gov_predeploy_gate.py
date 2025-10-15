#!/usr/bin/env python3
"""
Blocks deploy if governance health is red.
Env:
  PROM_URL        Prometheus base URL (default http://localhost:9090)
Thresholds (override via env if needed):
  ECE_MAX=0.06
  ENTROPY_CRIT=0.25
  VIOLATION_SPIKE=0.02
"""
import os, sys, json, urllib.request, urllib.parse

PROM = os.getenv("PROM_URL","http://localhost:9090")
ECE_MAX = float(os.getenv("ECE_MAX","0.06"))
ENTROPY_CRIT = float(os.getenv("ENTROPY_CRIT","0.25"))
VIOLATION_SPIKE = float(os.getenv("VIOLATION_SPIKE","0.02"))

def q(expr):
    url = f"{PROM}/api/v1/query?{urllib.parse.urlencode({'query':expr})}"
    with urllib.request.urlopen(url, timeout=5) as r:
        data = json.load(r)
        if data.get("status")!="success": raise RuntimeError(data)
        res = data["data"]["result"]
        if not res: return 0.0
        return float(res[0]["value"][1])

def main():
    # point-in-time health; use rate() for violation spikes if you track it as a counter
    ece = q("governance_ece")
    entropy = q("governance_entropy_drift")
    viol = q("governance_violation_rate")  # or rate(governance_policy_violations_total[5m])
    print(f"[gate] ece={ece:.3f} entropy={entropy:.3f} violation_rate={viol:.3f}")

    fails = []
    if ece > ECE_MAX: fails.append(f"ECE {ece:.3f}>{ECE_MAX}")
    if entropy >= ENTROPY_CRIT: fails.append(f"Entropy {entropy:.3f}>={ENTROPY_CRIT}")
    if viol > VIOLATION_SPIKE: fails.append(f"Violation {viol:.3f}>{VIOLATION_SPIKE}")

    if fails:
        print("❌ Governance gate BLOCKED:", "; ".join(fails))
        sys.exit(1)
    print("✅ Governance gate PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()
