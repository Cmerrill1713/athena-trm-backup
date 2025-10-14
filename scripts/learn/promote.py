#!/usr/bin/env python3
"""
Promote candidate if it beats baseline and is safe (=0 regressions).
- Updates models/registry.json
- Atomically switches models/trm/current -> artifacts/trm/<ts>
- Notifies via broker (optional)
"""
import argparse
import json
import os
import sys
import pathlib
import time
from typing import Dict, Any

REGISTRY = pathlib.Path("models/registry.json")
CURRENT = pathlib.Path("models/trm/current")


def load_metrics(path: pathlib.Path) -> Dict[str, Any]:
    """Load metrics.json from path"""
    p = path / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def safe_mkdirs():
    """Ensure model directories exist"""
    (REGISTRY.parent).mkdir(parents=True, exist_ok=True)
    (CURRENT.parent).mkdir(parents=True, exist_ok=True)


def update_registry(candidate_path: str, metrics: dict):
    """Add promotion to registry"""
    safe_mkdirs()
    reg = []
    if REGISTRY.exists():
        try:
            reg = json.loads(REGISTRY.read_text())
        except:
            reg = []

    reg.append({
        "name": "trm",
        "path": candidate_path,
        "metrics": metrics,
        "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    REGISTRY.write_text(json.dumps(reg, indent=2))


def switch_symlink(target: pathlib.Path):
    """Atomically switch current symlink to new target"""
    safe_mkdirs()
    tmp = CURRENT.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    tmp.symlink_to(target.resolve())
    if CURRENT.exists() or CURRENT.is_symlink():
        CURRENT.unlink()
    tmp.rename(CURRENT)


def broker_notify(msg: str):
    """Optional: notify via broker if available"""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
        from broker_client import BrokerClient

        client = BrokerClient()
        client.write_file(
            os.path.expanduser("~/Desktop/trm_promotion.txt"),
            msg
        )
        client.reveal_in_finder(os.path.expanduser("~/Desktop/trm_promotion.txt"))
        print("📬 Notification sent to Desktop")
    except Exception as e:
        print(f"⚠️  Broker notification skipped: {e}")


def main():
    ap = argparse.ArgumentParser(description="Promote TRM candidate if better + safe")
    ap.add_argument("--candidate", required=False, help="artifacts/trm/<ts>")
    ap.add_argument("--force", action="store_true", help="Promote even if not better")
    args = ap.parse_args()

    # Default to most recent artifacts dir
    if args.candidate:
        cand = pathlib.Path(args.candidate)
    else:
        artifact_dir = pathlib.Path("artifacts/trm")
        if not artifact_dir.exists():
            print(f"❌ No artifacts directory: {artifact_dir}")
            sys.exit(1)

        candidates = sorted(artifact_dir.glob("*"), key=lambda p: p.name, reverse=True)
        if not candidates:
            print(f"❌ No candidates in {artifact_dir}")
            sys.exit(1)
        cand = candidates[0]

    if not cand.exists():
        print(f"❌ Candidate missing: {cand}")
        sys.exit(1)

    print(f"📦 Candidate: {cand}")
    cm = load_metrics(cand)

    # Safety check: must have zero safety regressions
    if cm.get("safety_regressions", 0) != 0:
        print(f"❌ Safety regressions detected: {cm.get('safety_regressions')}")
        print("   Aborting promotion")
        sys.exit(1)

    # Get baseline accuracy
    try:
        base_m = load_metrics(CURRENT.resolve())
        base_acc = base_m.get("route_accuracy", 0.0)
        print(f"📊 Baseline accuracy: {base_acc}")
    except Exception:
        base_acc = 0.0
        print("⚠️  No baseline found, treating as 0.0")

    cand_acc = cm.get("route_accuracy", 0.0)
    print(f"📊 Candidate accuracy: {cand_acc}")

    # Improvement check
    if not args.force and cand_acc <= base_acc:
        print(f"❌ No improvement (candidate {cand_acc} <= baseline {base_acc})")
        print("   Use --force to promote anyway")
        sys.exit(1)

    # Promote!
    print(f"✅ Promoting {cand.name}...")
    switch_symlink(cand)
    update_registry(str(cand), cm)

    improvement = cand_acc - base_acc
    msg = f"""TRM Model Promoted!

Candidate: {cand.name}
Route Accuracy: {cand_acc} (baseline: {base_acc})
Improvement: +{improvement:.4f} ({improvement/base_acc*100 if base_acc > 0 else 0:.2f}%)
Safety Regressions: 0

Artifacts: {cand}
Registry: models/registry.json
Current: models/trm/current -> {cand.name}
"""

    print("\n" + "="*60)
    print(msg)
    print("="*60)

    broker_notify(msg)
    print("\n✅ Promotion complete!")


if __name__ == "__main__":
    main()
