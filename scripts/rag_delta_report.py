#!/usr/bin/env python3
"""
RAG Delta Report - Compare two evaluation modes (e.g., BM25 vs Semantic).

Runs eval_rag_hit_support.py twice with different modes, computes deltas,
and emits JSON + Markdown reports for CI/CD pipelines.

Usage:
  python3 scripts/rag_delta_report.py \
    --baseline-mode bm25 \
    --treatment-mode nearText \
    --seed seeds/eval_seed.jsonl \
    --expect-hit 0.97 --expect-support 0.95

With delta gates (fail if improvement not significant):
  python3 scripts/rag_delta_report.py \
    --baseline-mode bm25 \
    --treatment-mode nearText \
    --seed seeds/eval_seed.jsonl \
    --min-delta-hit 0.01 \
    --min-delta-support 0.01 \
    --max-delta-latency-p95 0.1 \
    --fail-on-delta-gates
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Tuple


def run_eval(script: str, common_args: list, mode: str, report_path: str) -> Tuple[Dict[str, Any], int]:
    """
    Run the evaluation script with the given mode and return parsed results.
    
    Returns:
        Tuple of (parsed_json_report, return_code)
    """
    cmd = [
        sys.executable, script,
        "--mode", mode,
        "--report", report_path,
    ] + common_args
    
    print(f"\n🔍 Running {mode} evaluation...", file=sys.stderr)
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    # Allow return code 0 (success) or 1 (quality gates failed)
    # We want to read the report even if gates failed
    if res.returncode not in (0, 1):
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        raise SystemExit(f"Evaluation script failed with code {res.returncode}")
    
    # The report should be on disk even if gates failed
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report not found: {report_path}")
    
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f), res.returncode


def pct(x: float) -> float:
    """Convert fraction to percentage with 2 decimal places."""
    return round(x * 100.0, 2)


def check_delta_gates(delta: Dict[str, Any], args: argparse.Namespace) -> Tuple[bool, list]:
    """
    Check if delta meets minimum improvement thresholds.
    
    Returns:
        Tuple of (passed, list_of_violations)
    """
    violations = []
    
    if hasattr(args, 'min_delta_hit') and args.min_delta_hit is not None:
        if delta['delta']['hit@k'] < args.min_delta_hit:
            violations.append(
                f"hit@k delta {pct(delta['delta']['hit@k'])}% < "
                f"required {pct(args.min_delta_hit)}%"
            )
    
    if hasattr(args, 'min_delta_support') and args.min_delta_support is not None:
        if delta['delta']['support@k'] < args.min_delta_support:
            violations.append(
                f"support@k delta {pct(delta['delta']['support@k'])}% < "
                f"required {pct(args.min_delta_support)}%"
            )
    
    if hasattr(args, 'min_delta_mrr') and args.min_delta_mrr is not None:
        if delta['delta']['mrr@k'] < args.min_delta_mrr:
            violations.append(
                f"mrr@k delta {delta['delta']['mrr@k']:.4f} < "
                f"required {args.min_delta_mrr:.4f}"
            )
    
    if hasattr(args, 'max_delta_latency_p95') and args.max_delta_latency_p95 is not None:
        if delta['delta']['latency_sec_p95'] > args.max_delta_latency_p95:
            violations.append(
                f"latency p95 delta {delta['delta']['latency_sec_p95']:.4f}s > "
                f"allowed {args.max_delta_latency_p95:.4f}s"
            )
    
    return len(violations) == 0, violations


def main():
    ap = argparse.ArgumentParser(
        description="Compare two RAG evaluation modes and emit delta reports"
    )
    
    # Script configuration
    ap.add_argument("--eval-script", default="scripts/eval_rag_hit_support.py",
                    help="Path to evaluation script")
    
    # Comparison modes
    ap.add_argument("--baseline-mode", default="bm25", 
                    choices=["bm25", "nearText", "hybrid"],
                    help="Baseline retrieval mode")
    ap.add_argument("--treatment-mode", default="nearText",
                    choices=["bm25", "nearText", "hybrid"],
                    help="Treatment retrieval mode to compare against baseline")
    
    # Weaviate configuration
    ap.add_argument("--weaviate-url", default=os.getenv("WEAVIATE_URL", "http://127.0.0.1:8080"),
                    help="Weaviate endpoint")
    ap.add_argument("--clazz", default="DocsV2",
                    help="Weaviate class name")
    ap.add_argument("--auth-bearer", default=os.getenv("WEAVIATE_BEARER", ""),
                    help="Bearer token for Weaviate auth")
    
    # Evaluation parameters
    ap.add_argument("--seed", required=True,
                    help="Path to seed file (JSONL or CSV)")
    ap.add_argument("--k", type=int, default=5,
                    help="Top-k for hit@k and MRR@k")
    ap.add_argument("--support-k", type=int, default=3,
                    help="Top-k for support@k")
    ap.add_argument("--id-field", default="doc_id",
                    help="Document ID field name")
    
    # Quality gate thresholds (for underlying evaluations)
    ap.add_argument("--expect-hit", type=float, default=0.97,
                    help="Expected hit@k threshold")
    ap.add_argument("--expect-support", type=float, default=0.95,
                    help="Expected support@k threshold")
    
    # Delta gates (optional minimum improvements)
    ap.add_argument("--min-delta-hit", type=float, default=None,
                    help="Minimum required improvement in hit@k (e.g., 0.01 = +1%%)")
    ap.add_argument("--min-delta-support", type=float, default=None,
                    help="Minimum required improvement in support@k")
    ap.add_argument("--min-delta-mrr", type=float, default=None,
                    help="Minimum required improvement in mrr@k")
    ap.add_argument("--max-delta-latency-p95", type=float, default=None,
                    help="Maximum allowed increase in p95 latency (seconds)")
    ap.add_argument("--fail-on-delta-gates", action="store_true",
                    help="Exit with error if delta gates not met")
    
    # Output configuration
    ap.add_argument("--out-json", default=None,
                    help="Output JSON path (default: artifacts/delta_*.json)")
    ap.add_argument("--out-md", default=None,
                    help="Output Markdown path (default: artifacts/delta_*.md)")
    
    args = ap.parse_args()
    
    # Setup
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = "artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Report paths for individual evaluations
    base_rpt = os.path.join(artifacts_dir, f"eval_{args.baseline_mode}_{ts}.json")
    treat_rpt = os.path.join(artifacts_dir, f"eval_{args.treatment_mode}_{ts}.json")
    
    # Common arguments for both evaluations
    common = [
        "--weaviate-url", args.weaviate_url,
        "--class", args.clazz,
        "--seed", args.seed,
        "--k", str(args.k),
        "--support-k", str(args.support_k),
        "--expect-hit", str(args.expect_hit),
        "--expect-support", str(args.expect_support),
        "--id-field", args.id_field,
    ]
    if args.auth_bearer:
        common += ["--auth-bearer", args.auth_bearer]
    
    # Run both evaluations
    print(f"\n📊 RAG Delta Report: {args.baseline_mode} → {args.treatment_mode}", file=sys.stderr)
    print(f"⏰ Timestamp: {ts} UTC\n", file=sys.stderr)
    
    base, base_rc = run_eval(args.eval_script, common, args.baseline_mode, base_rpt)
    treat, treat_rc = run_eval(args.eval_script, common, args.treatment_mode, treat_rpt)
    
    print(f"\n✅ Both evaluations completed", file=sys.stderr)
    
    # Helper to safely extract numeric values
    def get(d: dict, key: str) -> float:
        return float(d.get(key, 0))
    
    # Compute delta
    delta = {
        "timestamp": ts,
        "class": args.clazz,
        "seed_file": args.seed,
        "seed_count": int(treat.get("total_queries", 0)),
        "baseline_mode": args.baseline_mode,
        "treatment_mode": args.treatment_mode,
        "baseline": {
            "hit@k": get(base, "hit@k"),
            "support@k": get(base, "support@k"),
            "mrr@k": get(base, "mrr@k"),
            "latency_sec_p50": get(base, "latency_sec_p50"),
            "latency_sec_p95": get(base, "latency_sec_p95"),
            "passed": bool(base.get("passed", False))
        },
        "treatment": {
            "hit@k": get(treat, "hit@k"),
            "support@k": get(treat, "support@k"),
            "mrr@k": get(treat, "mrr@k"),
            "latency_sec_p50": get(treat, "latency_sec_p50"),
            "latency_sec_p95": get(treat, "latency_sec_p95"),
            "passed": bool(treat.get("passed", False))
        },
        "delta": {
            "hit@k": round(get(treat, "hit@k") - get(base, "hit@k"), 4),
            "support@k": round(get(treat, "support@k") - get(base, "support@k"), 4),
            "mrr@k": round(get(treat, "mrr@k") - get(base, "mrr@k"), 4),
            "latency_sec_p50": round(get(treat, "latency_sec_p50") - get(base, "latency_sec_p50"), 4),
            "latency_sec_p95": round(get(treat, "latency_sec_p95") - get(base, "latency_sec_p95"), 4),
        }
    }
    
    # Check delta gates if requested
    delta_gates_passed = True
    delta_violations = []
    if args.fail_on_delta_gates:
        delta_gates_passed, delta_violations = check_delta_gates(delta, args)
        delta["delta_gates"] = {
            "passed": delta_gates_passed,
            "violations": delta_violations
        }
    
    # Write JSON report
    out_json = args.out_json or os.path.join(
        artifacts_dir, 
        f"delta_{args.baseline_mode}_vs_{args.treatment_mode}_{ts}.json"
    )
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(delta, f, indent=2)
    
    # Build Markdown summary
    md = []
    md.append(f"## RAG Delta Report ({args.baseline_mode} → {args.treatment_mode})\n")
    md.append(f"**Timestamp:** {ts} UTC  ")
    md.append(f"**Class:** `{args.clazz}` • **Seed:** `{args.seed}` • **N={delta['seed_count']}**\n")
    md.append("")
    md.append("| Metric | Baseline | Treatment | Δ |")
    md.append("|---|---:|---:|---:|")
    
    def row(label: str, key: str, pct_fmt: bool = False):
        b = delta["baseline"][key]
        t = delta["treatment"][key]
        d = delta["delta"][key]
        if pct_fmt:
            md.append(f"| {label} | {pct(b)}% | {pct(t)}% | {('+' if d >= 0 else '')}{pct(d)}% |")
        else:
            md.append(f"| {label} | {b:.4f} | {t:.4f} | {('+' if d >= 0 else '')}{d:.4f} |")
    
    row("hit@k", "hit@k", True)
    row("support@k", "support@k", True)
    row("mrr@k", "mrr@k", False)
    row("latency p50 (s)", "latency_sec_p50", False)
    row("latency p95 (s)", "latency_sec_p95", False)
    
    md.append("")
    md.append(f"**Baseline passed gates:** {delta['baseline']['passed']}  ")
    md.append(f"**Treatment passed gates:** {delta['treatment']['passed']}  ")
    
    if args.fail_on_delta_gates:
        md.append("")
        if delta_gates_passed:
            md.append("**✅ Delta improvement gates: PASSED**")
        else:
            md.append("**❌ Delta improvement gates: FAILED**")
            md.append("")
            md.append("**Violations:**")
            for v in delta_violations:
                md.append(f"- {v}")
    
    md_text = "\n".join(md)
    
    # Write Markdown report
    out_md = args.out_md or os.path.join(
        artifacts_dir,
        f"delta_{args.baseline_mode}_vs_{args.treatment_mode}_{ts}.md"
    )
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_text)
    
    # Print to console
    print("\n" + "="*70)
    print(json.dumps(delta, indent=2))
    print("\n" + "="*70)
    print(md_text)
    print("="*70 + "\n")
    
    print(f"📄 JSON report: {out_json}", file=sys.stderr)
    print(f"📄 Markdown report: {out_md}", file=sys.stderr)
    
    # Exit with appropriate code
    if args.fail_on_delta_gates and not delta_gates_passed:
        print("\n❌ Delta improvement gates not met!", file=sys.stderr)
        sys.exit(1)
    
    print("\n✅ Delta report generated successfully", file=sys.stderr)


if __name__ == "__main__":
    main()
