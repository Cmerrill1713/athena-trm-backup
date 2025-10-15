#!/usr/bin/env python3
"""
Synthetic probe for governance system - Devil's Advocate testing.
Triggers canary analysis with synthetic "bad" scenarios to keep metrics warm
and catch regressions off-hours.

Usage:
  python3 scripts/devil_advocate_probe.py --shadow-slice --canary-trigger
  python3 scripts/devil_advocate_probe.py --inject-failure --type entropy_spike
"""
import os, sys, json, time, random, argparse
import urllib.request

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

def inject_synthetic_metric(metric_name, value, labels=""):
    """Inject synthetic metric via Prometheus pushgateway"""
    push_url = f"http://localhost:9091/metrics/job/governance_synthetic"
    data = f"# TYPE {metric_name} gauge\n{metric_name}{labels} {value}\n"
    req = urllib.request.Request(push_url, data=data.encode(), method='POST')
    try:
        urllib.request.urlopen(req)
        print(f"Injected {metric_name}={value}")
        return True
    except Exception as e:
        print(f"Failed to inject metric: {e}")
        return False

def trigger_canary():
    """Trigger canary analysis by calling the decider"""
    os.system("python3 scripts/gov_canary_decider.py || true")

def run_scenario(scenario):
    """Run a specific synthetic failure scenario"""
    print(f"Running Devil's Advocate scenario: {scenario}")

    if scenario == "ece_spike":
        # Inject high ECE to trigger rollback
        inject_synthetic_metric("governance_ece", 0.08)
        time.sleep(5)
        trigger_canary()

    elif scenario == "entropy_spike":
        # Inject high entropy drift
        inject_synthetic_metric("governance_entropy_drift", 0.30)
        time.sleep(5)
        trigger_canary()

    elif scenario == "violation_spike":
        # Inject high violation rate
        inject_synthetic_metric("governance_violation_rate", 0.03)
        time.sleep(5)
        trigger_canary()

    elif scenario == "latency_spike":
        # Inject high latency delta
        inject_synthetic_metric("governance_latency_p95_delta", 0.30)
        time.sleep(5)
        trigger_canary()

    elif scenario == "low_solve_rate":
        # Inject low solve rate delta
        inject_synthetic_metric("governance_solve_rate_delta", 0.01)
        inject_synthetic_metric("governance_edge_case_score", 0.85)
        inject_synthetic_metric("governance_consistency_index", 0.95)
        inject_synthetic_metric("governance_canary_samples_total", 300)
        time.sleep(5)
        trigger_canary()

    elif scenario == "random_good":
        # Inject good metrics to test promote path
        inject_synthetic_metric("governance_solve_rate_delta", 0.04)
        inject_synthetic_metric("governance_edge_case_score", 0.90)
        inject_synthetic_metric("governance_consistency_index", 0.95)
        inject_synthetic_metric("governance_canary_samples_total", 300)
        inject_synthetic_metric("governance_ece", 0.03)
        inject_synthetic_metric("governance_entropy_drift", 0.15)
        inject_synthetic_metric("governance_violation_rate", 0.005)
        time.sleep(5)
        trigger_canary()

    print(f"Scenario {scenario} completed")

def main():
    parser = argparse.ArgumentParser(description="Governance Synthetic Probe - Devil's Advocate")
    parser.add_argument("--scenario", choices=[
        "ece_spike", "entropy_spike", "violation_spike", "latency_spike",
        "low_solve_rate", "random_good"
    ], help="Specific scenario to run")
    parser.add_argument("--shadow-slice", action="store_true",
                       help="Run on shadow traffic slice")
    parser.add_argument("--canary-trigger", action="store_true",
                       help="Trigger canary analysis after injection")
    parser.add_argument("--all-scenarios", action="store_true",
                       help="Run all scenarios in sequence")

    args = parser.parse_args()

    if args.all_scenarios:
        scenarios = ["ece_spike", "entropy_spike", "violation_spike",
                    "latency_spike", "low_solve_rate", "random_good"]
        for scenario in scenarios:
            run_scenario(scenario)
            time.sleep(30)  # Wait between scenarios
    elif args.scenario:
        run_scenario(args.scenario)
    else:
        # Default: run a random scenario
        scenarios = ["ece_spike", "entropy_spike", "violation_spike",
                    "low_solve_rate", "random_good"]
        scenario = random.choice(scenarios)
        run_scenario(scenario)

if __name__ == "__main__":
    main()
