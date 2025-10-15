#!/usr/bin/env python3
"""
Automated Incident Review System for Governance Rollbacks

When a rollback occurs, automatically creates a GitHub Issue or PR with:
- Full decision trace and metrics
- Grafana dashboard links with time ranges
- Audit log references
- Blameless postmortem template
- Root cause analysis framework

Usage:
  python3 scripts/gov_incident_reporter.py --rollback-reason "ECE spike" --metrics-file /tmp/metrics.json

Environment Variables:
  GITHUB_TOKEN: GitHub personal access token
  GITHUB_REPO: owner/repo (e.g., myorg/myrepo)
  GRAFANA_URL: Base Grafana URL for dashboard links
"""
import os, sys, json, time, requests
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")
GRAFANA_URL = os.getenv("GRAFANA_URL", "https://grafana.example.com")

def create_github_issue(title, body, labels=None):
    """Create a GitHub issue for the incident"""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set, cannot create issue")
        return None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "title": title,
        "body": body,
        "labels": labels or ["governance-incident", "rollback", "investigation-needed"]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        issue = response.json()
        print(f"✅ Created GitHub issue: {issue['html_url']}")
        return issue
    except Exception as e:
        print(f"❌ Failed to create GitHub issue: {e}")
        return None

def generate_grafana_links(rollback_time, window_minutes=15):
    """Generate Grafana dashboard links with appropriate time ranges"""
    # Convert to Grafana's time format (Unix timestamp in milliseconds)
    rollback_ts = int(rollback_time * 1000)
    window_start = rollback_ts - (window_minutes * 60 * 1000)
    window_end = rollback_ts + (5 * 60 * 1000)  # 5 minutes after rollback

    base_params = f"from={window_start}&to={window_end}"

    links = {
        "governance_overview": f"{GRAFANA_URL}/d/governance-overview?{base_params}",
        "canary_metrics": f"{GRAFANA_URL}/d/canary-analysis?{base_params}&var-service=all",
        "ece_trends": f"{GRAFANA_URL}/d/ece-monitoring?{base_params}",
        "violation_patterns": f"{GRAFANA_URL}/d/violation-dashboard?{base_params}"
    }

    return links

def get_recent_audit_log(rollback_time, hours_before=2):
    """Extract relevant audit log entries around the rollback"""
    try:
        with open("logs/canary_decisions.log", "r") as f:
            lines = f.readlines()

        # Find entries within time window
        relevant_lines = []
        for line in lines:
            if " - DECISION:" in line:
                # Extract timestamp
                timestamp_str = line.split(" - ")[0]
                try:
                    entry_time = time.mktime(time.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y"))
                    if abs(entry_time - rollback_time) < (hours_before * 3600):
                        relevant_lines.append(line.strip())
                except:
                    continue

        return relevant_lines[-10:]  # Last 10 relevant entries
    except Exception as e:
        return [f"Error reading audit log: {e}"]

def generate_incident_report(rollback_reason, metrics, rollback_time):
    """Generate comprehensive incident report"""

    grafana_links = generate_grafana_links(rollback_time)
    audit_entries = get_recent_audit_log(rollback_time)

    # Format metrics for readability
    metrics_formatted = json.dumps(metrics, indent=2)

    # Calculate time window for investigation
    window_start = time.ctime(rollback_time - (15 * 60))  # 15 minutes before
    window_end = time.ctime(rollback_time + (5 * 60))     # 5 minutes after

    report = f"""# 🚨 Governance Rollback Incident

**Incident Time**: {time.ctime(rollback_time)}
**Rollback Reason**: {rollback_reason}
**Investigation Window**: {window_start} → {window_end}

## 🎯 Incident Summary

**What Happened**: Governance system detected {rollback_reason} and automatically triggered rollback to maintain system stability.

**Impact**: Canary deployment was rolled back to previous stable version.

**Detection**: Automated governance monitoring and canary analysis.

## 📊 Key Metrics at Time of Rollback

```json
{metrics_formatted}
```

## 🔍 Investigation Resources

### Grafana Dashboards (Investigation Window)
- [**Governance Overview**]({grafana_links['governance_overview']}) - System-wide governance metrics
- [**Canary Analysis**]({grafana_links['canary_metrics']}) - Detailed canary performance
- [**ECE Monitoring**]({grafana_links['ece_trends']}) - Evolutionary computation efficiency trends
- [**Violation Patterns**]({grafana_links['violation_patterns']}) - Policy violation analysis

### Audit Trail
```
{chr(10).join(audit_entries)}
```

## 🧾 Blameless Postmortem Template

### Timeline
- **Detection Time**: {time.ctime(rollback_time)}
- **Rollback Execution**: Automatic (via governance-orchestrator)
- **Investigation Start**: [TBD]
- **Resolution Time**: [TBD]

### What Went Wrong?
- [ ] Threshold exceeded: {rollback_reason}
- [ ] Unexpected system behavior
- [ ] Configuration issue
- [ ] External dependency issue
- [ ] Monitoring gap
- [ ] Other: __________

### Why Did It Go Wrong?
- [ ] Inadequate threshold calibration
- [ ] System behavior change not anticipated
- [ ] Monitoring blind spot
- [ ] Process gap
- [ ] External factor
- [ ] Other: __________

### What Did We Learn?
- [ ] Threshold adjustment needed
- [ ] Monitoring improvement required
- [ ] Process change recommended
- [ ] System behavior better understood
- [ ] Other: __________

### Action Items
- [ ] Adjust governance thresholds
- [ ] Update monitoring configuration
- [ ] Improve alerting rules
- [ ] Update runbooks/documentation
- [ ] Training/knowledge sharing
- [ ] Other: __________

### Prevention Measures
- [ ] Threshold tuning based on this incident
- [ ] Additional monitoring/alerts
- [ ] Process improvements
- [ ] System hardening
- [ ] Other: __________

## 🔧 Root Cause Analysis

### Immediate Cause
The rollback was triggered by: **{rollback_reason}**

### Contributing Factors
- [ ] Recent system changes
- [ ] Configuration updates
- [ ] Traffic pattern changes
- [ ] External service issues
- [ ] Resource constraints
- [ ] Other: __________

### Systemic Issues
- [ ] Governance threshold too sensitive/conservative
- [ ] Insufficient monitoring coverage
- [ ] Process gaps in deployment pipeline
- [ ] Inadequate testing coverage
- [ ] Other: __________

## 📈 Follow-up Actions

### Immediate (Next 24 hours)
- [ ] Complete root cause analysis
- [ ] Implement temporary mitigations
- [ ] Update incident response procedures

### Short-term (Next Week)
- [ ] Implement permanent fixes
- [ ] Update governance thresholds
- [ ] Improve monitoring/alerting

### Long-term (Next Month)
- [ ] Process improvements
- [ ] System hardening
- [ ] Training and documentation

## 👥 Stakeholders

**Primary**: Governance Team, Platform Engineering
**Secondary**: Development Teams, SRE, Product
**Communication**: Slack (#governance-incidents), Email distribution

---

*This incident was automatically generated by the Governance Control Plane at {time.ctime()}*
"""

    return report

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Governance Incident Reporter")
    parser.add_argument("--rollback-reason", required=True,
                       help="Reason for the rollback (e.g., 'ECE spike', 'violation rate')")
    parser.add_argument("--metrics-file",
                       help="JSON file containing metrics at time of rollback")
    parser.add_argument("--rollback-time",
                       help="Unix timestamp of rollback (default: now)")
    parser.add_argument("--create-issue", action="store_true",
                       help="Actually create GitHub issue (default: dry run)")

    args = parser.parse_args()

    # Load metrics
    if args.metrics_file:
        try:
            with open(args.metrics_file, "r") as f:
                metrics = json.load(f)
        except:
            metrics = {"error": "Could not load metrics file"}
    else:
        metrics = {"note": "No metrics file provided"}

    # Determine rollback time
    rollback_time = float(args.rollback_time) if args.rollback_time else time.time()

    # Generate report
    report = generate_incident_report(args.rollback_reason, metrics, rollback_time)

    # Create issue title
    title = f"🚨 Governance Rollback: {args.rollback_reason} - {time.ctime(rollback_time)}"

    print("📋 Generated Incident Report:")
    print("=" * 50)
    print(report)
    print("=" * 50)

    if args.create_issue:
        print("🛠️  Creating GitHub issue...")
        issue = create_github_issue(title, report)
        if issue:
            print(f"✅ Issue created: {issue['html_url']}")
        else:
            print("❌ Failed to create issue")
            sys.exit(1)
    else:
        print("📝 Dry run - use --create-issue to actually create the GitHub issue")

if __name__ == "__main__":
    main()
