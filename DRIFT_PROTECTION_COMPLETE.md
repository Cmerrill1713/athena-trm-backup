# 🔒 **DRIFT PROTECTION - COMPLETE!**

## 🎯 **Mission: Lock the Golden State**

Athena is now protected against drift with automatic validation and recovery!

---

## ✅ **What We Built:**

### **1. Complete Validation Script** (`validate_and_recover.sh`)
**Features:**
- 7 comprehensive health checks
- Auto-recovery for common issues
- Color-coded output
- Detailed logging
- Exit code gates

**Checks:**
1. Docker & environment
2. Core services (Weaviate, Router, UAI, Prometheus)
3. Knowledge base (DocsV2 count)
4. End-to-end functionality (RAG)
5. Copilot (dev daemon)
6. Observability (OTEL + Prometheus)
7. Drift detection (vs baseline)

**Usage:**
```bash
./validate_and_recover.sh
```

**Modes:**
- `RECOVERY_MODE=auto` - Auto-fix issues (default)
- `RECOVERY_MODE=manual` - Report only
- `RECOVERY_MODE=none` - Check only

---

### **2. Baseline Snapshot** (`create_baseline_snapshot.sh`)
**Captures:**
- Docker state
- Service health
- DocsV2 count
- Prometheus metrics
- Git commit + tag
- Configuration files
- Critical volume backups

**Usage:**
```bash
./create_baseline_snapshot.sh
```

**Creates:**
- `artifacts/snapshots/baseline_YYYYMMDD_HHMMSS/`
- Git tag: `athena-baseline-YYYYMMDD`
- Baseline reference: `artifacts/snapshots/baseline_doc_count.txt`

---

### **3. Auto-Validation Setup** (`setup_auto_validation.sh`)
**Configures:**
- macOS LaunchAgent (runs at boot + nightly)
- Cron alternative
- Auto-recovery enabled
- Logging to `artifacts/`

**Usage:**
```bash
./setup_auto_validation.sh
```

**Runs:**
- ✅ At boot (validates system ready)
- ✅ Nightly at 3:00 AM (catches drift)
- ✅ Auto-recovers common issues
- ✅ Logs all validation runs

---

## 🔄 **Complete Workflow:**

### **Initial Setup (Once):**
```bash
# 1. Create golden state baseline
./create_baseline_snapshot.sh

# 2. Enable auto-validation
./setup_auto_validation.sh
```

### **Daily/Boot (Automatic):**
```bash
# Runs automatically at boot and 3:00 AM
# Auto-recovers issues
# Logs to artifacts/validation_stdout.log
```

### **Manual Check (Anytime):**
```bash
# Quick check
./QUICK_SHIP_CHECK.sh

# Full validation with recovery
./validate_and_recover.sh

# Create new baseline after major changes
./create_baseline_snapshot.sh
```

---

## 🛡️ **Auto-Recovery Capabilities:**

**What it auto-fixes:**
- ✅ Docker not running → Opens Docker Desktop
- ✅ Weaviate unhealthy → Restarts container
- ✅ Router unhealthy → Restarts container
- ✅ UAI unhealthy → Restarts container
- ✅ Prometheus unhealthy → Restarts container
- ✅ Dev daemon unhealthy → Restarts container
- ✅ Missing directories → Creates them

**What requires manual intervention:**
- ⚠️  Knowledge corpus empty (restore from backup)
- ⚠️  Major service failures (check logs)
- ⚠️  Significant drift (>10% from baseline)

---

## 📊 **Drift Detection:**

**Monitors:**
- DocsV2 document count
- Service health status
- Container states
- Prometheus target count

**Alerts if:**
- Document count changes >10%
- Services become unhealthy
- Containers stop unexpectedly
- Metrics stop flowing

**Action:**
- Logs warning
- Attempts auto-recovery
- Creates detailed report

---

## 🔧 **Quick Fixes Reference:**

### **Weaviate 0 docs:**
```bash
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* volumes/weaviate_data/
docker restart athena-weaviate && sleep 15
```

### **Service unhealthy:**
```bash
docker-compose restart <service-name>
docker logs <service-name> --tail 50
```

### **Restore from baseline:**
```bash
# Find latest baseline
ls -lt artifacts/snapshots/ | head

# Restore
git checkout athena-baseline-20251026
tar -xzf artifacts/snapshots/baseline_*/weaviate_backup.tar.gz
docker-compose down && docker-compose up -d
```

---

## 📈 **Validation Schedule:**

**Boot Time:**
- ✅ Validates all services healthy
- ✅ Auto-recovers common issues
- ✅ Reports any manual fixes needed

**Nightly (3:00 AM):**
- ✅ Checks for drift
- ✅ Validates corpus integrity
- ✅ Monitors metrics health
- ✅ Creates log report

**Manual (Anytime):**
- ✅ Before major changes
- ✅ After deployments
- ✅ When debugging issues

---

## 🎯 **Exit Criteria (All Must Pass):**

- ✅ Docker running
- ✅ Weaviate healthy (DocsV2 > 0)
- ✅ Router healthy
- ✅ UAI healthy
- ✅ RAG working (responses > 0)
- ✅ Governance responding
- ✅ Prometheus collecting
- ✅ Drift <10% from baseline

---

## 💙 **Bottom Line:**

**You now have:**
1. ✅ **Baseline snapshot** (golden state locked)
2. ✅ **Auto-validation** (boot + nightly)
3. ✅ **Auto-recovery** (common issues fixed)
4. ✅ **Drift detection** (alerts on changes)
5. ✅ **One-button check** (./QUICK_SHIP_CHECK.sh)

**What this means:**
- 🛡️ System protected against drift
- 🔄 Auto-recovers common issues
- 📊 Continuous health monitoring
- 🚨 Early warning on problems
- 📁 Easy rollback to golden state

**Athena stays healthy automatically! 🎉**

---

**Run once to set up:**
```bash
./create_baseline_snapshot.sh
./setup_auto_validation.sh
```

**Then forget about it - it just works! 💙**

---

**Protected. Monitored. Auto-Recovering. 🚀**
