#!/usr/bin/env python3
"""
Self-Tuning Canary Window System

Dynamically adjusts canary observation windows based on:
- Traffic volume (higher traffic = shorter windows)
- Historical decision patterns (stable systems = shorter windows)
- Decision confidence (high confidence = shorter windows)
- Risk tolerance settings

Usage:
  python3 scripts/gov_window_tuner.py --calculate-optimal --traffic-rate 100 --risk-tolerance medium
  python3 scripts/gov_window_tuner.py --get-current-settings
"""
import os, sys, json, time, statistics
from datetime import datetime, timedelta

DEFAULT_MIN_WINDOW = 5    # minutes
DEFAULT_MAX_WINDOW = 60   # minutes
DEFAULT_TARGET_WINDOW = 15 # minutes

def load_decision_history(days=7):
    """Load recent decision history for pattern analysis"""
    try:
        with open("logs/canary_decisions.log", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    decisions = []
    cutoff_time = time.time() - (days * 24 * 60 * 60)

    for line in lines:
        if " - DECISION:" not in line:
            continue

        try:
            parts = line.strip().split(" - ")
            timestamp_str = parts[0]
            decision_part = parts[1]

            timestamp = time.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
            timestamp_epoch = time.mktime(timestamp)

            if timestamp_epoch < cutoff_time:
                continue

            decision = decision_part.replace("DECISION: ", "")
            decisions.append({
                "timestamp": timestamp_epoch,
                "decision": decision
            })

        except Exception:
            continue

    return decisions

def analyze_system_stability(decisions, days=7):
    """Analyze system stability from decision patterns"""
    if not decisions:
        return {
            "stability_score": 0.5,  # Neutral
            "rollback_rate": 0.0,
            "decision_frequency_hours": 24,  # Conservative default
            "confidence": "low"
        }

    total_decisions = len(decisions)
    rollback_count = sum(1 for d in decisions if d["decision"] == "ROLLBACK")

    rollback_rate = rollback_count / total_decisions if total_decisions > 0 else 0

    # Calculate average time between decisions
    if len(decisions) > 1:
        timestamps = sorted([d["timestamp"] for d in decisions])
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval_hours = statistics.mean(intervals) / 3600
    else:
        avg_interval_hours = 24  # Conservative default

    # Calculate stability score (0-1, higher = more stable)
    stability_score = max(0, min(1, 1 - (rollback_rate * 2) - (avg_interval_hours / 48)))

    # Determine confidence level
    if stability_score > 0.8 and total_decisions > 20:
        confidence = "high"
    elif stability_score > 0.6 and total_decisions > 10:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "stability_score": stability_score,
        "rollback_rate": rollback_rate,
        "decision_frequency_hours": avg_interval_hours,
        "total_decisions": total_decisions,
        "confidence": confidence
    }

def estimate_traffic_impact(traffic_rate=None):
    """
    Estimate traffic impact on optimal window size.
    Higher traffic = can observe patterns faster = shorter windows.
    """
    if traffic_rate is None:
        # Try to estimate from recent metrics
        try:
            # This would integrate with your metrics system
            # For now, return neutral impact
            return 1.0
        except:
            return 1.0

    # Traffic impact factor (higher traffic = shorter windows)
    # 10 req/min = 1.5x faster observation
    # 100 req/min = 2x faster observation
    # 1000 req/min = 3x faster observation
    traffic_factor = min(3.0, max(0.5, traffic_rate / 50))
    return 1 / traffic_factor  # Convert to window multiplier

def calculate_optimal_window(stability_analysis, traffic_factor=1.0, risk_tolerance="medium"):
    """
    Calculate optimal canary observation window based on multiple factors.

    Returns window in minutes.
    """

    # Base window
    base_window = DEFAULT_TARGET_WINDOW

    # Stability adjustment (more stable = shorter window)
    stability_multiplier = 2 - stability_analysis["stability_score"]  # 1.0 to 2.0
    stable_window = base_window * stability_multiplier

    # Traffic adjustment (higher traffic = shorter window)
    traffic_adjusted_window = stable_window * traffic_factor

    # Risk tolerance adjustment
    risk_multipliers = {
        "low": 1.5,      # More conservative, longer windows
        "medium": 1.0,   # Standard
        "high": 0.7      # More aggressive, shorter windows
    }
    risk_multiplier = risk_multipliers.get(risk_tolerance, 1.0)
    risk_adjusted_window = traffic_adjusted_window * risk_multiplier

    # Confidence adjustment
    confidence_multipliers = {
        "high": 0.8,     # High confidence = shorter windows
        "medium": 1.0,   # Standard
        "low": 1.3       # Low confidence = longer windows
    }
    confidence_multiplier = confidence_multipliers.get(stability_analysis["confidence"], 1.0)
    final_window = risk_adjusted_window * confidence_multiplier

    # Clamp to reasonable bounds
    optimal_window = max(DEFAULT_MIN_WINDOW, min(DEFAULT_MAX_WINDOW, final_window))

    return {
        "optimal_window_minutes": round(optimal_window, 1),
        "base_window": base_window,
        "stability_multiplier": round(stability_multiplier, 2),
        "traffic_factor": round(traffic_factor, 2),
        "risk_multiplier": risk_multiplier,
        "confidence_multiplier": confidence_multiplier,
        "calculation_factors": {
            "stability_score": round(stability_analysis["stability_score"], 2),
            "rollback_rate": round(stability_analysis["rollback_rate"], 3),
            "decision_frequency_hours": round(stability_analysis["decision_frequency_hours"], 1),
            "confidence_level": stability_analysis["confidence"],
            "risk_tolerance": risk_tolerance
        }
    }

def save_window_settings(settings):
    """Save optimal window settings for use by canary system"""
    os.makedirs("state", exist_ok=True)
    with open("state/canary_window_settings.json", "w") as f:
        json.dump({
            **settings,
            "last_updated": time.time(),
            "version": "1.0"
        }, f, indent=2)

def load_window_settings():
    """Load current window settings"""
    try:
        with open("state/canary_window_settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "optimal_window_minutes": DEFAULT_TARGET_WINDOW,
            "last_updated": 0
        }

def print_window_analysis(analysis, settings):
    """Print detailed window analysis"""
    print("🎯 Self-Tuning Canary Window Analysis")
    print("=" * 50)

    print(f"📊 Stability Analysis:")
    factors = settings["calculation_factors"]
    print(f"   Stability Score: {factors['stability_score']:.1%}")
    print(f"   Rollback Rate: {factors['rollback_rate']:.1%}")
    print(f"   Decision Frequency: {factors['decision_frequency_hours']:.1f} hours")
    print(f"   Confidence Level: {factors['confidence_level']}")
    print()

    print("⚙️  Window Calculation:")
    print(f"   Base Window: {settings['base_window']} minutes")
    print(f"   Stability Multiplier: {settings['stability_multiplier']}")
    print(f"   Traffic Factor: {settings['traffic_factor']}")
    print(f"   Risk Multiplier: {settings['risk_multiplier']} ({factors['risk_tolerance']} tolerance)")
    print(f"   Confidence Multiplier: {settings['confidence_multiplier']}")
    print()

    print("🎯 Optimal Settings:")
    print(f"   Recommended Window: {settings['optimal_window_minutes']} minutes")
    print(f"   Range: {DEFAULT_MIN_WINDOW}-{DEFAULT_MAX_WINDOW} minutes")
    print()

    # Provide recommendations
    window = settings['optimal_window_minutes']
    if window <= 10:
        print("💡 Recommendation: Fast-tracked canary (high confidence/stable system)")
    elif window <= 20:
        print("💡 Recommendation: Standard canary window (balanced approach)")
    elif window <= 40:
        print("💡 Recommendation: Extended observation (lower confidence/caution advised)")
    else:
        print("💡 Recommendation: Conservative approach (system instability detected)")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Self-Tuning Canary Window Calculator")
    parser.add_argument("--calculate-optimal", action="store_true",
                       help="Calculate optimal window settings")
    parser.add_argument("--traffic-rate", type=float,
                       help="Current traffic rate (requests/minute)")
    parser.add_argument("--risk-tolerance", choices=["low", "medium", "high"], default="medium",
                       help="Risk tolerance level")
    parser.add_argument("--analysis-days", type=int, default=7,
                       help="Days of history to analyze")
    parser.add_argument("--get-current-settings", action="store_true",
                       help="Show current window settings")
    parser.add_argument("--save-settings", action="store_true",
                       help="Save calculated settings for canary system")

    args = parser.parse_args()

    if args.get_current_settings:
        current = load_window_settings()
        print("🎯 Current Canary Window Settings:")
        print(json.dumps(current, indent=2))
        return

    if args.calculate_optimal:
        # Load decision history
        decisions = load_decision_history(args.analysis_days)

        # Analyze system stability
        stability = analyze_system_stability(decisions, args.analysis_days)

        # Estimate traffic impact
        traffic_factor = estimate_traffic_impact(args.traffic_rate)

        # Calculate optimal window
        settings = calculate_optimal_window(stability, traffic_factor, args.risk_tolerance)

        # Print analysis
        print_window_analysis(stability, settings)

        # Save settings if requested
        if args.save_settings:
            save_window_settings(settings)
            print(f"💾 Settings saved to state/canary_window_settings.json")

        return

    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()
