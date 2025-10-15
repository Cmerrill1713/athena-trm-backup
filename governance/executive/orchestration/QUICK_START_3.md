# MCP Store Quick Start

Get your unified validation storage running in 5 minutes.

## 🚀 Start the Service

```bash
# From the repository root
cd /Users/christianmerrill/Documents/GitHub

# Start MCP Store + dependencies (Postgres, Redis, Weaviate)
make mcp-store-full

# Wait for services to be ready (~20 seconds)
# Check health
make mcp-store-health
```

Expected output:
```
✅ MCP Store is healthy
```

## 🔧 Initialize Weaviate Schema

One-time setup for semantic search:

```bash
make mcp-store-init-schema
```

## ✅ Verify Installation

Run the integration test suite:

```bash
cd AI-Projects/universal-ai-tools/services/mcp_store
./test_integration.sh
```

Expected output:
```
✅ All integration tests passed!
🎉 MCP Store is fully operational!
```

## 📝 Use It

### From Command Line

```bash
# Write a validation result
curl -X POST http://localhost:8411/v1/store/results \
  -H 'Content-Type: application/json' \
  -d '{
    "agent": "smoke-test",
    "service": "bridge",
    "status": "PASS",
    "summary": "All health checks passed",
    "details": {"latency_ms": 45, "checks": 5},
    "commit": "v0.9.7"
  }'

# List recent failures
curl "http://localhost:8411/v1/store/results?status=FAIL&limit=10" | jq

# View specific service history
curl "http://localhost:8411/v1/store/results?service=bridge&limit=20" | jq
```

### From Python

```python
import requests

# Store a result
result = requests.post("http://localhost:8411/v1/store/results", json={
    "agent": "pytest",
    "service": "athena",
    "status": "PASS",
    "summary": "Integration tests passed",
    "details": {"tests_run": 25, "duration_s": 12.5}
}).json()

print(f"Stored with ID: {result['id']}")

# Query results
recent = requests.get("http://localhost:8411/v1/store/results", params={
    "service": "athena",
    "limit": 50
}).json()

print(f"Found {recent['count']} results")
```

### From MCP Tools

```python
from mcp import Client

mcp = Client()

# Store via MCP
result = mcp.call_tool("store_write",
    agent="validator",
    service="bridge",
    status="PASS",
    summary="Health check passed",
    details_json='{"p95_ms": 612}'
)

# Query via MCP
failures = mcp.call_tool("store_list", status="FAIL", limit=10)
```

### From Go Services

```go
import "github.com/yourusername/universal-ai-tools/go-services/shared/mcpstore"

client := mcpstore.NewClient()

// Store health check result
client.StoreHealthCheck("api-gateway", true, 45, map[string]interface{}{
    "endpoint": "/health",
    "dependencies": "all-green",
})
```

## 🔍 View Your Data

### Postgres (Source of Truth)

```bash
docker exec -it universal-ai-tools-postgres psql -U postgres -d universal_ai_tools

# Query recent results
SELECT agent, service, status, summary, created_at
FROM validation_results
ORDER BY created_at DESC
LIMIT 10;

# Count by status
SELECT status, COUNT(*)
FROM validation_results
GROUP BY status;
```

### Redis (Cache)

```bash
docker exec -it universal-ai-tools-redis redis-cli

# Check cached correlation IDs
KEYS mcpstore:*
```

### Weaviate (Semantic Search)

```bash
curl http://localhost:8090/v1/objects?class=ValidationResult | jq
```

## 🔄 Daily Workflow

### Morning Health Check

```bash
# Check all services
make mcp-store-health
make stack-status

# View overnight failures
curl "http://localhost:8411/v1/store/results?status=FAIL&limit=20" | jq
```

### During Development

```bash
# Your tests automatically store results (if using enhanced MCP server)
npm test
pytest

# View what just ran
curl "http://localhost:8411/v1/store/results?limit=5" | jq
```

### Before Deploy

```bash
# Run validation suite
./scripts/validate_all_services.sh

# Check results
CORRELATION_ID="pre-deploy-$(date +%Y%m%d)"
curl "http://localhost:8411/v1/store/results?correlation_id=$CORRELATION_ID" | jq
```

## 🛑 Stop the Service

```bash
# Stop MCP Store only
make mcp-store-down

# Stop everything (MCP Store + dependencies)
cd AI-Projects/universal-ai-tools
docker compose -f docker-compose.yml -f docker-compose.mcp-store.yml down
```

## 📚 Next Steps

- [Migration Guide](./MIGRATION_GUIDE.md) - Integrate your services
- [README](./README.md) - Full documentation
- [API Reference](./README.md#api-endpoints) - Complete API docs

## 🆘 Troubleshooting

### Service won't start

```bash
# Check Docker
docker ps

# Check logs
make mcp-store-logs

# Check dependencies
docker ps | grep -E "postgres|redis|weaviate"
```

### Can't connect

```bash
# Verify network
docker network ls | grep ai-network

# Test connectivity
curl http://localhost:8411/health
```

### Results not storing

```bash
# Check Postgres connection
docker exec -it universal-ai-tools-postgres psql -U postgres -d universal_ai_tools -c "\dt"

# Check table exists
docker exec -it universal-ai-tools-postgres psql -U postgres -d universal_ai_tools -c "SELECT COUNT(*) FROM validation_results;"
```

### Need help?

```bash
# View service logs
make mcp-store-logs

# Check health with details
curl http://localhost:8411/health | jq
```

## 🎉 You're All Set!

Your MCP Store is now running and ready to collect validation results from all your services!

