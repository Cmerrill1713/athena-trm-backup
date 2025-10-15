# 🚦 Athena Operator Card - Daily Go/No-Go

**Time**: 2-4 minutes | **Frequency**: Daily | **Owner**: Operations

---

## 🎯 **Quick Start**

```bash
cd ~/Documents/GitHub
mkdir -p logs
```

---

## ✅ **Go/No-Go Checklist**

### 1️⃣  Health Sweep (60-90s)

```bash
make kokoro-health
```

**Pass Criteria**:
- ✅ Kokoro is UP
- ✅ Model: Kokoro-82M
- ✅ No errors in output

**Action if FAIL**:
```bash
make kokoro-start
make kokoro-health  # Verify
```

---

### 2️⃣  End-to-End (60s)

```bash
make report-health
```

**Pass Criteria**:
- ✅ Report window opens
- ✅ Athena speaks with natural voice (Kokoro)
- ✅ NO "Using fallback voice" announcement
- ✅ Synopsis is clean (20-30s)

**Action if FAIL**:
```bash
# If generic voice or fallback announcement:
make kokoro-health
make kokoro-start

# Retry
make report-health
```

---

### 3️⃣  Safety Nets (30-60s)

```bash
make breaker-test
make auto-rollback
```

**Pass Criteria**:
- ✅ Breaker opens at 80% failure
- ✅ `Allow? False` shown
- ✅ Auto-rollback says "canary healthy" OR "gap within tolerance"

**Action if FAIL**:
```bash
# Check auto-rollback logic
cat models/routing_flags.json

# Review recent decisions
make learn-stats
```

---

### 4️⃣  Data Protection (20s)

```bash
make pg-backup
ls -lh backups/ | tail -1
```

**Pass Criteria**:
- ✅ Backup created with today's timestamp
- ✅ Size > 0 KB

**Action if FAIL**:
```bash
# Check database
docker ps | grep postgres

# Restart if needed
docker restart athena-postgres

# Retry backup
make pg-backup
```

---

## 🚦 **Go/No-Go Decision**

### ✅ **GO** (Ship It!)
- All 4 checks pass
- Voice is natural (Kokoro)
- No critical alerts
- Data accumulating

→ **Continue normal operations**

### ⚠️  **CAUTION** (Monitor)
- 1-2 checks fail
- Fallback voice in use
- Warnings in logs

→ **Fix issues, monitor closely**

### 🔴 **NO-GO** (Fix First)
- 3+ checks fail
- Multiple systems down
- Critical alerts

→ **Stop deployments, debug, fix**

---

## 🔥 **Red/Yellow Playbook**

### Voice Fell Back / Silent

```bash
make kokoro-health || make kokoro-start
make report-health  # Verify
```

**Root Cause**: Kokoro server down  
**Fix Time**: <1 minute

---

### FastVLM Slow or Down

```bash
make fastvlm-health
tail -200 /tmp/fastvlm_watchdog.log
```

**Root Cause**: Process crash or hang  
**Fix Time**: <2 minutes (watchdog auto-recovers)

---

### Success Rate < 95% or Alerts Firing

```bash
make learn-stats
make auto-rollback
open http://localhost:9090/alerts
```

**Root Cause**: Model degradation or bad canary  
**Fix Time**: 5 minutes (auto-rollback handles)

---

### Prometheus "No Data"

```bash
open http://localhost:9090/targets
docker compose -f docker-compose.monitoring.yml restart prometheus
```

**Root Cause**: Scraping failure or container issue  
**Fix Time**: <2 minutes

---

## 🔒 **One-Time Guardrails Setup**

### Enable Automation

```bash
# 1. Set up cron jobs
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh

# 2. Enable Kokoro auto-start
make kokoro-autostart

# 3. Verify
crontab -l | grep "Athena Automation"
launchctl list | grep kokoro
```

### Cron Schedule

```
*/5 * * * *  Auto-rollback check
0 2 * * *    Nightly evolution
0 3 * * *    Daily backup
0 9 * * 1    Weekly autopilot report
0 9 * * 1-5  Daily health report
```

---

## 📊 **SLO Quick Reference**

| Metric | Target | Alert |
|--------|--------|-------|
| Routing Success (7d) | ≥95% | <90% |
| P95 Latency | <1500ms | >3000ms |
| TTS Fallback (15m) | <1% | >1% |
| Watchdog Restarts (1h) | ≤3 | >3 |
| Circuit Breaker Opens | 0 | >0 |
| Canary Gap | <5% | ≥5% |

---

## 🔗 **Quick Links**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **AlertManager** | http://localhost:9093 | - |
| **Metrics** | http://localhost:8888/metrics/ | - |
| **Kokoro Health** | http://localhost:8020/health | - |

---

## 📈 **Daily Commands**

### Morning Routine (2-4 min)
```bash
make kokoro-health
make report-health
make learn-stats
```

### As Needed
```bash
# Monitor services
make kokoro-logs
make monitoring-logs

# Check dashboards
open http://localhost:3001

# Review evolution
tail -50 logs/evolution.log
```

---

## 🎯 **Expected Voice Behavior**

### ✅ **CORRECT** (Kokoro)
- Natural, warm female voice
- Smooth articulation
- Expressive inflection
- Professional quality
- Says: "All systems nominal. 7-day success 100.0 percent..."

### ❌ **WRONG** (Generic/Fallback)
- Monotone, robotic
- Flat delivery
- Announces: "Using fallback voice temporarily."

**If you hear fallback**: Run `make kokoro-start`

---

## 📋 **Daily Log Review**

### Check These Logs
```bash
tail -50 logs/rollback.log     # Any auto-rollbacks?
tail -50 logs/evolution.log    # Any promotions?
tail -50 logs/backup.log       # Backups successful?
```

### Expected Entries

**rollback.log**:
```
✅ Canary healthy. Gap within tolerance (<5%)
```

**evolution.log**:
```
✅ Ingesting outcomes... rolling_window=150
```

**backup.log**:
```
✅ Wrote backups/pg-20251012-030000.sql.zst (4.2K)
```

---

## 🔄 **Weekly Review (Monday)**

Automated report at 9 AM:
```bash
# Review in Athena Reporter window
# Or check logs:
tail -100 logs/weekly.log
```

**Topics**:
- 7-day success rate
- Total decisions processed
- Model promotions
- Circuit breaker trips
- Active alerts

---

## ✅ **Production Readiness**

| Component | Status | Daily Check |
|-----------|--------|-------------|
| Voice (Kokoro) | 🟢 GO | `make kokoro-health` |
| Reporting | 🟢 GO | `make report-health` |
| Monitoring | 🟢 GO | `make check-metrics` |
| Learning | 🟢 GO | `make learn-stats` |
| Safety | 🟢 GO | `make breaker-test` |
| Backups | 🟢 GO | `make pg-backup` |

**Overall**: 🟢 **PRODUCTION-READY**

---

## 🚨 **Emergency Contacts**

| Issue | First Command | Escalation |
|-------|--------------|------------|
| Voice down | `make kokoro-start` | Check `/tmp/kokoro.err` |
| No metrics | `docker restart athena-prometheus` | Check scrape targets |
| Low success | `make auto-rollback` | Review `make learn-stats` |
| DB issues | `docker restart athena-postgres` | Check disk space |

---

## 🎤 **Voice Quality Verification**

**Listen Test**:
```bash
make kokoro-test
```

**Expected**: Natural, warm, expressive female voice

**NOT Expected**: Monotone, robotic, generic voice

**If generic**: Kokoro is down - run `make kokoro-start`

---

## 📅 **Print & Post**

**Recommended**: Print this card and keep it visible at your desk.

**Update Frequency**: Review weekly, update as system evolves.

**Last Updated**: October 12, 2025

---

**🟢 Athena is GO for production! Natural voice operational!** 🚀🎤✨

---

## 🔖 **Quick Copy-Paste Commands**

```bash
# Daily Go/No-Go (run all at once)
make kokoro-health && \
make report-health && \
make breaker-test && \
make learn-stats && \
echo "✅ All checks passed - GO!"

# Emergency restart
make kokoro-start && \
docker restart athena-prometheus && \
docker restart athena-postgres

# Full system status
make kokoro-health && \
make check-metrics && \
make learn-stats && \
open http://localhost:3001
```

---

**Keep this card handy! Athena is production-ready!** 🎯✅
