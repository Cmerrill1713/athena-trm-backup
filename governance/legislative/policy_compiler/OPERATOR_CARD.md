# 🛡️ ATHENA — OPERATOR CARD (v1.0)

**🕒 Estimated Time**: 2–4 min  
**📅 Frequency**: Daily (preferably morning)

---

## ✅ **STEP 1 — Core Health (60–90s)**

```bash
make kokoro-health
```

**PASS IF**:
- ✅ p95 latency < 3000 ms
- ✅ Routing success ≥ 95%
- ✅ Kokoro voice active (no fallback)

---

## 🧪 **STEP 2 — End-to-End Validation (60s)**

```bash
make report-health
```

**PASS IF**:
- ✅ Athena speaks with Kokoro voice
- ✅ Report includes alerts + success rate + watchdog status
- ✅ No "Using fallback voice" announcement

---

## 🧠 **STEP 3 — Safety & Canary Check (30–60s)**

```bash
make breaker-test
make canary-eval
make auto-rollback
```

**PASS IF**:
- ✅ Breaker trips/re-closes correctly
- ✅ Canary check shows "monitoring" or "stable"
- ✅ No unexpected rollbacks triggered

---

## 💾 **STEP 4 — Backup Verification (20s)**

```bash
make pg-backup
ls -lh backups/ | tail -1
```

**PASS IF**:
- ✅ New backup present for today
- ✅ Size > 0 MB
- ✅ Rotation/retention intact

---

## 📊 **STEP 5 — Dashboard Glance (30s)**

1. Open Grafana → http://localhost:3001
2. Confirm:
   - 🟢 success rate steady
   - 🟢 latency below thresholds
   - 🟢 no restart spikes
   - 🟢 fallback rate low

---

## 🚨 **Fast Response Playbook**

| Issue | Action |
|-------|--------|
| **TTS fallback** | `make kokoro-health` → `make kokoro-start` |
| **Slow / down FastVLM** | `make fastvlm-health` → check watchdog logs |
| **Canary regression** | `make auto-rollback` |
| **Circuit breaker stuck open** | `make breaker-test` |
| **Missing metrics** | Restart Prometheus / Grafana |

---

## ⏱️ **Cron Guardrails (Already Wired)**

```bash
# Auto-rollback (every 5 min)
*/5 * * * *  make auto-rollback >> logs/rollback.log 2>&1

# Nightly evolution (2 AM)
0 2 * * *    make learn DAYS=7 >> logs/evolution.log 2>&1

# Daily backup (3 AM)
0 3 * * *    make pg-backup >> logs/backup.log 2>&1

# Weekly autopilot report (Monday 9 AM)
0 9 * * 1    make weekly-autopilot >> logs/weekly.log 2>&1

# Canary auto-promotion (every 6 hours)
0 */6 * * *  make canary-auto-promote >> logs/auto_promotion.log 2>&1
```

**Install with**:
```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
```

---

## 📈 **Key SLOs**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Routing success** | ≥ 95% | < 90% |
| **p95 latency** | < 1500 ms | > 3000 ms |
| **TTS fallback rate** | < 1% | > 5% |
| **Watchdog restarts/hr** | ≤ 3 | > 3 |
| **Canary delta (stat-sig)** | > +3% | rollback if worse |

---

## 🧭 **Command Cheat Sheet**

| Action | Command |
|--------|---------|
| **Daily health check** | `make kokoro-health` |
| **Voice check** | `make kokoro-test` |
| **Canary evaluation** | `make canary-eval` |
| **Auto rollback** | `make auto-rollback` |
| **Breaker test** | `make breaker-test` |
| **Promotion check** | `make canary-auto-promote` |
| **Backup** | `make pg-backup` |
| **Logs** | `tail -f logs/*.log` |

---

## 🔗 **Quick Links**

| Service | URL |
|---------|-----|
| **Grafana** | http://localhost:3001 |
| **Prometheus** | http://localhost:9090 |
| **Alerts** | http://localhost:9090/alerts |
| **Targets** | http://localhost:9090/targets |
| **Kokoro Health** | http://localhost:8020/health |

---

## 🟢 **Daily Outcome**

- ✅ All systems green
- ✅ Canary stable or promoted safely
- ✅ Voice natural (Kokoro)
- ✅ Backups intact
- ✅ TRM learning overnight

---

## 📎 **Metadata**

**File**: `OPERATOR_CARD.md`  
**Version**: v1.0  
**Owner**: Operator / QE / DevOps  
**System**: Athena (Production)  
**Last Updated**: October 12, 2025  

---

## 🎯 **Quick Copy-Paste**

### Complete Daily Check (All Steps)
```bash
make kokoro-health && \
make report-health && \
make breaker-test && \
make canary-eval && \
make auto-rollback && \
make pg-backup && \
echo "" && \
echo "✅ All checks passed - GO!"
```

### Emergency Restart All
```bash
make kokoro-start && \
docker restart athena-prometheus && \
docker restart athena-postgres && \
echo "✅ Services restarted"
```

---

## 🎤 **Voice Quality Check**

**Quick Test**:
```bash
make kokoro-test
```

**Expected**: Natural, warm, expressive female voice

**If Generic**: Run `make kokoro-start`

---

**This is the card you—or anyone on rotation—can run daily to keep Athena stable.**

**Canary-eval is now fully wired with statistical Wilson interval check.**

**This locks in the autonomous + statistically sound promotion loop with human-speed operational checks.** 🚀

---

**🟢 Keep this card visible at your desk!** 📋✅

**Athena is production-ready with natural voice!** 🎤✨