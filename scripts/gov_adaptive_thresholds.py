#!/usr/bin/env python3
"""
Adaptive Threshold Calculator for Governance System
Learns from historical decisions to adjust thresholds dynamically.

Analyzes past governance decisions to:
- Calculate rolling baselines for KPIs
- Adjust thresholds based on system stability
- Provide confidence scores for decisions
- Detect drift in system behavior

Usage:
  python3 scripts/gov_adaptive_thresholds.py --analyze-last-30-days
  python3 scripts/gov_adaptive_thresholds.py --update-thresholds
"""
import os, sys, json, time, statistics
from datetime import datetime, timedelta
from collections import defaultdict

LOG_FILE = "logs/canary_decisions.log"
THRESHOLDS_FILE = "state/adaptive_thresholds.json"

def parse_decision_log():
    """Parse audit log and extract decision data"""
    decisions = []

    if not os.path.exists(LOG_FILE):
        return decisions

    with open(LOG_FILE, "r") as f:
        for line in f:
            if "DECISION:" not in line:
                continue

            try:
                # Parse log line: "timestamp - DECISION: X - REASON: Y - METRICS: {...}"
                parts = line.strip().split(" - ")
                timestamp_str = parts[0]
                decision_part = parts[1]
                reason_part = parts[2] if len(parts) > 2 else ""
                metrics_part = parts[3] if len(parts) > 3 else ""

                # Parse timestamp
                timestamp = time.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
                timestamp_epoch = time.mktime(timestamp)

                # Parse decision
                decision = decision_part.replace("DECISION: ", "")

                # Parse metrics JSON
                metrics = {}
                if "METRICS:" in metrics_part:
                    metrics_json = metrics_part.replace("METRICS: ", "")
                    try:
                        metrics = json.loads(metrics_json)
                    except:
                        metrics = {}

                decisions.append({
                    "timestamp": timestamp_epoch,
                    "decision": decision,
                    "reason": reason_part.replace("REASON: ", ""),
                    "metrics": metrics
                })

            except Exception as e:
                # Skip malformed lines
                continue

    return decisions

def calculate_rolling_baselines(decisions, days=30):
    """Calculate rolling baselines from historical decisions"""
    cutoff_time = time.time() - (days * 24 * 60 * 60)

    # Filter recent decisions
    recent = [d for d in decisions if d["timestamp"] > cutoff_time]

    if len(recent) < 10:
        print(f"⚠️  Insufficient data: only {len(recent)} decisions in last {days} days")
        return None

    # Extract KPI values
    kpis = {
        "ece_post": [],
        "violation_rate_delta": [],
        "solve_rate_delta": [],
        "latency_p95_delta": [],
        "edge_case_score": [],
        "consistency_index": []
    }

    for decision in recent:
        metrics = decision["metrics"]
        for kpi in kpis:
            if kpi in metrics and metrics[kpi] is not None:
                kpis[kpi].append(metrics[kpi])

    # Calculate baselines
    baselines = {}
    for kpi, values in kpis.items():
        if len(values) >= 5:  # Need minimum samples
            baselines[kpi] = {
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "count": len(values),
                "percentile_95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else max(values)
            }

    return baselines

def analyze_decision_patterns(decisions, days=30):
    """Analyze patterns in governance decisions"""
    cutoff_time = time.time() - (days * 24 * 60 * 60)

    recent = [d for d in decisions if d["timestamp"] > cutoff_time]

    total_decisions = len(recent)
    if total_decisions == 0:
        return None

    # Count decision types
    decision_counts = defaultdict(int)
    for d in recent:
        decision_counts[d["decision"]] += 1

    # Calculate stability metrics
    promote_rate = decision_counts.get("PROMOTE", 0) / total_decisions
    rollback_rate = decision_counts.get("ROLLBACK", 0) / total_decisions
    hold_rate = decision_counts.get("HOLD", 0) / total_decisions

    # Calculate average time between decisions
    if len(recent) > 1:
        timestamps = sorted([d["timestamp"] for d in recent])
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval_hours = statistics.mean(intervals) / 3600
    else:
        avg_interval_hours = 0

    return {
        "total_decisions": total_decisions,
        "decision_distribution": dict(decision_counts),
        "stability_metrics": {
            "promote_rate": promote_rate,
            "rollback_rate": rollback_rate,
            "hold_rate": hold_rate,
            "avg_decision_interval_hours": avg_interval_hours
        }
    }

def calculate_adaptive_thresholds(baselines, patterns):
    """Calculate adaptive thresholds based on baselines and patterns"""
    if not baselines or not patterns:
        return None

    # Base thresholds (from governance_policy.yaml)
    adaptive = {
        "ece_threshold": 0.06,      # Base ECE threshold
        "violation_threshold": 0.005,  # Base violation threshold
        "solve_threshold": 0.02,    # Base solve rate threshold
        "confidence_score": 0.0,    # Overall confidence in thresholds
        "last_updated": time.time(),
        "rationale": []
    }

    # Adjust ECE threshold based on historical distribution
    if "ece_post" in baselines:
        ece_baseline = baselines["ece_post"]
        # If system is stable (low rollback rate), tighten threshold
        stability_factor = 1 - patterns["stability_metrics"]["rollback_rate"]

        # Adaptive threshold: mean + 2*stdev, but not below 0.03 or above 0.12
        suggested_ece = ece_baseline["mean"] + (2 * ece_baseline["stdev"])
        adaptive_ece = max(0.03, min(0.12, suggested_ece * stability_factor))

        adaptive["ece_threshold"] = round(adaptive_ece, 3)
        adaptive["rationale"].append(f"ECE threshold adapted to {adaptive_ece:.3f} based on {ece_baseline['count']} samples")

    # Adjust violation threshold based on patterns
    if "violation_rate_delta" in baselines and patterns["stability_metrics"]["rollback_rate"] < 0.1:
        viol_baseline = baselines["violation_rate_delta"]
        # If rollback rate is low, we can be more sensitive to violations
        adaptive_viol = max(0.001, viol_baseline["percentile_95"] * 0.8)  # 80% of 95th percentile
        adaptive["violation_threshold"] = round(adaptive_viol, 4)
        adaptive["rationale"].append(f"Violation threshold tightened to {adaptive_viol:.4f} due to system stability")

    # Calculate confidence score
    sample_sizes = [b["count"] for b in baselines.values()]
    avg_samples = statistics.mean(sample_sizes) if sample_sizes else 0
    stability_score = 1 - patterns["stability_metrics"]["rollback_rate"]

    # Confidence increases with more samples and better stability
    confidence = min(1.0, (avg_samples / 50) * stability_score)
    adaptive["confidence_score"] = round(confidence, 2)

    if confidence > 0.7:
        adaptive["rationale"].append("High confidence: sufficient samples and system stability")
    elif confidence > 0.4:
        adaptive["rationale"].append("Medium confidence: acceptable samples but monitor closely")
    else:
        adaptive["rationale"].append("Low confidence: limited samples, consider manual thresholds")

    return adaptive

def save_adaptive_thresholds(thresholds):
    """Save adaptive thresholds to state file"""
    os.makedirs("state", exist_ok=True)
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(thresholds, f, indent=2)

def load_adaptive_thresholds():
    """Load saved adaptive thresholds"""
    try:
        with open(THRESHOLDS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def print_analysis(baselines, patterns, adaptive):
    """Print comprehensive analysis"""
    print("🔍 Governance Adaptive Threshold Analysis")
    print("=" * 50)

    if patterns:
        print(f"📊 Decision Patterns (last {patterns.get('analysis_days', 30)} days):")
        print(f"   Total decisions: {patterns['total_decisions']}")
        print(f"   Distribution: {patterns['decision_distribution']}")
        print(".1%")
        print(".1f")
        print()

    if baselines:
        print("📈 KPI Baselines:")
        for kpi, stats in baselines.items():
            print("10")
        print()

    if adaptive:
        print("🎯 Adaptive Thresholds:")
        print(f"   ECE Threshold: {adaptive['ece_threshold']} (was 0.06)")
        print(f"   Violation Threshold: {adaptive['violation_threshold']} (was 0.005)")
        print(".1%")
        print()
        print("📝 Rationale:")
        for reason in adaptive["rationale"]:
            print(f"   • {reason}")
        print()
        print(f"💾 Thresholds saved to {THRESHOLDS_FILE}")
    else:
        print("⚠️  Could not calculate adaptive thresholds (insufficient data)")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Governance Adaptive Threshold Calculator")
    parser.add_argument("--analyze-last-days", type=int, default=30,
                       help="Days of history to analyze")
    parser.add_argument("--update-thresholds", action="store_true",
                       help="Update adaptive thresholds based on analysis")
    parser.add_argument("--show-current", action="store_true",
                       help="Show currently active adaptive thresholds")

    args = parser.parse_args()

    if args.show_current:
        current = load_adaptive_thresholds()
        if current:
            print("🎯 Current Adaptive Thresholds:")
            print(json.dumps(current, indent=2))
        else:
            print("❌ No adaptive thresholds currently active")
        return

    # Parse decision history
    decisions = parse_decision_log()

    if not decisions:
        print("❌ No decision history found in audit log")
        return

    # Calculate baselines and patterns
    baselines = calculate_rolling_baselines(decisions, args.analyze_last_days)
    patterns = analyze_decision_patterns(decisions, args.analyze_last_days)

    if patterns:
        patterns["analysis_days"] = args.analyze_last_days

    # Calculate adaptive thresholds
    adaptive = None
    if args.update_thresholds:
        adaptive = calculate_adaptive_thresholds(baselines, patterns)
        if adaptive:
            save_adaptive_thresholds(adaptive)

    # Print analysis
    print_analysis(baselines, patterns, adaptive)

if __name__ == "__main__":
    main()
