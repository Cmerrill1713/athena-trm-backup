# 📋 **WEEKLY OPS CHECKLIST**

**Print this and stick on your monitor!**

---

## 🗓️ **MONDAY (1 minute)**

### **Quick Health Check:**
```bash
./QUICK_SHIP_CHECK.sh
```

**Expect:** ✅ All checks passed

### **Review Alerts:**
```bash
tail -n 50 artifacts/validation_stdout.log
```

**Look for:** Any warnings or auto-recoveries over the weekend

**Action:** If any issues found, investigate before they compound

---

## 🗓️ **WEDNESDAY (2 minutes)**

### **Refresh Baseline:**
```bash
make metrics-snapshot
```

**Why:** Keeps performance baseline current

### **Shadow Health:**
```bash
make go-parity
```

**Expect:** Parity ≥ 99%

**Why:** Ensures Go migration path stays ready

---

## 🗓️ **FRIDAY (3 minutes)**

### **Backup Corpus:**
```bash
make kb-backup
```

**Verify:**
```bash
ls -lh artifacts/backups/ | tail -1
```

**Expect:** Fresh .tar.gz file

### **Dashboard Check:**
```bash
open http://localhost:3001  # Grafana
# Or check status: curl http://localhost:9113/health
```

**Look for:**
- ✅ Router p95 <500ms
- ✅ Error rate <1%
- ✅ All services green
- ✅ No drift alerts

---

## 🚨 **"IN CASE OF WEIRDNESS" ONE-LINERS:**

### **Hard Reset Services (Keeps Data):**
```bash
docker-compose up -d --force-recreate
```

### **Roll Back to Last Golden Tag:**
```bash
git checkout $(git tag -l 'athena-baseline-*' | tail -n1)
./validate_and_recover.sh
```

### **Re-attach Corpus:**
```bash
docker restart athena-weaviate && sleep 15
./QUICK_SHIP_CHECK.sh
```

### **Restore from Backup:**
```bash
make kb-restore-latest
docker-compose restart athena-weaviate
```

### **Emergency Rollback (Go → Python):**
```bash
make go-rollback
```

---

## 📊 **MONTHLY (15 minutes)**

### **Full Confidence Drill:**
```bash
./CONFIDENCE_DRILL.sh
```

**Expect:** Perfect score (10/10 passed)

### **Create New Baseline:**
```bash
./create_baseline_snapshot.sh
```

### **Review Metrics:**
- Check Grafana for trends
- Review alert log for patterns
- Update capability registry if needed

### **Clean Old Backups:**
```bash
# Keep last 30 days
find artifacts/backups -name "*.tar.gz" -mtime +30 -delete
find artifacts/snapshots -type d -mtime +30 -delete
```

---

## 🎯 **HEALTH INDICATORS (GREEN = GOOD):**

### **Core Services:**
- ✅ Weaviate: `curl http://127.0.0.1:8090/v1/.well-known/ready`
- ✅ Router: `curl http://127.0.0.1:9113/health`
- ✅ UAI: `curl http://127.0.0.1:8080/health`
- ✅ Prometheus: `curl http://127.0.0.1:9090/-/healthy`

### **Knowledge Base:**
- ✅ DocsV2 count > 0
- ✅ Drift <10% from baseline
- ✅ Fresh backup exists

### **Performance:**
- ✅ Router p95 <500ms
- ✅ RAG hit@5 ≥0.97
- ✅ Error rate <1%

### **Alerts:**
- ✅ No critical alerts in last 7 days
- ✅ Auto-recoveries working
- ✅ Notifications received

---

## 💡 **TIPS:**

### **Before Major Changes:**
```bash
./create_baseline_snapshot.sh
# Creates git tag + backup
# Easy rollback if needed
```

### **Daily Habit:**
```bash
# Just check once:
./QUICK_SHIP_CHECK.sh
```

### **If You See Red:**
1. Don't panic - system auto-recovers most issues
2. Check `artifacts/validation_latest.log` for details
3. Run `./validate_and_recover.sh` for auto-fix
4. If stuck, rollback to last baseline

---

## 📅 **SCHEDULE SUMMARY:**

| Day | Task | Duration | Command |
|-----|------|----------|---------|
| Monday | Health check | 1 min | `./QUICK_SHIP_CHECK.sh` |
| Monday | Review alerts | 1 min | `tail artifacts/validation_stdout.log` |
| Wednesday | Refresh baseline | 1 min | `make metrics-snapshot` |
| Wednesday | Shadow health | 1 min | `make go-parity` |
| Friday | Backup corpus | 2 min | `make kb-backup` |
| Friday | Dashboard check | 1 min | Open Grafana/check status |
| Monthly | Full drill | 15 min | `./CONFIDENCE_DRILL.sh` |
| Monthly | Create baseline | 5 min | `./create_baseline_snapshot.sh` |

**Total: ~10 minutes/week + 20 minutes/month**

---

## 💙 **BOTTOM LINE:**

**Athena stays healthy with minimal effort:**
- Auto-validates nightly
- Auto-recovers issues
- Alerts you to problems
- Easy rollback anytime

**You focus on building. Athena protects itself! 🛡️🚀**

---

**Print this. Use this. Stay protected! 💙**

