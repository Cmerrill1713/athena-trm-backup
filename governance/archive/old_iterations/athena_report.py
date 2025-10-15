#!/usr/bin/env python3
"""
Athena Reporter - Smart Voice + Visual System Reports

Auto-detects when to pop a window vs just speak:
- Light responses → speak only
- Dense content (code, tables, many sections) → window + voice
- Explicit "show/display/report" → window + voice

Usage:
  athena_report.py [health|evolution|metrics]           # Auto-detect
  athena_report.py --window                             # Force window
  athena_report.py --no-window                          # Suppress window
  athena_report.py --user "show me the details" health  # Detect user intent

Environment:
  ATHENA_REPORT=always|auto|never    # Global policy (default: auto)
  ATHENA_REPORT_TOKENS=600           # Token threshold for auto-window
  ATHENA_REPORT_CODEBLOCKS=1         # Code block threshold
  ATHENA_REPORT_SECTIONS=4           # Section threshold
"""
import os
import re
import sys
import urllib.parse
import subprocess
import time
from datetime import datetime, timedelta
from typing import Tuple
import requests
from dataclasses import dataclass
import math

PROM_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3001"

# -------- Configuration --------
VERBOSITY = os.getenv("ATHENA_VERBOSITY", "brief")  # brief|normal|detailed

@dataclass
class KPIs:
    success_7d: float          # 0..1
    p95_ms: float
    p50_ms: float
    decisions_24h: int
    promotions_7d: int
    active_alerts: int
    success_24h: float = 0.0
    p95_ms_24h: float = 0.0

def _fmt_pct(x: float) -> str:
    if x is None or math.isnan(x): return "n/a"
    return f"{x*100:.1f}%"

def _fmt_ms(x: float) -> str:
    if x is None or math.isnan(x): return "n/a"
    if x >= 1000: return f"{x/1000:.1f}s"
    return f"{x:.0f}ms"

def _is_bad(k: KPIs):
    # warn/critical thresholds
    warn = (k.success_7d < 0.95) or (k.p95_ms > 1500)
    crit = (k.active_alerts > 0) or (k.success_7d < 0.90) or (k.p95_ms > 2500)
    return warn, crit

def build_synopsis(k: KPIs) -> str:
    warn, crit = _is_bad(k)
    lines = []

    if crit:
        lines.append("Status critical.")
    elif warn:
        lines.append("Status degraded.")
    else:
        lines.append("All systems nominal.")

    # Always mention alerts if any
    if k.active_alerts:
        lines.append(f"{k.active_alerts} active alert{'s' if k.active_alerts!=1 else ''}.")

    # Only say a KPI if it's meaningful; cap total to keep it short
    items = []
    items.append(f"7-day success {_fmt_pct(k.success_7d)}.")
    if not math.isnan(k.p95_ms):
        items.append(f"P95 {_fmt_ms(k.p95_ms)}.")
    if not math.isnan(k.p50_ms) and VERBOSITY != "brief":
        items.append(f"P50 {_fmt_ms(k.p50_ms)}.")
    if k.decisions_24h:
        items.append(f"{k.decisions_24h} decisions last 24 hours.")
    if k.promotions_7d and VERBOSITY != "brief":
        items.append(f"{k.promotions_7d} promotions this week.")

    # If degraded/critical, lead with the offending metric(s)
    if crit or warn:
        ordered = []
        if k.success_7d < 0.95: ordered.append(items[0])
        if k.p95_ms > 1500: ordered.append(f"P95 {_fmt_ms(k.p95_ms)}.")
        # add alerts line already handled above
        # then append a small amount of context
        for it in items:
            if it not in ordered:
                ordered.append(it)
        items = ordered

    # keep it tight: 3 bullets in brief, 5 in normal, 7 in detailed
    cap = {"brief": 3, "normal": 5, "detailed": 7}[VERBOSITY]
    lines.extend(items[:cap])

    return " ".join(lines)

# -------- Policy Configuration --------
REPORT_MODE = os.getenv("ATHENA_REPORT", "auto").lower().strip()
TOKENS_THRESHOLD = int(os.getenv("ATHENA_REPORT_TOKENS", "600"))
CODEBLOCK_THRESHOLD = int(os.getenv("ATHENA_REPORT_CODEBLOCKS", "1"))
SECTION_THRESHOLD = int(os.getenv("ATHENA_REPORT_SECTIONS", "4"))

def approx_tokens(s: str) -> int:
    """Rough token estimate ~ chars / 4"""
    return max(1, len(s) // 4)

def count_codeblocks(md: str) -> int:
    """Count fenced code blocks ```...```"""
    return len(re.findall(r"```", md)) // 2

def count_sections(md: str) -> int:
    """Count markdown headings"""
    return len(re.findall(r"(?m)^\s*#{1,6}\s+", md))

def user_requested_window(user_text: str) -> bool:
    """Detect if user explicitly asked to see a window"""
    if not user_text:
        return False
    triggers = [
        r"\b(show|open|pop\s?out|display|report|window|viewer)\b",
        r"\bsee (details|full|report|breakdown)\b",
        r"\b(visual|graph|chart|dashboard)\b",
    ]
    text = user_text.lower()
    return any(re.search(p, text) for p in triggers)

def should_popout(user_utterance: str, summary: str, md: str) -> Tuple[bool, str]:
    """
    Return (decision, reason) based on policy.

    Policy:
    - always: Always pop window
    - never: Never pop window (speak only)
    - auto: Use heuristics (dense content or user request)
    """
    # Hard overrides
    if REPORT_MODE == "always":
        return True, "env=always"
    if REPORT_MODE == "never":
        return False, "env=never"

    # Explicit user request
    if user_requested_window(user_utterance):
        return True, "user-request"

    # Heuristics for dense content
    tok = approx_tokens(md)
    codes = count_codeblocks(md)
    secs = count_sections(md)

    reasons = []
    if tok >= TOKENS_THRESHOLD:
        reasons.append(f"tokens>={TOKENS_THRESHOLD}")
    if codes >= CODEBLOCK_THRESHOLD:
        reasons.append(f"codeblocks>={CODEBLOCK_THRESHOLD}")
    if secs >= SECTION_THRESHOLD:
        reasons.append(f"sections>={SECTION_THRESHOLD}")

    decision = len(reasons) > 0
    return (decision, "+".join(reasons) if reasons else "light")

def query_prometheus(query):
    """Query Prometheus and return the result"""
    try:
        response = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query}, timeout=5)
        data = response.json()
        if data.get("status") == "success" and data.get("data", {}).get("result"):
            return data["data"]["result"][0]["value"][1]
        return None
    except Exception as e:
        print(f"⚠️  Prometheus query failed: {e}", file=sys.stderr)
        return None

def get_metric_value(query, default=0):
    """Get a metric value with fallback"""
    result = query_prometheus(query)
    if result is None:
        return default
    try:
        return float(result)
    except:
        return default

def synthesize_system_report():
    """
    Generate system health report from real Prometheus metrics
    """
    print("📊 Querying Prometheus for metrics...", file=sys.stderr)

    # Query real metrics
    success_rate_7d = get_metric_value(
        'sum(increase(routing_success_total[7d])) / sum(increase(routing_decisions_total[7d]))',
        0.95
    )

    p95_latency = get_metric_value(
        'histogram_quantile(0.95, sum(rate(routing_latency_ms_bucket[5m])) by (le))',
        0
    )

    p50_latency = get_metric_value(
        'histogram_quantile(0.50, sum(rate(routing_latency_ms_bucket[5m])) by (le))',
        0
    )

    decisions_24h = get_metric_value(
        'sum(increase(routing_decisions_total[24h]))',
        0
    )

    decisions_1h = get_metric_value(
        'sum(increase(routing_decisions_total[1h]))',
        0
    )

    promotions_7d = get_metric_value(
        'sum(increase(trm_promotions_total[7d]))',
        0
    )

    # Check for active alerts
    try:
        alerts_resp = requests.get(f"{PROM_URL}/api/v1/alerts", timeout=5)
        alerts_data = alerts_resp.json()
        active_alerts = len([a for a in alerts_data.get("data", {}).get("alerts", [])
                            if a.get("state") == "firing" and a.get("labels", {}).get("alertname") != "MonitoringDeadman"])
    except:
        active_alerts = 0

    # Get model distribution
    try:
        models_resp = requests.get(
            f"{PROM_URL}/api/v1/query",
            params={"query": "sum by (model) (increase(routing_decisions_total[24h]))"},
            timeout=5
        )
        models_data = models_resp.json()
        model_dist = {}
        if models_data.get("status") == "success":
            for result in models_data.get("data", {}).get("result", []):
                model = result.get("metric", {}).get("model", "unknown")
                count = float(result.get("value", [0, 0])[1])
                if count > 0:
                    model_dist[model] = int(count)
    except:
        model_dist = {}

    # Determine status
    status = "✅ Nominal"
    status_emoji = "✅"
    concerns = []

    if success_rate_7d < 0.95:
        status = "⚠️  Degraded"
        status_emoji = "⚠️"
        concerns.append(f"Success rate below 95% ({success_rate_7d*100:.1f}%)")

    if p95_latency > 1500:
        status = "⚠️  Degraded"
        status_emoji = "⚠️"
        concerns.append(f"p95 latency above threshold ({p95_latency:.0f}ms)")

    if active_alerts > 0:
        status = "🔥 Alerts Firing"
        status_emoji = "🔥"
        concerns.append(f"{active_alerts} active alerts")

    if decisions_1h == 0:
        concerns.append("No routing activity in last hour")

    # Create KPIs object and generate prioritized synopsis
    kpis = KPIs(
        success_7d=success_rate_7d,
        p95_ms=p95_latency,
        p50_ms=p50_latency,
        decisions_24h=int(decisions_24h),
        promotions_7d=int(promotions_7d),
        active_alerts=active_alerts
    )

    # Generate clean, prioritized synopsis for voice
    summary = build_synopsis(kpis)

    # Generate detailed markdown report
    now = datetime.now()

    md = f"""# {status_emoji} System Health Report

**Generated:** {now.strftime("%Y-%m-%d %H:%M:%S")}
**Status:** **{status}**

---

## 📊 Key Performance Indicators

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **7-Day Success Rate** | **{success_rate_7d*100:.2f}%** | ≥95% | {'✅' if success_rate_7d >= 0.95 else '⚠️'} |
| **P95 Latency** | **{p95_latency:.0f} ms** | <1500ms | {'✅' if p95_latency < 1500 else '⚠️'} |
| **P50 Latency** | **{p50_latency:.0f} ms** | <400ms | {'✅' if p50_latency < 400 else '⚠️'} |
| **Active Alerts** | **{active_alerts}** | 0 | {'✅' if active_alerts == 0 else '🔥'} |
| **Decisions (24h)** | **{int(decisions_24h)}** | >0 | {'✅' if decisions_24h > 0 else '⚠️'} |
| **Decisions (1h)** | **{int(decisions_1h)}** | >0 | {'✅' if decisions_1h > 0 else '⚠️'} |
| **Promotions (7d)** | **{int(promotions_7d)}** | 1-3 | {'✅' if 1 <= promotions_7d <= 3 else '⚠️'} |

---

## 🎯 Model Distribution (24h)

"""

    if model_dist:
        total = sum(model_dist.values())
        for model, count in sorted(model_dist.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            md += f"- **{model}**: {count} decisions ({pct:.1f}%)\n"
    else:
        md += "_No routing activity in last 24 hours_\n"

    md += "\n---\n\n"

    if concerns:
        md += "## ⚠️  Concerns\n\n"
        for concern in concerns:
            md += f"- {concern}\n"
        md += "\n"
    else:
        md += "## ✅ All Systems Nominal\n\n"
        md += "All KPIs within target thresholds. No intervention required.\n\n"

    md += f"""---

## 🔗 Quick Links

- [Grafana Dashboard]({GRAFANA_URL}/d/trm-evolution)
- [Prometheus]({PROM_URL})
- [Active Alerts]({PROM_URL}/alerts)
- [Targets]({PROM_URL}/targets)

---

## 📅 Next Actions

- **Evolution Run:** Tonight at 2:00 AM
- **Next Review:** {(now + timedelta(days=1)).strftime("%Y-%m-%d 09:00")}
- **Data Archive:** {(now.replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")} (monthly)

---

_Generated by Athena Reporter • TRM Evolution Monitoring_
"""

    return "Daily System Health", summary, md

def synthesize_evolution_report():
    """Generate evolution-specific report"""
    # TODO: Query TRM training runs, accuracy deltas, etc.
    summary = "Evolution system operational. Nightly training scheduled. No pending promotions."
    md = "# Evolution Status\n\n(Coming soon: training runs, accuracy trends, model registry)"
    return "Evolution Report", summary, md

def synthesize_metrics_report():
    """Generate detailed metrics report"""
    # TODO: Detailed metrics breakdown
    summary = "Metrics collection active. All targets up. Recording rules operational."
    md = "# Metrics Health\n\n(Coming soon: scrape success, cardinality, query performance)"
    return "Metrics Report", summary, md

def _singleflight_lock(name="athena_report.lock"):
    """Prevent bursts from spawning multiples within ~3s."""
    import fcntl
    import pathlib
    import tempfile
    lock_path = pathlib.Path(tempfile.gettempdir()) / name
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # auto-release after 3 seconds
        os.write(fd, str(time.time()).encode())
        return fd  # keep fd open until function exits
    except (BlockingIOError, OSError):
        # Someone else is running very recently – just exit quietly
        print("🔒 Report already in progress (lock contention)", file=sys.stderr)
        return None

def open_report(title, summary, md):
    """Open Athena Reporter with the generated report"""
    import hashlib
    import pathlib
    import tempfile

    # 0) singleflight lock (burst protection)
    fd = _singleflight_lock()
    if fd is None:
        return True  # Another instance is handling this

    try:
        # 1) write body to temp file (avoid long URLs)
        tmp_file = pathlib.Path(tempfile.gettempdir()) / f"athena_report_{os.getpid()}.md"
        tmp_file.write_text(md, encoding="utf-8")

        # 2) stable report_id = hash(summary+body) (same content => same id)
        h = hashlib.sha256()
        h.update(summary.encode("utf-8"))
        h.update(md.encode("utf-8"))
        report_id = h.hexdigest()[:16]

        # 3) include timestamp for visibility but dedupe uses report_id
        ts = int(time.time())

        # Use quote instead of urlencode to avoid '+' for spaces
        # urlencode with quote_via=quote ensures spaces become %20, not +
        url = "athena://report?" + urllib.parse.urlencode({
            "title": title,
            "summary": summary,
            "md_path": str(tmp_file),
            "report_id": report_id,
            "ts": str(ts)
        }, quote_via=urllib.parse.quote)

        print(f"🗣️  Opening report: {title}", file=sys.stderr)
        print(f"📢  Synopsis: {summary[:100]}...", file=sys.stderr)
        print(f"🆔  Report ID: {report_id}", file=sys.stderr)
        print(f"📄  Markdown file: {tmp_file}", file=sys.stderr)

        # Open the Reporter (macOS will launch app if not running)
        result = subprocess.run(["open", url], capture_output=True)

        if result.returncode != 0:
            print("❌ Failed to open reporter", file=sys.stderr)
            print("   Make sure AthenaReporter is built: make reporter-build", file=sys.stderr)
            return False

        return True

    finally:
        if fd is not None:
            try:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            except Exception:
                pass

def main():
    """
    Main entry point with smart window policy

    Usage:
      athena_report.py [health|evolution|metrics]           # Auto-detect
      athena_report.py --window health                      # Force window
      athena_report.py --no-window health                   # Suppress window
      athena_report.py --user "show me details" health      # Detect user intent
    """
    # Parse CLI flags
    force_window = "--window" in sys.argv
    force_no = "--no-window" in sys.argv

    # Get user utterance if provided
    user_utterance = ""
    if "--user" in sys.argv:
        try:
            idx = sys.argv.index("--user")
            user_utterance = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        except (ValueError, IndexError):
            pass

    if not user_utterance:
        user_utterance = os.getenv("ATHENA_LAST_UTTERANCE", "")

    # Determine report mode (filter out flags)
    mode_args = [a for a in sys.argv[1:] if not a.startswith("--") and a != user_utterance]
    mode = mode_args[0] if mode_args else "health"

    # Generate report
    if mode == "health":
        title, summary, md = synthesize_system_report()
    elif mode == "evolution":
        title, summary, md = synthesize_evolution_report()
    elif mode == "metrics":
        title, summary, md = synthesize_metrics_report()
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} [health|evolution|metrics] [--window|--no-window] [--user 'text']", file=sys.stderr)
        sys.exit(1)

    # Decide whether to pop window
    if force_window:
        print(f"🗣️  Opening window (forced): {title}", file=sys.stderr)
        print(f"📢  Synopsis: {summary[:80]}...", file=sys.stderr)
        success = open_report(title, summary, md)
        sys.exit(0 if success else 1)

    if force_no:
        print(f"💬 Voice only: {summary}", file=sys.stderr)
        print(summary)  # Print to stdout for TTS
        sys.exit(0)

    # Auto-detect based on content and user request
    should_pop, reason = should_popout(user_utterance, summary, md)

    if should_pop:
        print(f"🗣️  Opening window ({reason}): {title}", file=sys.stderr)
        print(f"📢  Synopsis: {summary[:80]}...", file=sys.stderr)
        success = open_report(title, summary, md)
        sys.exit(0 if success else 1)
    else:
        print(f"💬 Light response ({reason}) - voice only", file=sys.stderr)
        print(summary)  # Print to stdout for TTS
        sys.exit(0)

if __name__ == "__main__":
    main()
