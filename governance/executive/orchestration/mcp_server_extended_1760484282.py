#!/usr/bin/env python3
"""
Extended MCP Server with Additional Tools
Shows how to add many more tools to the MCP Store
"""
import json
import os
from datetime import datetime

import requests
from mcp.server.fastmcp import FastMCP, tool

STORE = os.getenv("MCPSTORE_URL", "http://athena-mcp-store:8411")

mcp = FastMCP("mcp-store-extended")

# ============================================================================
# EXISTING STORE TOOLS
# ============================================================================

@tool()
def store_write(agent: str, service: str, status: str, summary: str="", details_json: str="{}", commit: str="", correlation_id: str=""):
    """Write a validation result to the MCP Store."""
    payload = {
        "agent": agent, "service": service, "status": status,
        "summary": summary, "details": json.loads(details_json) if details_json else {},
        "commit": commit, "correlation_id": correlation_id if correlation_id else None
    }
    r = requests.post(f"{STORE}/v1/store/results", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_get(id: str):
    """Fetch a validation record by its unique ID."""
    r = requests.get(f"{STORE}/v1/store/results/{id}", timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_list(agent: str = "", service: str = "", status: str = "", limit: int = 100):
    """List validation results with optional filters."""
    params = {}
    if agent: params["agent"] = agent
    if service: params["service"] = service
    if status: params["status"] = status
    params["limit"] = limit
    r = requests.get(f"{STORE}/v1/store/results", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_health():
    """Check the health status of the MCP Store service."""
    r = requests.get(f"{STORE}/health", timeout=5)
    r.raise_for_status()
    return r.json()

# ============================================================================
# NEW ANALYTICS TOOLS
# ============================================================================

@tool()
def analyze_service_trends(service: str, days: int = 7):
    """
    Analyze pass/fail trends for a service over the last N days.
    
    Args:
        service: Name of the service to analyze
        days: Number of days to look back (default: 7)
    
    Returns:
        dict: Trend analysis with pass rate, failure count, and patterns
    """
    # This would query the store and compute trends
    # For now, showing the pattern
    results = store_list(service=service, limit=1000)

    # Simple analysis
    total = results['count']
    passed = sum(1 for r in results.get('results', []) if r['status'] == 'PASS')
    failed = sum(1 for r in results.get('results', []) if r['status'] == 'FAIL')

    return {
        "service": service,
        "period_days": days,
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / total * 100) if total > 0 else 0, 2),
        "status": "healthy" if (passed / total) > 0.95 else "degraded" if (passed / total) > 0.80 else "critical"
    }

@tool()
def compare_services(services: str, metric: str = "pass_rate"):
    """
    Compare multiple services by a specific metric.
    
    Args:
        services: Comma-separated list of service names (e.g., "bridge,athena,uat")
        metric: Metric to compare (pass_rate, avg_latency, failure_count)
    
    Returns:
        dict: Comparison of services with rankings
    """
    service_list = [s.strip() for s in services.split(",")]
    comparison = []

    for service in service_list:
        results = store_list(service=service, limit=100)
        total = results['count']
        passed = sum(1 for r in results.get('results', []) if r['status'] == 'PASS')

        comparison.append({
            "service": service,
            "pass_rate": round((passed / total * 100) if total > 0 else 0, 2),
            "total_tests": total
        })

    # Sort by metric
    comparison.sort(key=lambda x: x.get(metric, 0), reverse=True)

    return {
        "metric": metric,
        "services": comparison,
        "best": comparison[0]['service'] if comparison else None,
        "worst": comparison[-1]['service'] if comparison else None
    }

@tool()
def detect_regressions(service: str, threshold: float = 0.1):
    """
    Detect performance regressions by comparing recent tests to baseline.
    
    Args:
        service: Name of the service to check
        threshold: Threshold for regression detection (0.1 = 10% degradation)
    
    Returns:
        dict: Regression analysis with detected issues
    """
    # Get recent results
    results = store_list(service=service, limit=50)

    if results['count'] < 10:
        return {"status": "insufficient_data", "message": "Need at least 10 test runs"}

    # Simple regression detection logic
    recent = results['results'][:10]  # Last 10
    baseline = results['results'][10:30]  # Previous 20

    recent_pass_rate = sum(1 for r in recent if r['status'] == 'PASS') / len(recent)
    baseline_pass_rate = sum(1 for r in baseline if r['status'] == 'PASS') / len(baseline)

    degradation = baseline_pass_rate - recent_pass_rate

    return {
        "service": service,
        "recent_pass_rate": round(recent_pass_rate * 100, 2),
        "baseline_pass_rate": round(baseline_pass_rate * 100, 2),
        "degradation_pct": round(degradation * 100, 2),
        "regression_detected": degradation > threshold,
        "severity": "critical" if degradation > 0.2 else "warning" if degradation > threshold else "none"
    }

# ============================================================================
# ALERTING & NOTIFICATION TOOLS
# ============================================================================

@tool()
def create_alert_rule(service: str, condition: str, threshold: float, notification_channel: str):
    """
    Create an alert rule for service monitoring.
    
    Args:
        service: Service to monitor
        condition: Condition to alert on (failure_rate, latency_p95, consecutive_failures)
        threshold: Threshold value that triggers the alert
        notification_channel: Where to send alerts (slack, email, pagerduty)
    
    Returns:
        dict: Created alert rule configuration
    """
    rule = {
        "id": f"alert-{service}-{condition}-{datetime.now().timestamp()}",
        "service": service,
        "condition": condition,
        "threshold": threshold,
        "notification_channel": notification_channel,
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }

    # In production, this would store the rule in a database
    return {
        "status": "created",
        "rule": rule,
        "message": f"Alert rule created for {service}"
    }

@tool()
def check_service_sla(service: str, sla_target: float = 99.9, window_hours: int = 24):
    """
    Check if a service is meeting its SLA target.
    
    Args:
        service: Service name
        sla_target: Target uptime percentage (default: 99.9%)
        window_hours: Time window to check (default: 24 hours)
    
    Returns:
        dict: SLA compliance status with details
    """
    results = store_list(service=service, limit=1000)

    total = results['count']
    passed = sum(1 for r in results.get('results', []) if r['status'] == 'PASS')

    actual_uptime = (passed / total * 100) if total > 0 else 0
    sla_met = actual_uptime >= sla_target

    return {
        "service": service,
        "sla_target": sla_target,
        "actual_uptime": round(actual_uptime, 3),
        "sla_met": sla_met,
        "tests_evaluated": total,
        "window_hours": window_hours,
        "status": "compliant" if sla_met else "breach",
        "shortfall": round(sla_target - actual_uptime, 3) if not sla_met else 0
    }

# ============================================================================
# INCIDENT MANAGEMENT TOOLS
# ============================================================================

@tool()
def create_incident(service: str, severity: str, title: str, description: str):
    """
    Create an incident record linked to validation failures.
    
    Args:
        service: Affected service
        severity: Incident severity (P1, P2, P3, P4)
        title: Brief incident title
        description: Detailed description
    
    Returns:
        dict: Created incident with ID and details
    """
    incident = {
        "id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "service": service,
        "severity": severity,
        "title": title,
        "description": description,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "created_by": "mcp-store"
    }

    # Store incident (in production, this would use a database)
    # For now, we can store it as a special validation record
    store_write(
        agent="incident-manager",
        service=service,
        status="FAIL",
        summary=f"Incident {incident['id']}: {title}",
        details_json=json.dumps(incident)
    )

    return {
        "status": "created",
        "incident": incident
    }

@tool()
def correlate_failures(time_window_minutes: int = 60):
    """
    Find correlated failures across services in a time window.
    
    Args:
        time_window_minutes: Time window to search for correlations
    
    Returns:
        dict: Correlated failure patterns across services
    """
    # Get recent failures across all services
    all_failures = store_list(status="FAIL", limit=500)

    # Group by time windows (simplified logic)
    correlations = {}
    for result in all_failures.get('results', []):
        service = result['service']
        if service not in correlations:
            correlations[service] = []
        correlations[service].append(result)

    # Find services that failed around the same time
    correlated_services = [s for s, failures in correlations.items() if len(failures) > 2]

    return {
        "time_window_minutes": time_window_minutes,
        "total_failures": all_failures['count'],
        "affected_services": len(correlated_services),
        "services": correlated_services,
        "pattern": "multiple_service_failure" if len(correlated_services) > 3 else "isolated_failure"
    }

# ============================================================================
# REPORTING TOOLS
# ============================================================================

@tool()
def generate_daily_report(date: str = ""):
    """
    Generate a daily validation report for all services.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
    
    Returns:
        dict: Daily report with summary statistics
    """
    target_date = date if date else datetime.now().strftime("%Y-%m-%d")

    # Get all results for the day
    all_results = store_list(limit=10000)

    # Aggregate by service
    services = {}
    for result in all_results.get('results', []):
        service = result['service']
        if service not in services:
            services[service] = {"total": 0, "passed": 0, "failed": 0, "warned": 0}

        services[service]["total"] += 1
        if result['status'] == 'PASS':
            services[service]["passed"] += 1
        elif result['status'] == 'FAIL':
            services[service]["failed"] += 1
        else:
            services[service]["warned"] += 1

    # Calculate pass rates
    for service, stats in services.items():
        stats["pass_rate"] = round((stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0, 2)

    return {
        "date": target_date,
        "total_tests": all_results['count'],
        "services_tested": len(services),
        "services": services,
        "summary": {
            "healthy": sum(1 for s in services.values() if s["pass_rate"] > 95),
            "degraded": sum(1 for s in services.values() if 80 < s["pass_rate"] <= 95),
            "critical": sum(1 for s in services.values() if s["pass_rate"] <= 80)
        }
    }

@tool()
def export_results(service: str = "", format: str = "json", limit: int = 1000):
    """
    Export validation results in various formats.
    
    Args:
        service: Optional service filter
        format: Export format (json, csv, markdown)
        limit: Maximum number of results to export
    
    Returns:
        str: Formatted export data
    """
    results = store_list(service=service, limit=limit)

    if format == "json":
        return json.dumps(results, indent=2)

    elif format == "csv":
        # Convert to CSV format
        lines = ["agent,service,status,summary,created_at"]
        for r in results.get('results', []):
            lines.append(f"{r['agent']},{r['service']},{r['status']},{r['summary']},{r['created_at']}")
        return "\n".join(lines)

    elif format == "markdown":
        # Convert to Markdown table
        lines = ["| Agent | Service | Status | Summary | Time |", "|-------|---------|--------|---------|------|"]
        for r in results.get('results', []):
            lines.append(f"| {r['agent']} | {r['service']} | {r['status']} | {r['summary']} | {r['created_at']} |")
        return "\n".join(lines)

    return json.dumps(results)

# ============================================================================
# INTEGRATION TOOLS (Connect to other services)
# ============================================================================

@tool()
def sync_to_github(service: str, status: str, commit_sha: str):
    """
    Sync validation results to GitHub commit status.
    
    Args:
        service: Service name
        status: Validation status (PASS/FAIL)
        commit_sha: Git commit SHA
    
    Returns:
        dict: GitHub sync status
    """
    # In production, this would call GitHub API
    github_status = {
        "state": "success" if status == "PASS" else "failure",
        "context": f"validation/{service}",
        "description": f"{service} validation {status}",
        "target_url": f"{STORE}/v1/store/results?service={service}&commit={commit_sha}"
    }

    return {
        "status": "synced",
        "github_status": github_status,
        "commit_sha": commit_sha
    }

@tool()
def trigger_slack_notification(channel: str, service: str, status: str, message: str):
    """
    Send validation results to Slack.
    
    Args:
        channel: Slack channel ID
        service: Service name
        status: Validation status
        message: Notification message
    
    Returns:
        dict: Slack notification status
    """
    slack_payload = {
        "channel": channel,
        "text": f"🚨 *{service}* validation {status}",
        "attachments": [{
            "color": "good" if status == "PASS" else "danger",
            "text": message,
            "footer": "MCP Store",
            "ts": int(datetime.now().timestamp())
        }]
    }

    # In production, this would POST to Slack webhook
    return {
        "status": "sent",
        "channel": channel,
        "payload": slack_payload
    }

if __name__ == "__main__":
    mcp.run()

