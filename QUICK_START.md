# Athena Quick Start Guide

**Status:** 🎊 100% Operational  
**Last Updated:** October 16, 2025

---

## ⚡ **ONE-LINE COMMANDS**

```bash
make start          # Start all Athena services
make stop           # Stop all services
make status         # Quick health check
make restart        # Restart everything
make wire-validate  # Verify 100% wiring
```

---

## 🚀 **Daily Usage**

### **Start Your Day**
```bash
cd ~/Documents/GitHub
make start
make status
```

### **View Dashboards**
```bash
open http://localhost:3001  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

### **Run Experiments**
```bash
make exp-shadow      # Safe shadow mode
make exp-remediate   # 1% canary auto-fix
make exp-ab          # A/B policy test
```

### **Switch Modes**
```bash
./scripts/flip_mode.sh shadow   # Observe only
./scripts/flip_mode.sh canary   # 1-5% enforcement
./scripts/flip_mode.sh enforce  # Full governance
```

---

## 📊 **Service Endpoints**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Orchestrator** | 9110 | http://localhost:9110 | Verdict engine |
| **Master API** | 8000 | http://localhost:8000 | Control interface |
| **Prometheus** | 9090 | http://localhost:9090 | Metrics database |
| **Grafana** | 3001 | http://localhost:3001 | Dashboards |
| **Metrics** | 9109 | http://localhost:9109 | Exporter |
| **Canary** | 9111 | http://localhost:9111 | Window eval |

---

## 🧪 **Quick Tests**

### **Test Verdict**
```bash
curl -X POST http://localhost:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "test-'$(date +%s)'",
    "verdict": "PASS",
    "ece_post": 0.03,
    "entropy": 0.05,
    "actions": ["PROMOTE"],
    "ts": "'$(date -u +%FT%TZ)'"
  }'
```

### **Check Health**
```bash
curl http://localhost:9110/health
curl http://localhost:8000/health
curl http://localhost:9090/-/ready
```

### **View Metrics**
```bash
curl -s http://localhost:9110/metrics | grep governance_
```

### **Check State**
```bash
curl -s http://localhost:9110/state | jq
```

---

## 📈 **Monitoring**

### **Watch Metrics Live**
```bash
watch -n 5 'curl -s http://localhost:9110/metrics | grep governance_verdicts_total'
```

### **Check Coverage**
```bash
make gate
# Expected: ≥98%
```

### **View Logs**
```bash
tail -f artifacts/orchestrator.log
tail -f artifacts/athena_api.log
```

---

## 🛡️ **Safety Commands**

### **Emergency Rollback**
```bash
./scripts/flip_mode.sh shadow
```

### **Full Validation**
```bash
make wire-validate  # Should be 100%
make pre-ship-safe  # All tests
```

### **Stop Everything**
```bash
make stop
```

---

## 🎯 **Common Workflows**

### **Morning Startup**
```bash
cd ~/Documents/GitHub
make start
make status
open http://localhost:3001
```

### **Run Daily Experiment**
```bash
make exp-shadow
# Check artifacts/remediation_shadow/
```

### **Deploy to Canary**
```bash
./scripts/flip_mode.sh canary
watch -n 10 'make gate'
# Monitor for 1 hour
```

### **Check System Health**
```bash
make wire-validate
make status
curl http://localhost:9110/metrics | grep governance_
```

---

## 📚 **Documentation**

| File | Purpose |
|------|---------|
| `STATUS.md` | Current system status |
| `NEXT_STEPS.md` | Roadmap (15 min → 1 month) |
| `SYSTEM_ARCHITECTURE.md` | Architecture details |
| `WIRING_DEFINITION.md` | Wiring explanation |
| `IN_PATH_GOVERNANCE_GUIDE.md` | Deployment guide |
| `CURSOR_SETUP_GUIDE.md` | Development setup |

---

## 🚨 **Troubleshooting**

### **Service Won't Start**
```bash
# Check if port is in use
lsof -i :9110
lsof -i :8000

# Kill and restart
make stop
make start
```

### **100% Wiring Failed**
```bash
# Check individual services
make status

# View detailed report
cat artifacts/wiring/wiring_report.json | jq
```

### **Metrics Not Showing**
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq

# Restart Prometheus
docker compose -f docker-compose.athena-governance.yml restart athena-prometheus
```

---

## 🎊 **Success Indicators**

✅ `make status` shows all services green  
✅ `make wire-validate` shows 100%  
✅ `make gate` shows coverage ≥98%  
✅ Grafana dashboards show live data  
✅ `curl localhost:9110/metrics` returns governance metrics  

---

## 📞 **Quick Help**

**"Services won't start"**  
→ `make stop && make start`

**"Need fresh start"**  
→ `make restart`

**"What's running?"**  
→ `make status`

**"Is everything wired?"**  
→ `make wire-validate`

**"What mode am I in?"**  
→ `curl http://localhost:9110/state | jq .mode`

**"How do I view dashboards?"**  
→ `open http://localhost:3001`

---

## 🎯 **Next Actions**

**Today:**
1. `make start` - Get everything running
2. `make status` - Verify all green
3. `make exp-shadow` - Run experiment
4. `open http://localhost:3001` - View results

**This Week:**
1. Run 10 shadow experiments
2. Deploy to canary mode
3. Monitor KPIs
4. Review NEXT_STEPS.md

---

**🚀 Athena is ready to govern your AI systems!**

For detailed guidance, see `NEXT_STEPS.md`

