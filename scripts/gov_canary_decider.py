#!/usr/bin/env python3
"""
Decide PROMOTE / HOLD / ROLLBACK based on canary KPIs in Prometheus.

Env:
  PROM_URL                  Prometheus base (default http://localhost:9090)
  WINDOW_MINUTES            How long to observe after deploy (default 15)
  MIN_SAMPLES               Minimum tasks in window to decide (default 200)
  # Policy thresholds (same as governance_policy.yaml)
  REQ_SOLVE_DELTA_GE        default 0.02
  REQ_VIOL_DELTA_LE         default 0.005
  REQ_P95_DELTA_LE          default 0.25
  REQ_ECE_POST_LE           default 0.06
  REQ_EDGE_SCORE_GE         default 0.80
  REQ_CONSIST_IDX_GE        default 0.90
Exit codes:
  0 -> PROMOTE
  10 -> HOLD (insufficient data)
  20 -> ROLLBACK
"""
import os, sys, json, urllib.request, urllib.parse, time

PROM = os.getenv("PROM_URL","http://localhost:9090")
WINDOW_MIN = int(os.getenv("WINDOW_MINUTES","15"))
MIN_SAMPLES = int(os.getenv("MIN_SAMPLES","200"))

def load_dynamic_window_settings():
    """Load dynamic window settings if available"""
    try:
        with open("state/canary_window_settings.json", "r") as f:
            settings = json.load(f)
            optimal_window = settings.get("optimal_window_minutes", WINDOW_MIN)
            # Only use if settings are recent (< 24 hours old)
            if time.time() - settings.get("last_updated", 0) < 86400:
                return optimal_window
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return WINDOW_MIN

# Use dynamic window if available
WINDOW_MIN = load_dynamic_window_settings()

# Load base thresholds
REQ_SOLVE = float(os.getenv("REQ_SOLVE_DELTA_GE","0.02"))
REQ_VIOL  = float(os.getenv("REQ_VIOL_DELTA_LE","0.005"))
REQ_P95   = float(os.getenv("REQ_P95_DELTA_LE","0.25"))
REQ_ECE   = float(os.getenv("REQ_ECE_POST_LE","0.06"))
REQ_EDGE  = float(os.getenv("REQ_EDGE_SCORE_GE","0.80"))
REQ_CONS  = float(os.getenv("REQ_CONSIST_IDX_GE","0.90"))

# Check for active threshold overrides (from Slack bot)
def load_threshold_overrides():
    """Load temporary threshold overrides if active"""
    try:
        with open("state/threshold_override.json", "r") as f:
            override = json.load(f)

        # Check if override is still valid
        if time.time() < override.get("expires_at", 0):
            return override
        else:
            # Expired override, remove file
            os.remove("state/threshold_override.json")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}

# Load adaptive thresholds if available (lower priority than manual overrides)
def load_adaptive_thresholds():
    """Load learned adaptive thresholds"""
    try:
        with open("state/adaptive_thresholds.json", "r") as f:
            adaptive = json.load(f)

        # Only use if confidence is reasonable
        if adaptive.get("confidence_score", 0) > 0.3:
            return adaptive
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}

# Apply thresholds in priority order: manual overrides > adaptive > defaults
overrides = load_threshold_overrides()
adaptive = load_adaptive_thresholds()

if "ece_threshold" in overrides:
    REQ_ECE = overrides["ece_threshold"]
    print(f"[override] ECE threshold manually set to {REQ_ECE} (expires: {time.ctime(overrides['expires_at'])})")
elif "ece_threshold" in adaptive:
    REQ_ECE = adaptive["ece_threshold"]
    print(f"[adaptive] ECE threshold learned at {REQ_ECE} (confidence: {adaptive.get('confidence_score', 0):.1%})")

if "violation_threshold" in adaptive and not overrides:  # Only apply adaptive if no manual override
    REQ_VIOL = adaptive["violation_threshold"]
    print(f"[adaptive] Violation threshold learned at {REQ_VIOL} (confidence: {adaptive.get('confidence_score', 0):.1%})")

def q(expr):
    url = f"{PROM}/api/v1/query?{urllib.parse.urlencode({'query':expr})}"
    with urllib.request.urlopen(url, timeout=8) as r:
        data = json.load(r)
        if data.get("status")!="success": raise RuntimeError(data)
        res = data["data"]["result"]
        if not res: return None
        return float(res[0]["value"][1])

def main():
    # You should expose these from your exporter/canary process
    solve_delta = q("governance_solve_rate_delta")
    viol_delta  = q("governance_violation_rate_delta")
    p95_delta   = q("governance_latency_p95_delta")
    ece_post    = q("governance_ece_post")
    edge_score  = q("governance_edge_case_score")
    cons_idx    = q("governance_consistency_index")
    # sample count in window; expose a counter or approximate via task rate
    samples     = q("governance_canary_samples_total")

    metrics = {
      "solve_rate_delta": solve_delta,
      "violation_rate_delta": viol_delta,
      "latency_p95_delta": p95_delta,
      "ece_post": ece_post,
      "edge_case_score": edge_score,
      "consistency_index": cons_idx,
      "samples": samples
    }

    print(json.dumps(metrics, indent=2))

    # Determine decision
    decision = "UNKNOWN"
    exit_code = 0
    reason = ""

    # Guard: insufficient data
    if samples is None or samples < MIN_SAMPLES:
        decision = "HOLD"
        exit_code = 10
        reason = f"samples={samples} < {MIN_SAMPLES}"
        print(f"[decider] {decision}: {reason}")
        log_decision(decision, reason, metrics)
        sys.exit(exit_code)

    # Any hard breaker -> rollback
    breakers = []
    if ece_post is not None and ece_post > REQ_ECE: breakers.append(f"ece_post {ece_post:.3f}>{REQ_ECE}")
    if viol_delta is not None and viol_delta > REQ_VIOL: breakers.append(f"viol_delta {viol_delta:.3f}>{REQ_VIOL}")
    if p95_delta is not None and p95_delta > REQ_P95: breakers.append(f"p95_delta {p95_delta:.2f}>{REQ_P95}")

    if breakers:
        decision = "ROLLBACK"
        exit_code = 20
        reason = f"{' '.join(breakers)}"
        print(f"[decider] {decision}: {reason}")
        log_decision(decision, reason, metrics)
        sys.exit(exit_code)

    # Positive promotion gate
    checks = []
    if solve_delta is None or solve_delta < REQ_SOLVE: checks.append("solve_delta")
    if edge_score is None or edge_score < REQ_EDGE:   checks.append("edge_case_score")
    if cons_idx is None or cons_idx < REQ_CONS:       checks.append("consistency_index")

    if checks:
        decision = "HOLD"
        exit_code = 10
        reason = f"waiting for {', '.join(checks)} to clear"
        print(f"[decider] {decision}: {reason}")
        log_decision(decision, reason, metrics)
        sys.exit(exit_code)

    decision = "PROMOTE"
    exit_code = 0
    reason = "All KPIs passed"
    print(f"[decider] {decision}")
    log_decision(decision, reason, metrics)
    sys.exit(exit_code)

def log_decision(decision, reason, metrics):
    """Log decision to audit trail"""
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/canary_decisions.log", "a") as f:
            timestamp = time.asctime()
            log_entry = f"{timestamp} - DECISION: {decision} - REASON: {reason} - METRICS: {json.dumps(metrics)}\n"
            f.write(log_entry)
    except Exception as e:
        # Don't fail the decision if logging fails
        print(f"[warning] Failed to write audit log: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
