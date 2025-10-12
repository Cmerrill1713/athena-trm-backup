#!/usr/bin/env python3
"""Check eval threshold helper for CI"""
import json
import sys

def ok(r):
    return (r.get("total", 0) > 0) and (r.get("passed", 0) / r.get("total", 1) >= 0.80)

sumr = json.load(open(sys.argv[1]))
plan = json.load(open(sys.argv[2]))

if not (ok(sumr) and ok(plan)):
    print("❌ Nightly eval below threshold (<80%)")
    sys.exit(1)
else:
    print("✅ Nightly eval passed (≥80%)")
