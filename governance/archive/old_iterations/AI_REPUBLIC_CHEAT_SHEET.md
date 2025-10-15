# 🤖 AI REPUBLIC CHEAT SHEET

---

## 💚 DAILY CHECK (2 minutes)

```bash
# Health
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager

# Activity
tail -5 /var/log/ai-republic/constitutional_audit.log

# Alerts
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log || echo "✅ Clean"
```

---

## 🚨 TRIBUNAL ALERT? (DO THIS)

```bash
# Check details
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -3

# Options:
# 1. APPROVE (let system handle)
# 2. OVERRIDE (rare, false positive)
# 3. ESCALATE (oversight council)
```

---

## 🔧 SYSTEM DOWN?

```bash
# Restart all
sudo systemctl restart ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Verify
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

---

## 📊 QUICK STATUS

```bash
# Full health
/opt/ai-republic/monitor_constitutional_health.sh && /opt/ai-republic/phase2/monitor_judicial_health.sh

# Logs
tail -f /var/log/ai-republic/constitutional_audit.log
```

---

## 🎯 KEY METRICS

| What | Normal | Warning | Critical |
|------|--------|---------|----------|
| Compliance | >99.9% | 99-99.9% | <99% |
| Tribunals | 0-1/day | 2-5/day | >5/day |
| Uptime | >99.9% | 99-99.9% | <99% |

---

**✅ Normal: Ignore. 🚨 Tribunal: Check. 🔧 Down: Restart.**

*That's the entire AI Republic operations.* 🏛️⚖️🤖
