# MCP Store Quick Reference Card

## 🚀 Launch (5 minutes)

```bash
make mcp-store-full           # Start everything
make mcp-store-init-schema    # Setup Weaviate (once)
make mcp-store-health         # Verify
```

## 📝 Write Results

### Bash
```bash
curl -X POST http://localhost:8411/v1/store/results \
  -H 'Content-Type: application/json' \
  -d '{"agent":"test","service":"bridge","status":"PASS","summary":"OK"}'
```

### Python
```python
import requests
requests.post("http://localhost:8411/v1/store/results", json={
    "agent": "pytest", "service": "bridge", "status": "PASS"
})
```

### MCP Tool
```python
mcp.call_tool("store_write", agent="test", service="bridge", 
              status="PASS", summary="OK", details_json='{}')
```

## 🔍 Query Results

```bash
# Recent failures
curl "http://localhost:8411/v1/store/results?status=FAIL&limit=10" | jq

# Service history
curl "http://localhost:8411/v1/store/results?service=bridge" | jq

# Test run
curl "http://localhost:8411/v1/store/results?correlation_id=RUN_ID" | jq
```

## 🔧 Operations

```bash
make mcp-store-up           # Start
make mcp-store-down         # Stop
make mcp-store-logs         # View logs
make mcp-store-restart      # Restart
make mcp-store-health       # Health check
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| `services/mcp_store/QUICK_START.md` | 5-min setup |
| `services/mcp_store/README.md` | Full API docs |
| `services/mcp_store/MIGRATION_GUIDE.md` | Integration |
| `MCP_STORE_COMPLETE.md` | Architecture |
| `MCP_MIGRATION_SUMMARY.md` | What we built |

## 🔗 URLs

- Service: http://localhost:8411
- Health: http://localhost:8411/health
- Docs: http://localhost:8411/docs

## 🆘 Troubleshooting

```bash
make mcp-store-logs                    # View logs
docker ps | grep mcp-store             # Check running
./services/mcp_store/test_integration.sh  # Run tests
```

## ✅ Status Codes

- `PASS` - Success
- `FAIL` - Failure
- `WARN` - Warning

---
**Location:** /Users/christianmerrill/Documents/GitHub/  
**Status:** ✅ Ready to ship
