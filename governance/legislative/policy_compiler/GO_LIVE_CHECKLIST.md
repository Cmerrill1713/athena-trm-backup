# 🚀 FastVLM Go-Live Checklist

**5-minute production deployment**

---

## ✅ Pre-Flight

- [ ] Workspace: `/Users/christianmerrill/Documents/GitHub`
- [ ] Disk space: >5GB free (for model)
- [ ] Ports available: 8811 (FastVLM), 9090 (Prometheus), 3001 (Grafana)
- [ ] Database: PostgreSQL running on 5433

---

## 🎯 Option 1: One-Command Go-Live (Recommended)

```bash
make fastvlm-go-live
```

**What it does**:
1. ✅ Starts monitoring stack
2. ✅ Starts FastVLM server (background)
3. ✅ Waits for warmup (30s)
4. ✅ Seeds traffic (smoke tests)
5. ✅ Runs daily ops check
6. ✅ Offers to enable automation

**Time**: ~5 minutes (mostly waiting for warmup + downloads if first time)

---

## 🎯 Option 2: Manual Steps

### **Step 1: Start Services** (2 min)
```bash
# Terminal 1: Monitoring
make monitoring-up

# Terminal 2: FastVLM
make fastvlm-server
# Wait for: "🚀 FastVLM Server ready on http://127.0.0.1:8811"
```

---

### **Step 2: Validate** (30 sec)
```bash
# Terminal 3 (or after Ctrl+C from Terminal 2)
sleep 30
make fastvlm-validate
```

**Expected**: All ✓'s

---

### **Step 3: Seed Traffic** (30 sec)
```bash
make fastvlm-smoke
make vision-chart IMG=fastvlm/assets/canary/chart.png
```

---

### **Step 4: Verify Metrics** (30 sec)
```bash
# Check metrics endpoint
make fastvlm-metrics | head -20

# Check Prometheus scraping
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job=="fastvlm")'
```

---

### **Step 5: Enable Automation** (2 min)
```bash
# 24/7 watchdog
make fastvlm-autostart

# Nightly learning
bash scripts/learn/setup_nightly_learning.sh

# Auto-promotion (every 6h)
bash scripts/setup_auto_promotion.sh

# Verify
crontab -l
```

---

## 📊 Verification Commands

### **Health Checks**
```bash
make fastvlm-health              # 5-second check
make fastvlm-confidence          # Full confidence check
make daily-ops                   # 90-second ops check
```

### **Metrics**
```bash
# Server metrics
curl http://127.0.0.1:8811/metrics | grep "^fastvlm_"

# Prometheus
curl 'http://localhost:9090/api/v1/query?query=up{job="fastvlm"}' | jq

# Recording rules
curl 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' | jq
```

### **Lineage**
```bash
make lineage-tree                # View model history
make lineage-open                # Open full report
```

---

## 🎯 Success Criteria

- [ ] `make fastvlm-health` returns ✅
- [ ] `make fastvlm-validate` all checks pass
- [ ] Prometheus scraping FastVLM (check /targets)
- [ ] Recording rules active (fast queries work)
- [ ] Smoke tests pass (6 image types)
- [ ] Metrics visible: `make fastvlm-metrics`
- [ ] Lineage generated: `make lineage-tree`
- [ ] Daily ops clean: `make daily-ops`
- [ ] Cron jobs installed: `crontab -l`
- [ ] Real vision query works

---

## 🧪 Smoke Tests

### **Quick Test**
```bash
make vision-chart IMG=fastvlm/assets/canary/chart.png
```

**Expected**: Chart data extracted in <2 seconds

---

### **Full Smoke Suite**
```bash
make fastvlm-smoke
```

**Expected**: 6 tests pass

---

### **Promotion Test**
```bash
make promotion-test
```

**Expected**: Promotion metric incremented

---

## 🚨 Rollback Plan

### **If Something Breaks**

**Stop services**:
```bash
make fastvlm-down
make monitoring-down
```

**Check logs**:
```bash
make fastvlm-logs
tail /tmp/fastvlm_server.log
```

**Disable automation**:
```bash
crontab -l | grep -v "make learn\|canary-auto-promote" | crontab -
make fastvlm-disable-autostart
```

---

### **If Canary Causes Issues**

**Instant rollback**:
```bash
make canary-rollback
source /tmp/canary.env
```

**Disable auto-promotion**:
```bash
crontab -l | grep -v canary-auto-promote | crontab -
```

---

## 📊 Post-Go-Live Monitoring

### **First Hour**
- [ ] Check every 15 min: `make fastvlm-health`
- [ ] Watch metrics: `make fastvlm-metrics`
- [ ] Monitor logs: `make fastvlm-logs`

### **First Day**
- [ ] Morning: `make daily-ops`
- [ ] Evening: `make daily-ops`
- [ ] Check lineage: `make lineage-tree`

### **First Week**
- [ ] Daily: `make daily-ops`
- [ ] Check learning: `tail logs/evolution.log`
- [ ] Check promotions: `tail logs/auto_promotion.log`

---

## 🎯 Quick Reference

### **Start**
```bash
make fastvlm-go-live             # One-command go-live
# or
make fastvlm-quickstart          # Setup + start + validate
```

### **Daily**
```bash
make daily-ops                   # 90-second check
```

### **Use**
```bash
make vision-chart IMG=chart.png  # Extract data
make vision-ocr IMG=doc.png      # Extract text
```

### **Monitor**
```bash
make fastvlm-metrics             # View metrics
make lineage-tree                # View history
```

### **Emergency**
```bash
make fastvlm-down                # Stop
make canary-rollback             # Rollback canary
```

---

## ✅ Go-Live Checklist

### **Pre-Flight**
- [ ] Ports available (8811, 9090, 3001)
- [ ] Disk space >5GB
- [ ] Database accessible

### **Deployment**
- [ ] Run: `make fastvlm-go-live`
- [ ] All steps complete successfully
- [ ] Services started

### **Validation**
- [ ] Health checks pass
- [ ] Metrics flowing
- [ ] Smoke tests pass
- [ ] Lineage generated

### **Automation**
- [ ] Watchdog enabled
- [ ] Cron jobs installed
- [ ] Verified with `crontab -l`

### **Final Check**
- [ ] `make daily-ops` all green
- [ ] Real vision query works
- [ ] Grafana dashboard shows data

---

## 🎉 You're Live!

**Run**: `make fastvlm-go-live`

**Then**: `make daily-ops` every morning

**That's it!** The system runs itself! 🚀

