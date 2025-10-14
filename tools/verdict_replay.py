#!/usr/bin/env python3
"""
Replay synthetic verdicts through the Exec action engine.
Usage:
  python tools/verdict_replay.py --verdict PASS
  python tools/verdict_replay.py --verdict SOFT_FAIL --actions QUARANTINE
  python tools/verdict_replay.py --verdict HARD_FAIL --actions ROLLBACK
"""
import argparse, json, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from exec.verdict_actions import ExecState, apply_verdict

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--verdict", required=True, choices=["PASS","SOFT_FAIL","HARD_FAIL"])
    p.add_argument("--task_id", default="T-demo-42")
    p.add_argument("--actions", nargs="*", default=[])
    p.add_argument("--ece", type=float, default=0.055)
    p.add_argument("--entropy", type=float, default=0.04)
    args = p.parse_args()

    verdict = {
        "task_id": args.task_id,
        "verdict": args.verdict,
        "calibrated_conf": 0.88 if args.verdict=="PASS" else 0.62,
        "ece_estimate": args.ece,
        "entropy_drift": args.entropy,
        "actions": args.actions
    }
    state = ExecState(safe_version="v1.8", current_version="v1.9-canary")
    print("[replay] input verdict:", json.dumps(verdict, indent=2))
    apply_verdict(verdict, state)
    print("[replay] final state:", state)

if __name__ == "__main__":
    main()
