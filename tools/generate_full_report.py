#!/usr/bin/env python3
"""
Full Validation Report Generator
=================================
Compiles all validation results into single report
"""

import os
import json
import subprocess
import datetime
import socket


def read_json(path, default=None):
    """Read JSON file with fallback"""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def shell(cmd):
    """Execute shell command and return output"""
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def fmtn(n):
    """Format number with commas"""
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def main():
    # Load data
    inv = read_json("./state/code_inventory.json", {})
    tel = read_json("./state/telemetry_stats.json", {})
    eval_summarize = read_json("./orchestrator/state/eval.summarize.json", {})
    eval_plan = read_json("./orchestrator/state/eval.plan.json", {})

    # Git info
    repo = shell("git rev-parse --show-toplevel") if os.path.exists(".git") else os.getcwd()
    branch = shell("git rev-parse --abbrev-ref HEAD") if os.path.exists(".git") else "unknown"
    rev = shell("git rev-parse --short HEAD") if os.path.exists(".git") else "unknown"
    host = socket.gethostname()
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Extract data
    grand = inv.get("grand_total", {})
    by_comp = inv.get("components", [])

    # Build report
    lines = []
    lines.append("# NeuroForge - Full Validation Report\n")
    lines.append(f"**Generated:** {now} on **{host}**  ")
    lines.append(f"**Repo:** `{os.path.basename(repo)}`  ")
    lines.append(f"**Branch:** `{branch}`  ")
    lines.append(f"**Rev:** `{rev}`  \n")
    lines.append("---\n")

    # Code Inventory
    lines.append("## 📊 Code Inventory\n")

    if grand:
        lines.append(f"**Grand Total:**  ")
        lines.append(f"- Files: **{fmtn(grand.get('files', 0))}**  ")
        lines.append(f"- Lines: **{fmtn(grand.get('lines', 0))}**  \n")

        lines.append("**By Language (Top 10):**  ")
        for lang, d in sorted(grand.get("by_lang", {}).items(), key=lambda x: -x[1]["lines"])[:10]:
            lines.append(f"- {lang}: {fmtn(d['lines'])} lines ({fmtn(d['files'])} files)")
    else:
        lines.append("- (No inventory data available)\n")

    # Components
    lines.append("\n## 🧩 Components\n")

    if by_comp:
        for c in sorted(by_comp, key=lambda x: -x["totals"]["lines"])[:10]:
            t = c["totals"]
            name = c["component"]
            rev_str = c.get("git_rev", "—")
            lines.append(f"### {name}")
            lines.append(f"- Files: {fmtn(t['files'])}, Lines: {fmtn(t['lines'])}")
            lines.append(f"- Git: `{rev_str}`")

            # Top 3 languages
            langs = sorted(t["by_lang"].items(), key=lambda x: -x[1]["lines"])[:3]
            if langs:
                lang_str = ", ".join(f"{k} ({fmtn(v['lines'])})" for k, v in langs)
                lines.append(f"- Top: {lang_str}")
            lines.append("")
    else:
        lines.append("- (No components found)\n")

    # Quality Gates
    lines.append("## ✅ Quality Gates\n")

    # Evals
    def eval_section(name, data):
        if not data:
            return f"**{name}:** No data\n"
        passed = data.get("passed", 0)
        total = data.get("total", 0)
        rate = f"{(passed/total*100):.1f}%" if total else "0.0%"
        emoji = "✅" if (passed/total >= 0.80 if total else False) else "❌"
        return f"**{name}:** {emoji} {passed}/{total} ({rate})\n"

    lines.append(eval_section("Golden Eval - Summarize", eval_summarize))
    lines.append(eval_section("Golden Eval - Plan", eval_plan))

    # Telemetry
    lines.append("## 📈 Performance Metrics\n")

    if tel and tel.get("count", 0) > 0:
        lines.append(f"**Traces analyzed:** {fmtn(tel['count'])}  ")
        lines.append(f"**Latency:**  ")
        lines.append(f"- p50: {fmtn(tel.get('p50', 0))}ms  ")
        lines.append(f"- p95: {fmtn(tel.get('p95', 0))}ms {'✅' if tel.get('p95', 9999) <= 1500 else '❌'}  ")
        lines.append(f"- p99: {fmtn(tel.get('p99', 0))}ms  \n")

        if tel.get("by_capability"):
            lines.append("**By Capability:**  ")
            for cap, s in tel["by_capability"].items():
                p95_emoji = "✅" if s.get('p95', 9999) <= 1500 else "❌"
                lines.append(f"- {cap}: p50={fmtn(s.get('p50', 0))}ms, p95={fmtn(s.get('p95', 0))}ms {p95_emoji}, n={fmtn(s.get('count', 0))}")
    else:
        lines.append("- (No telemetry data available)\n")

    # Status
    lines.append("\n## 🎯 Overall Status\n")

    # Determine status
    all_green = True

    # Check evals
    for name, data in [("summarize", eval_summarize), ("plan", eval_plan)]:
        if data:
            passed = data.get("passed", 0)
            total = data.get("total", 1)
            if passed / total < 0.80:
                all_green = False

    # Check p95
    if tel and tel.get("p95", 0) > 1500:
        all_green = False

    if all_green:
        lines.append("**Status:** ✅ **ALL SYSTEMS GREEN**  ")
        lines.append("**Ready to ship!** 🚀\n")
    else:
        lines.append("**Status:** ⚠️ **ISSUES DETECTED**  ")
        lines.append("**Review quality gates before shipping**\n")

    # Footer
    lines.append("---\n")
    lines.append("**Generated by:** `tools/generate_full_report.py`  ")
    lines.append("**Command:** `make full-validate`  \n")

    # Write report
    with open("FULL_VALIDATION_REPORT.md", "w") as f:
        f.write("\n".join(lines))

    print("✅ Full validation report written to FULL_VALIDATION_REPORT.md")


if __name__ == "__main__":
    main()
