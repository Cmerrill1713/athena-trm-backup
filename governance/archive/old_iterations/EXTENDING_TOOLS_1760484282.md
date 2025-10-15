# Extending MCP Store with Custom Tools

The MCP Store is designed to be infinitely extensible. You can add as many tools as you need!

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  MCP Client (Your Orchestrator, AI Agent, etc)  │
└──────────────────────┬──────────────────────────┘
                       │
                       │ MCP Protocol
                       ▼
┌──────────────────────────────────────────────────┐
│  MCP Server (mcp_server.py or extended version)  │
│                                                   │
│  🔧 Tool 1: store_write                          │
│  🔧 Tool 2: store_get                            │
│  🔧 Tool 3: store_list                           │
│  🔧 Tool 4: analyze_trends                       │
│  🔧 Tool 5: detect_regressions                   │
│  🔧 Tool 6: create_incident                      │
│  🔧 Tool N: YOUR_CUSTOM_TOOL                     │
│                                                   │
└────────┬──────────┬──────────┬───────────────────┘
         │          │          │
         ▼          ▼          ▼
    ┌────────┐  ┌──────┐  ┌──────────┐
    │MCP Store│ │GitHub│  │ Slack    │
    │  API    │ │  API │  │Webhook   │
    └────────┘  └──────┘  └──────────┘
```

## 🚀 We Just Added 15+ New Tools!

I created `mcp_server_extended.py` with these tool categories:

### 📊 Analytics Tools (5 tools)
- `analyze_service_trends` - Pass/fail trends over time
- `compare_services` - Compare multiple services
- `detect_regressions` - Automatic regression detection
- `check_service_sla` - SLA compliance monitoring
- `correlate_failures` - Find correlated failures

### 🚨 Alerting Tools (2 tools)
- `create_alert_rule` - Set up monitoring alerts
- `trigger_slack_notification` - Send Slack notifications

### 🔥 Incident Management (2 tools)
- `create_incident` - Create incident records
- `correlate_failures` - Cross-service failure analysis

### 📝 Reporting Tools (2 tools)
- `generate_daily_report` - Daily validation reports
- `export_results` - Export in JSON/CSV/Markdown

### 🔗 Integration Tools (2 tools)
- `sync_to_github` - GitHub commit status integration
- `trigger_slack_notification` - Slack integration

## 📝 How to Add Your Own Tools

### Step 1: Create a Function

```python
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("my-mcp-server")

@tool()
def my_custom_tool(param1: str, param2: int = 10):
    """
    Description of what this tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 10)
    
    Returns:
        dict: What the tool returns
    """
    # Your implementation here
    result = do_something(param1, param2)
    return {"status": "success", "data": result}
```

### Step 2: Use Any Python Library

```python
@tool()
def analyze_with_pandas(service: str):
    """Analyze service data using pandas."""
    import pandas as pd
    
    # Get data from MCP Store
    results = store_list(service=service, limit=1000)
    
    # Convert to DataFrame
    df = pd.DataFrame(results['results'])
    
    # Analyze
    analysis = {
        "mean_success_rate": df[df['status'] == 'PASS'].shape[0] / len(df),
        "trend": "improving" if df.tail(10)['status'].value_counts().get('PASS', 0) > 7 else "degrading"
    }
    
    return analysis
```

### Step 3: Call External APIs

```python
@tool()
def create_jira_ticket(service: str, summary: str, description: str):
    """Create a Jira ticket from validation failure."""
    import requests
    
    jira_url = os.getenv("JIRA_URL")
    jira_auth = os.getenv("JIRA_TOKEN")
    
    response = requests.post(
        f"{jira_url}/rest/api/2/issue",
        headers={"Authorization": f"Bearer {jira_auth}"},
        json={
            "fields": {
                "project": {"key": "OPS"},
                "summary": f"[{service}] {summary}",
                "description": description,
                "issuetype": {"name": "Bug"}
            }
        }
    )
    
    return {"ticket_id": response.json()['key']}
```

### Step 4: Chain Multiple Tools

```python
@tool()
def auto_investigate_failure(service: str):
    """
    Automatically investigate service failures and create incident if needed.
    """
    # Step 1: Analyze trends
    trends = analyze_service_trends(service, days=7)
    
    # Step 2: Check for regressions
    regression = detect_regressions(service)
    
    # Step 3: If critical, create incident
    if regression['severity'] == 'critical':
        incident = create_incident(
            service=service,
            severity="P1",
            title=f"Performance regression detected",
            description=f"Pass rate dropped by {regression['degradation_pct']}%"
        )
        
        # Step 4: Notify team
        trigger_slack_notification(
            channel="#incidents",
            service=service,
            status="FAIL",
            message=f"Critical regression: {incident['incident']['id']}"
        )
        
        return {"action": "incident_created", "incident": incident}
    
    return {"action": "no_action_needed", "trends": trends}
```

## 🎨 Real-World Tool Examples

### Example 1: Automated Runbook Execution

```python
@tool()
def execute_runbook(service: str, runbook_id: str):
    """
    Execute automated remediation steps from a runbook.
    
    Args:
        service: Service to remediate
        runbook_id: ID of the runbook to execute
    
    Returns:
        dict: Execution results
    """
    runbooks = {
        "restart": lambda: restart_service(service),
        "scale_up": lambda: scale_service(service, replicas=3),
        "rollback": lambda: rollback_deployment(service),
    }
    
    if runbook_id in runbooks:
        result = runbooks[runbook_id]()
        
        # Log the remediation
        store_write(
            agent="auto-remediation",
            service=service,
            status="PASS",
            summary=f"Executed runbook: {runbook_id}",
            details_json=json.dumps({"runbook": runbook_id, "result": result})
        )
        
        return {"status": "executed", "runbook": runbook_id, "result": result}
    
    return {"status": "runbook_not_found"}
```

### Example 2: Cost Analysis

```python
@tool()
def analyze_test_costs(time_period: str = "month"):
    """
    Analyze infrastructure costs related to testing.
    
    Args:
        time_period: Time period (day, week, month)
    
    Returns:
        dict: Cost breakdown and optimization suggestions
    """
    # Get all test runs
    results = store_list(limit=10000)
    
    # Calculate costs (simplified)
    total_tests = results['count']
    compute_cost = total_tests * 0.001  # $0.001 per test
    storage_cost = (total_tests * 1024) / 1000000 * 0.023  # Storage costs
    
    return {
        "period": time_period,
        "total_tests": total_tests,
        "compute_cost_usd": round(compute_cost, 2),
        "storage_cost_usd": round(storage_cost, 2),
        "total_cost_usd": round(compute_cost + storage_cost, 2),
        "optimization_tips": [
            "Consider reducing test frequency for stable services",
            "Archive old test results to cold storage"
        ]
    }
```

### Example 3: ML-Based Failure Prediction

```python
@tool()
def predict_next_failure(service: str):
    """
    Use ML to predict when the next failure might occur.
    
    Args:
        service: Service to analyze
    
    Returns:
        dict: Failure prediction with confidence score
    """
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    
    # Get historical data
    results = store_list(service=service, limit=500)
    
    # Feature engineering (simplified)
    features = []
    labels = []
    
    for i, result in enumerate(results.get('results', [])):
        # Extract features
        hour_of_day = int(result['created_at'][11:13])
        day_of_week = 1  # Parse from timestamp
        
        features.append([hour_of_day, day_of_week])
        labels.append(1 if result['status'] == 'FAIL' else 0)
    
    if len(features) < 50:
        return {"status": "insufficient_data"}
    
    # Train simple model
    X = np.array(features)
    y = np.array(labels)
    
    model = RandomForestClassifier(n_estimators=10)
    model.fit(X, y)
    
    # Predict next 24 hours
    predictions = []
    for hour in range(24):
        prob = model.predict_proba([[hour, datetime.now().weekday()]])[0][1]
        predictions.append({"hour": hour, "failure_probability": round(prob, 3)})
    
    # Find highest risk hour
    highest_risk = max(predictions, key=lambda x: x['failure_probability'])
    
    return {
        "service": service,
        "next_24h_predictions": predictions,
        "highest_risk_hour": highest_risk['hour'],
        "risk_level": "high" if highest_risk['failure_probability'] > 0.5 else "medium"
    }
```

## 🔧 Using the Extended Tools

### Option 1: Update MCP Config

```json
{
  "mcp-store-extended": {
    "command": "python",
    "args": ["services/mcp_store/mcp_server_extended.py"],
    "env": {
      "MCPSTORE_URL": "http://127.0.0.1:8411"
    }
  }
}
```

### Option 2: Call from Your Code

```python
from mcp import Client

mcp = Client()

# Use analytics tool
trends = mcp.call_tool("analyze_service_trends", 
    service="bridge",
    days=7
)

# Detect regressions
regression = mcp.call_tool("detect_regressions",
    service="bridge",
    threshold=0.1
)

# Generate report
report = mcp.call_tool("generate_daily_report")
```

## 📦 Tool Categories You Can Add

### 1. **Observability Tools**
- `trace_request_flow` - Distributed tracing
- `analyze_logs` - Log aggregation and analysis
- `metric_correlation` - Correlate metrics across services
- `anomaly_detection` - Detect anomalies in metrics

### 2. **Security Tools**
- `scan_for_vulnerabilities` - Security scanning
- `check_compliance` - Compliance validation
- `audit_access_logs` - Security audit trails
- `rotate_credentials` - Automated credential rotation

### 3. **Performance Tools**
- `benchmark_service` - Performance benchmarking
- `load_test_runner` - Automated load testing
- `optimize_config` - Configuration optimization
- `capacity_planning` - Capacity analysis

### 4. **Deployment Tools**
- `canary_deployment` - Canary release automation
- `blue_green_switch` - Blue-green deployment
- `rollback_service` - Automated rollbacks
- `version_comparison` - Compare deployments

### 5. **AI/ML Tools**
- `predict_failures` - ML-based failure prediction
- `classify_errors` - Error classification
- `recommend_fixes` - Auto-suggest fixes
- `generate_test_cases` - AI test generation

## 🎯 Best Practices

### 1. **Keep Tools Focused**
Each tool should do ONE thing well:
```python
# ✅ Good - focused tool
@tool()
def restart_service(service: str):
    """Restart a specific service."""
    ...

# ❌ Bad - too many responsibilities
@tool()
def fix_everything(service: str):
    """Restart, scale, and optimize service."""
    ...
```

### 2. **Provide Clear Documentation**
```python
@tool()
def my_tool(param: str):
    """
    One-line summary of what this tool does.
    
    Detailed explanation of the tool's purpose and behavior.
    
    Args:
        param: Clear description with examples (e.g., "bridge", "athena")
    
    Returns:
        dict: Description of return structure
        
    Example:
        >>> my_tool("bridge")
        {"status": "success", "result": {...}}
    """
    ...
```

### 3. **Handle Errors Gracefully**
```python
@tool()
def safe_tool(service: str):
    """Tool with proper error handling."""
    try:
        result = risky_operation(service)
        return {"status": "success", "data": result}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "service": service,
            "suggestion": "Check if service exists"
        }
```

### 4. **Add Validation**
```python
@tool()
def validated_tool(service: str, threshold: float):
    """Tool with input validation."""
    # Validate inputs
    if not service:
        return {"error": "service parameter is required"}
    
    if not 0 <= threshold <= 1:
        return {"error": "threshold must be between 0 and 1"}
    
    # Proceed with logic
    ...
```

## 🚀 Next Steps

1. **Review** `mcp_server_extended.py` - See 15+ ready-to-use tools
2. **Choose** tools relevant to your workflow
3. **Customize** tools for your specific needs
4. **Add** your own custom tools
5. **Share** tools with your team

## 📚 Resources

- **MCP Protocol Docs**: https://github.com/modelcontextprotocol
- **FastMCP Library**: https://github.com/jlowin/fastmcp
- **Our Examples**: `services/mcp_store/mcp_server_extended.py`

---

The MCP Store is YOUR platform - extend it however you need! 🎉

