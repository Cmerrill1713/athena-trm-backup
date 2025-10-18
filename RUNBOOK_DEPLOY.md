# 🚀 **DEPLOYMENT RUNBOOK - v0.1.0**

## **FREEZE STATUS: MONDAY-READY** 🧊

**Release:** v0.1.0  
**Git Tag:** v0.1.0  
**Date:** 2025-10-17  
**Status:** All validations passing, production-ready

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### **Validation Status**

- ✅ All 13 TODOs complete
- ✅ 12/12 tests passing (Swift Reflex 6/6, Graph-of-Code 6/6)
- ✅ 9/9 services operational
- ✅ Integration tests passing (Verdict→ECE, Router failover)
- ✅ Documentation complete

### **Snapshots Captured**

- ✅ `snapshots/docker-running-2025-10-17.txt` - Running containers
- ✅ `snapshots/router-pip-2025-10-17.txt` - Python dependencies (678 packages)
- ✅ Git tag: v0.1.0 pushed to origin

---

## 🚀 **GO-LIVE PLAYBOOK (90 seconds)**

### **1. Deploy New Version**

```bash
cd /Users/christianmerrill/Documents/GitHub
./scripts/deploy.sh
```

**What it does:**

1. Backs up current deployment
2. Stops existing services
3. Builds fresh images with BUILD_SHA
4. Starts all services
5. Runs health checks
6. Runs contract tests

**Expected output:**

```
✅ DEPLOYMENT SUCCESSFUL
Release: v0.1.0
Build: <git-sha>
Services: 6 healthy
```

### **2. Manual Verification**

```bash
# Test router routing
curl -X POST http://localhost:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"query": "test", "max_tokens": 50}'

# Test verdict flow
curl -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "test", "verdict": "PASS", "confidence": 0.95}'

# Check all health endpoints
for port in 9113 9110 8412 8000 9090 3001; do
  curl -s http://localhost:$port/health | jq .status || true
done
```

---

## 🔄 **ROLLBACK PLAYBOOK (30 seconds)**

### **If Deployment Fails**

```bash
cd /Users/christianmerrill/Documents/GitHub
./scripts/rollback.sh
```

**What it does:**

1. Stops current deployment
2. Reverts to `docker-compose.prev.yml`
3. Starts previous version
4. Quick health check

**Expected output:**

```
✅ ROLLBACK COMPLETE
Reverted to previous deployment
```

---

## 🛡️ **GUARDRAILS (PREVENT "SURPRISE TUESDAYS")**

### **1. Change Freeze**

- **Rule:** No merges to main until after Monday stand-up
- **Enforcement:** Branch protection on GitHub
- **Override:** Requires approval from 2+ reviewers

### **2. Golden Tests as CI Gate**

- **File:** `tests/test_contracts.sh`
- **Runs:** On every PR and before deploy
- **Gates:** Deploy only if all tests pass
- **Tests:**
  - Router health
  - AGI Core health
  - Orchestrator health
  - MCP UI health
  - Router routing decision
  - Verdict→ECE flow

### **3. Alerts That Matter**

**Critical (Page immediately):**

- ⚠️ **RouterDown** - Router unreachable for 1+ minute
- ⚠️ **OrchestratorDown** - Orchestrator unreachable for 2+ minutes

**Warnings (Monitor):**

- ⚠️ **MCPToolFailureRateHigh** - MCP tools failing >5% over 10min
- ⚠️ **RouterTTFTHigh** - Time-to-first-token p95 > 1.0s over 5min
- ⚠️ **HighErrorRate** - 5xx errors >10% over 5min

**Configuration:** `monitoring/prometheus/alerts.yml`

---

## 📊 **POST-DEPLOY MONITORING (First 30 Minutes)**

### **1. Grafana Dashboards**

**URL:** http://localhost:3001

**Key Dashboards:**

- **Platform Health Glance** - Overall system status
- **Routing Dashboard** - Router latency, failovers, decisions
- **Bridge Dashboard** - Swift app integration health
- **Circuit Breaker Panel** - Service degradation tracking

**What to watch:**

- Router p95 latency < 1.0s
- Upstream failure rate < 5%
- MCP tool errors minimal
- All services showing "healthy"

### **2. Log Monitoring**

```bash
# Router logs
tail -f /tmp/router.log | grep -E "ERROR|WARN"

# AGI Core logs
tail -f /tmp/agi-core.log | grep -E "ERROR|WARN"

# Canary Consumer logs
tail -f /tmp/canary-consumer.log | grep -E "ERROR|WARN"

# Docker logs (if containerized)
docker compose logs -f --tail=50 router
```

**Red flags:**

- Repeated timeout errors
- 4xx errors from MCP /tool/web_search
- Connection refused errors
- Memory/CPU warnings

### **3. Prometheus Metrics**

**URL:** http://localhost:9090

**Key Queries:**

```promql
# Router latency
histogram_quantile(0.95, rate(athena_router_ttft_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# MCP tool failures
rate(mcp_tool_errors_total[10m]) / rate(mcp_tool_calls_total[10m])

# Service uptime
up{job=~"athena-.*"}
```

---

## 🔧 **TROUBLESHOOTING**

### **Router Not Starting**

```bash
# Check logs
tail -50 /tmp/router.log

# Common issues:
# - Port 9113 already in use
# - Missing OLLAMA_ENDPOINT
# - Python dependencies missing

# Fix:
pkill -f "services/router/app.py"
python3 services/router/app.py > /tmp/router.log 2>&1 &
```

### **Health Check Failing**

```bash
# Check service status
curl http://localhost:9113/health

# If 404/connection refused:
# 1. Check if service is running: ps aux | grep router
# 2. Check if port is listening: lsof -i :9113
# 3. Restart service

# If unhealthy response:
# Check logs for errors
```

### **Contract Tests Failing**

```bash
# Run tests manually to see details
bash tests/test_contracts.sh

# Check specific service
curl -v http://localhost:9113/health

# Verify all services are up
docker compose ps
ps aux | grep -E "router|agi_core|canary"
```

---

## 🎯 **LOW-RISK "NICE NEXT WINS"**

### **1. vLLM Backend for UAT 7B**

**Impact:** 2-3× throughput, same API  
**Risk:** Low (drop-in replacement)  
**Time:** 1 hour

### **2. Synthetic Canary**

**What:** Cron tiny prompt every 5 min, alert on mismatch  
**Risk:** Low (monitoring only)  
**Time:** 30 minutes

### **3. Chaos Minute** (Off-hours)

**What:** Kill MCP or UAT once, confirm graceful degrade  
**Risk:** Medium (test failover)  
**Time:** 15 minutes
**When:** Off-hours only

---

## 📋 **SERVICE ENDPOINTS**

| Service       | Port | Health        | Purpose                    |
| ------------- | ---- | ------------- | -------------------------- |
| Router        | 9113 | `/health`     | Local-first model routing  |
| AGI Core      | 8000 | `/health`     | Multi-agent framework      |
| Orchestrator  | 9110 | `/health`     | Verdict processing         |
| MCP UI        | 8412 | `/health`     | Model control protocol     |
| Bridge        | 8014 | `/health`     | Swift integration          |
| Graph-of-Code | 8200 | `/health`     | Symbol dependency analysis |
| Prometheus    | 9090 | `/-/healthy`  | Metrics collection         |
| Grafana       | 3001 | `/api/health` | Visualization              |

---

## 🏆 **SUCCESS CRITERIA**

Deployment is successful when:

- ✅ All contract tests pass (`bash tests/test_contracts.sh`)
- ✅ All services respond to health checks
- ✅ Router successfully routes test request
- ✅ Verdict flow processes test verdict
- ✅ No critical alerts firing
- ✅ Grafana dashboards show green
- ✅ Logs show no errors for 5+ minutes

---

## 📞 **ESCALATION**

If deployment fails and rollback doesn't resolve:

1. Check `INTEGRATION_RUNBOOK.md` for service-specific troubleshooting
2. Review `COMPLETE_MISSION_SUCCESS.md` for system architecture
3. Check git history: `git log --oneline v0.1.0..HEAD`
4. Compare with snapshots: `snapshots/docker-running-2025-10-17.txt`

---

**Last Updated:** 2025-10-17  
**Version:** v0.1.0  
**Status:** Production-ready, Monday-proof 🧊🚀
