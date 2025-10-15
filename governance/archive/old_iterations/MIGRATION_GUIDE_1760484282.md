# MCP Store Migration Guide

This guide shows how to migrate your existing services and tests to use the centralized MCP Store.

## 🎯 Overview

The MCP Store replaces scattered validation logging with a unified system:

**Before:** Each service logs to its own files/stdout
**After:** All services write to MCP Store → Postgres + Weaviate + Redis

## 📦 What We Found

### Existing MCP Server (`mcp-server.js`)
- Tests LLM Router, HRM-MLX, FastVLM
- Runs Playwright tests
- Swift compilation/testing tools

### Go Services (47 services)
- API Gateway, Auth, Chat, Memory, WebSocket Hub
- Load Balancer, Message Broker, Cache Coordinator
- Research, Orchestration, Monitoring services
- All have `/health` endpoints

## 🚀 Quick Migration Paths

### 1. Use Enhanced MCP Server (Easiest)

Replace your current MCP server config:

**Before:**
```json
{
  "universal-ai-tools": {
    "command": "node",
    "args": ["mcp-server.js"]
  }
}
```

**After:**
```json
{
  "universal-ai-tools-enhanced": {
    "command": "node",
    "args": ["services/mcp_store/mcp_enhanced_server.js"],
    "env": {
      "MCPSTORE_URL": "http://127.0.0.1:8411"
    }
  }
}
```

**Benefits:**
- ✅ Zero code changes
- ✅ Automatic result storage
- ✅ All existing tools work identically
- ✅ Adds latency metrics automatically

### 2. Add MCP Store Client to Go Services

Create a reusable Go client library:

```go
// go-services/shared/mcpstore/client.go
package mcpstore

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "time"
)

type ValidationResult struct {
    Agent         string                 `json:"agent"`
    Service       string                 `json:"service"`
    Status        string                 `json:"status"` // PASS, FAIL, WARN
    Summary       string                 `json:"summary"`
    Details       map[string]interface{} `json:"details"`
    Commit        string                 `json:"commit,omitempty"`
    CorrelationID string                 `json:"correlation_id,omitempty"`
}

type Client struct {
    BaseURL    string
    HTTPClient *http.Client
}

func NewClient() *Client {
    baseURL := os.Getenv("MCPSTORE_URL")
    if baseURL == "" {
        baseURL = "http://localhost:8411"
    }
    
    return &Client{
        BaseURL: baseURL,
        HTTPClient: &http.Client{
            Timeout: 10 * time.Second,
        },
    }
}

func (c *Client) Store(result ValidationResult) error {
    jsonData, err := json.Marshal(result)
    if err != nil {
        return fmt.Errorf("marshal error: %w", err)
    }
    
    resp, err := c.HTTPClient.Post(
        fmt.Sprintf("%s/v1/store/results", c.BaseURL),
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return fmt.Errorf("request error: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode >= 400 {
        return fmt.Errorf("store failed: status %d", resp.StatusCode)
    }
    
    return nil
}

func (c *Client) StoreHealthCheck(serviceName string, healthy bool, latencyMs int64, details map[string]interface{}) {
    status := "PASS"
    if !healthy {
        status = "FAIL"
    }
    
    if details == nil {
        details = make(map[string]interface{})
    }
    details["latency_ms"] = latencyMs
    
    // Fire-and-forget, don't block on logging
    go c.Store(ValidationResult{
        Agent:   "health-monitor",
        Service: serviceName,
        Status:  status,
        Summary: fmt.Sprintf("Health check: %s", status),
        Details: details,
    })
}
```

### 3. Integrate with Existing Go Services

**Example: API Gateway Health Monitor**

```go
// go-services/api-gateway/main.go

import (
    "github.com/yourusername/universal-ai-tools/go-services/shared/mcpstore"
)

var mcpClient *mcpstore.Client

func init() {
    mcpClient = mcpstore.NewClient()
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    
    // Your existing health check logic
    healthy := checkDependencies()
    
    latency := time.Since(start).Milliseconds()
    
    // Store result in MCP Store
    mcpClient.StoreHealthCheck("api-gateway", healthy, latency, map[string]interface{}{
        "endpoint":     r.URL.Path,
        "dependencies": getDependencyStatus(),
    })
    
    // Your existing response
    if healthy {
        json.NewEncoder(w).Encode(map[string]interface{}{
            "status": "healthy",
            "latency_ms": latency,
        })
    } else {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]interface{}{
            "status": "unhealthy",
        })
    }
}
```

### 4. Add to Testing Scripts

**Example: Validation Script Integration**

```bash
#!/bin/bash
# scripts/validate_all_services.sh

MCPSTORE_URL=${MCPSTORE_URL:-"http://localhost:8411"}
CORRELATION_ID="validate-$(date +%s)"

# Test each service
for service in api-gateway:8080 auth-service:8015 chat-service:8016; do
    name=${service%%:*}
    port=${service##*:}
    
    echo "Testing $name..."
    
    start=$(date +%s%3N)
    if curl -sf http://localhost:$port/health > /dev/null; then
        status="PASS"
        latency=$(($(date +%s%3N) - start))
        
        # Store success
        curl -sS -X POST "$MCPSTORE_URL/v1/store/results" \
            -H "Content-Type: application/json" \
            -d "{
                \"agent\": \"validate-script\",
                \"service\": \"$name\",
                \"status\": \"$status\",
                \"summary\": \"Health check passed\",
                \"details\": {\"port\": $port, \"latency_ms\": $latency},
                \"correlation_id\": \"$CORRELATION_ID\"
            }" > /dev/null
        
        echo "✅ $name ($latency ms)"
    else
        # Store failure
        curl -sS -X POST "$MCPSTORE_URL/v1/store/results" \
            -H "Content-Type: application/json" \
            -d "{
                \"agent\": \"validate-script\",
                \"service\": \"$name\",
                \"status\": \"FAIL\",
                \"summary\": \"Health check failed\",
                \"details\": {\"port\": $port},
                \"correlation_id\": \"$CORRELATION_ID\"
            }" > /dev/null
        
        echo "❌ $name"
    fi
done

# View results
echo ""
echo "Results stored with correlation_id: $CORRELATION_ID"
echo "View at: http://localhost:8411/v1/store/results?correlation_id=$CORRELATION_ID"
```

### 5. Python Services Integration

```python
# orchestrator/validation_client.py

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional

class MCPStoreClient:
    def __init__(self):
        self.base_url = os.getenv("MCPSTORE_URL", "http://localhost:8411")
    
    def store(
        self,
        agent: str,
        service: str,
        status: str,
        summary: str = "",
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a validation result."""
        payload = {
            "agent": agent,
            "service": service,
            "status": status,
            "summary": summary,
            "details": details or {},
            "correlation_id": correlation_id,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        
        response = requests.post(
            f"{self.base_url}/v1/store/results",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    
    def store_test_result(
        self,
        test_name: str,
        passed: bool,
        duration_ms: int,
        **kwargs
    ):
        """Convenience method for test results."""
        return self.store(
            agent="pytest",
            service=test_name,
            status="PASS" if passed else "FAIL",
            summary=f"Test {'passed' if passed else 'failed'} in {duration_ms}ms",
            details={
                "duration_ms": duration_ms,
                **kwargs
            }
        )

# Usage in tests
def test_bridge_health():
    import time
    client = MCPStoreClient()
    
    start = time.time()
    result = requests.get("http://localhost:8014/health")
    duration_ms = int((time.time() - start) * 1000)
    
    passed = result.status_code == 200
    
    # Store result
    client.store_test_result(
        test_name="bridge-health",
        passed=passed,
        duration_ms=duration_ms,
        status_code=result.status_code,
    )
    
    assert passed
```

## 🔄 Migration Priority

### Phase 1: Zero-Touch (Week 1)
- ✅ Deploy MCP Store service
- ✅ Use enhanced MCP server
- ✅ Add to validation scripts

### Phase 2: High-Value Services (Week 2)
1. Bridge service
2. Athena service
3. UAT service
4. API Gateway
5. Auth Service

### Phase 3: All Go Services (Weeks 3-4)
- Add shared MCP Store client library
- Update all 47 Go services
- Migrate health checks

### Phase 4: Testing Suite (Week 5)
- Pytest integration
- Playwright integration
- CI/CD pipeline integration

## 📊 Querying Results

### CLI Examples

```bash
# View all recent failures
curl "http://localhost:8411/v1/store/results?status=FAIL&limit=20" | jq

# View results for a specific service
curl "http://localhost:8411/v1/store/results?service=bridge&limit=50" | jq

# View results from a specific test run
curl "http://localhost:8411/v1/store/results?correlation_id=nightly-2025-10-13" | jq
```

### Using MCP Tools

```python
from mcp import Client

mcp = Client()

# Get recent failures
failures = mcp.call_tool("store_list", status="FAIL", limit=10)

# Get bridge test history
bridge_results = mcp.call_tool("store_list", service="bridge", limit=50)
```

## 🎯 Next Steps

1. **Start MCP Store:**
   ```bash
   make mcp-store-up
   make mcp-store-init-schema
   ```

2. **Update MCP Config:**
   ```bash
   # Use enhanced server
   cp mcp-config.json mcp-config.backup.json
   # Edit mcp-config.json to use mcp_enhanced_server.js
   ```

3. **Run Tests:**
   ```bash
   # Tests now auto-store results
   node services/mcp_store/mcp_enhanced_server.js
   ```

4. **View Dashboard:**
   ```bash
   # Coming soon: Grafana dashboard
   open http://localhost:3002
   ```

## 🆘 Troubleshooting

### MCP Store not reachable
```bash
make mcp-store-logs
# Check if dependencies are running
docker ps | grep -E "postgres|redis|weaviate"
```

### Results not appearing
```bash
# Check Postgres
docker exec -it universal-ai-tools-postgres psql -U postgres -d universal_ai_tools -c "SELECT * FROM validation_results ORDER BY created_at DESC LIMIT 5;"

# Check service logs
make mcp-store-logs
```

### Weaviate schema missing
```bash
make mcp-store-init-schema
```

## 📚 References

- [MCP Store README](./README.md)
- [API Documentation](./README.md#api-endpoints)
- [Go Services Documentation](../../go-services/README.md)
- [Testing Guide](../../docs/testing.md)

