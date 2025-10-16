#!/usr/bin/env python3
import sys, yaml, json, hashlib, pathlib

def load_yaml(p):
    return yaml.safe_load(open(p))

def shax(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: policy_compiler.py policy/governance_policy.yaml policy/god_judge_verdict_mapping.yaml")
        sys.exit(1)
    pol = load_yaml(sys.argv[1])
    vmap = load_yaml(sys.argv[2])
    bundle = {"policy": pol, "verdict_mapping": vmap}
    out = pathlib.Path("manifests/policy_bundle.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"bundle": bundle, "hash": shax(bundle)}, indent=2))
    print("[compiler] wrote manifests/policy_bundle.json")
