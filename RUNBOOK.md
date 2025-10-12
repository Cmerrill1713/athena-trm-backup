# 🚀 **NEUROFORGE BRIDGE RUNBOOK**

## Quick Reference Card

### **Start (Mock Mode)**
```bash
make bridge-up
cd NeuroForgeApp && API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

### **Start (Real Mode)**
```bash
make bridge-down
USE_MOCK=0 \
UAT_BASE=http://127.0.0.1:8080 \
ATHENA_BASE=http://127.0.0.1:8090 \
UAT_TOKEN=supersecret \
ATH_TOKEN=supersecret \
BRIDGE_TOKEN=supersecret \
make bridge-up
```

### **Smoke Tests**
```bash
make bridge-smoke          # Contract validation
make bridge-slo            # p95 < 250ms check
make bridge-chaos          # Fallback validation
```

### **Stop Everything**
```bash
make bridge-down           # Stop bridge
make stop-all              # Stop bridge + UAT + Athena
```

### **Emergency Rollback**
```bash
make bridge-down && USE_MOCK=1 make bridge-up  # Instant safe mode
```

---

## 🔧 **Operational Procedures**

### **Procedure 1: Cold Start (Production)**
```bash
# 1. Verify backends are up
curl -s http://127.0.0.1:8080/health | jq .status  # UAT
curl -s http://127.0.0.1:8090/health | jq .status  # Athena

# 2. Start bridge with production config
ENV=prod \
USE_MOCK=0 \
UAT_BASE=http://127.0.0.1:8080 \
ATHENA_BASE=http://127.0.0.1:8090 \
UAT_TOKEN=$UAT_TOKEN \
ATH_TOKEN=$ATH_TOKEN \
BRIDGE_TOKEN=$BRIDGE_TOKEN \
make bridge-up

# 3. Verify health
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/health | jq .

# 4. Run smoke tests
BRIDGE_TOKEN=$BRIDGE_TOKEN make bridge-smoke

# 5. Launch app
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

### **Procedure 2: Verify Correlation IDs**
```bash
# Generate correlation ID
CID=$(uuidgen)

# Make request with correlation ID
curl -H "x-bridge-token: $BRIDGE_TOKEN" \
     -H "x-correlation-id: $CID" \
     http://127.0.0.1:8014/traces -s > /dev/null

# Check logs for exact correlation ID
tail -f logs/adapter.log | grep "$CID"
# Expected: timestamp GET /traces 200 Xms mock/real $CID
```

### **Procedure 3: Chaos Testing**
```bash
# 1. Start in real mode
USE_MOCK=0 make bridge-up

# 2. Verify real backends
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/health | jq .

# 3. Kill UAT
pkill -f ":8080" || true

# 4. Verify fallback to mock
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/traces | jq '.[0]'
# Expected: Mock data returned, no error

# 5. Check logs for circuit breaker
tail logs/adapter.log | grep "error"
# Expected: "UAT: error" but bridge still responds

# 6. Restart UAT
make uat-up

# 7. Verify auto-recovery
sleep 5
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/health | jq .uat.status
# Expected: "healthy" or "ok"
```

### **Procedure 4: SLO Validation**
```bash
# Run SLO check (p95 < 250ms)
python3 scripts/slo_check.py

# If it fails:
# 1. Check backend health
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8090/health

# 2. Check logs for slow queries
tail -f logs/adapter.log | grep -E '[0-9]{3,}ms'

# 3. Verify network latency
ping -c 5 127.0.0.1

# 4. DO NOT bump the SLO threshold - fix the backends
```

---

## 🚨 **Troubleshooting**

### **Problem: Bridge won't start**
```bash
# Check if port is in use
lsof -i:8014

# Check PID file
cat .bridge.pid
kill -0 $(cat .bridge.pid) 2>/dev/null && echo "Process running" || echo "PID stale"

# Force clean restart
make bridge-down
rm -f .bridge.pid
lsof -ti:8014 | xargs -n 1 kill -9 2>/dev/null || true
make bridge-up
```

### **Problem: Auth errors (401)**
```bash
# In development, don't use BRIDGE_TOKEN
ENV=dev BRIDGE_TOKEN= make bridge-up

# In production, ensure token is set
echo "BRIDGE_TOKEN=$BRIDGE_TOKEN"

# Test with token
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/health
```

### **Problem: Slow responses**
```bash
# Run SLO check
make bridge-slo

# Check for slow endpoints
tail -100 logs/adapter.log | grep -E '[0-9]{3,}ms'

# Check backend health
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8090/health

# Monitor live requests
tail -f logs/adapter.log
```

### **Problem: Swift compilation errors**
```bash
# Check for type conflicts
cd NeuroForgeApp
swift build 2>&1 | grep error

# Common issues:
# - "invalid redeclaration": Duplicate types (check Orchestrator.swift vs TracePanelView.swift)
# - "actor cannot have global actor": Remove @MainActor from actor Orchestrator
# - "AnyCodable ambiguous": Remove duplicate AnyCodable definitions

# Clean build
rm -rf .build
swift build
```

### **Problem: Schema drift**
```bash
# Check contract version
curl http://127.0.0.1:8014/contract | jq .version

# Compare with Swift models
grep -r "struct TraceSummary" NeuroForgeApp/Sources/

# Update Swift models to match API contract
# See bridge/adapter.py for authoritative schema
```

---

## 📊 **Health Checks**

### **Quick Health Check**
```bash
# All endpoints
curl http://127.0.0.1:8014/health | jq .
curl http://127.0.0.1:8014/contract | jq .version
curl http://127.0.0.1:8014/ | jq .service

# With auth
curl -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/traces | jq 'length'
```

### **Deep Health Check**
```bash
# 1. Bridge health
curl http://127.0.0.1:8014/health | jq '.'

# 2. Backend health
curl http://127.0.0.1:8080/health | jq .  # UAT
curl http://127.0.0.1:8090/health | jq .  # Athena

# 3. Contract version
curl http://127.0.0.1:8014/contract | jq '.version, .endpoints'

# 4. Recent logs
tail -20 logs/adapter.log

# 5. Process check
ps aux | grep -E '(uvicorn|bridge)'

# 6. Port check
lsof -i:8014 -i:8080 -i:8090
```

---

## 🔐 **Security**

### **Token Management**
```bash
# Generate secure token
BRIDGE_TOKEN=$(openssl rand -hex 32)

# Store in environment
echo "export BRIDGE_TOKEN=$BRIDGE_TOKEN" >> ~/.zshrc
source ~/.zshrc

# Use in production
ENV=prod BRIDGE_TOKEN=$BRIDGE_TOKEN make bridge-up
```

### **Log Sanitization**
```bash
# Logs should NOT contain:
# - Auth tokens
# - User PII
# - Full request bodies

# Logs SHOULD contain:
# - Correlation IDs
# - Status codes
# - Latency
# - Route decisions
# - Error types (not error details with PII)

# Check logs
tail -100 logs/adapter.log | grep -i "token\|password\|secret" || echo "✅ No secrets in logs"
```

---

## 📈 **Performance**

### **Load Testing**
```bash
# Sequential load
for i in {1..100}; do
  curl -s -H "x-bridge-token: $BRIDGE_TOKEN" http://127.0.0.1:8014/traces > /dev/null
  echo -n "."
done
echo ""

# Check SLO
make bridge-slo
```

### **Memory Monitoring**
```bash
# Watch memory usage
watch -n 5 'ps aux | grep uvicorn | grep -v grep'

# Check for leaks (run for 10 minutes)
for i in {1..600}; do
  curl -s http://127.0.0.1:8014/health > /dev/null
  sleep 1
done

# Memory should plateau, not grow linearly
```

---

## 🔄 **Deployment**

### **Tag Release**
```bash
# Tag bridge version
git tag -a bridge-1.0.0 -m "Bridge: Production ready with day-2 ops"
git push origin bridge-1.0.0

# Tag last known good
git tag -f bridge-lkg
git push -f origin bridge-lkg
```

### **launchd Setup (macOS Auto-Restart)**
```bash
# Copy launchd plist
cp launchd/com.neuroforge.bridge.plist ~/Library/LaunchAgents/

# Edit for your environment
nano ~/Library/LaunchAgents/com.neuroforge.bridge.plist
# Update paths, tokens, etc.

# Load
launchctl load -w ~/Library/LaunchAgents/com.neuroforge.bridge.plist

# Verify
launchctl list | grep neuroforge

# Check logs
tail -f ~/Library/Logs/neuroforge-bridge.{out,err}

# Unload (if needed)
launchctl unload ~/Library/LaunchAgents/com.neuroforge.bridge.plist
```

---

## 🎯 **Quick Reference**

| Command | Purpose |
|---------|---------|
| `make bridge-up` | Start bridge (mock mode) |
| `make bridge-down` | Stop bridge |
| `make bridge-smoke` | Run smoke tests |
| `make bridge-slo` | Check SLO (p95 < 250ms) |
| `make bridge-chaos` | Chaos test |
| `make bridge-all` | Start bridge + app |
| `./scripts/bridge_ops.sh start` | Start bridge |
| `./scripts/bridge_ops.sh smoke` | Run smoke tests |
| `./scripts/bridge_ops.sh real` | Start with real backends |
| `tail -f logs/adapter.log` | Watch logs |
| `cat .bridge.pid` | Check PID |
| `lsof -i:8014` | Check port |

---

## 📞 **Escalation**

1. **Check logs**: `tail -100 logs/adapter.log`
2. **Check health**: `curl http://127.0.0.1:8014/health | jq .`
3. **Restart**: `make bridge-down && make bridge-up`
4. **Rollback**: `make bridge-down && USE_MOCK=1 make bridge-up`
5. **Emergency**: Kill all: `make stop-all`

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
**Owner**: Christian Merrill
