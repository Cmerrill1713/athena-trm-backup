# 🤖 AI REPUBLIC OPS HANDBOOK

**Daily Operations - What You Actually Need to Know**

---

## 📊 QUICK HEALTH CHECK (Run Every Morning)

```bash
# Check all systems running
systemctl status ai-republic-constitutional --no-pager | grep -E "(Active|Status)"
systemctl status ai-republic-judicial --no-pager | grep -E "(Active|Status)"
systemctl status ai-republic-fop --no-pager | grep -E "(Active|Status)" || echo "Federation optional"
```

**Expected**: All show `Active: active (running)`

---

## 📈 MONITOR REAL-TIME STATUS

### Watch Live Activity
```bash
# See what's happening right now
tail -f /var/log/ai-republic/constitutional_audit.log
```

**What you'll see:**
```
2024-12-19 09:15:22 - INFO - JUDICIAL VERDICT: WARN for op_ai_response_123
2024-12-19 09:16:01 - INFO - JUDICIAL VERDICT: ALLOW for op_user_query_456
```

### Check System Health
```bash
# Overall status
/opt/ai-republic/monitor_constitutional_health.sh
/opt/ai-republic/phase2/monitor_judicial_health.sh
```

---

## 🚨 WHEN TO INTERVENE (Tribunal Alerts Only)

### P0: Tribunal Activation
**What it means**: Major violation detected, system needs human decision

**Check the alert:**
```bash
# See tribunal details
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -5
```

**Your options:**
- **Approve**: Let system quarantine/block as recommended
- **Override**: Rare, only for false positives
- **Escalate**: Involve full oversight council

### P1: System Issues
**What it means**: Services down or performance problems

```bash
# Restart if needed
sudo systemctl restart ai-republic-constitutional
sudo systemctl restart ai-republic-judicial
```

---

## 🔧 COMMON ISSUES & FIXES

### Issue: Service Not Running
```bash
# Check why
systemctl status ai-republic-constitutional

# Restart
sudo systemctl restart ai-republic-constitutional

# Check logs for errors
journalctl -u ai-republic-constitutional --since "1 hour ago"
```

### Issue: High Violation Rate
```bash
# Check what's triggering violations
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -10

# Usually self-corrects, monitor for patterns
```

### Issue: Federation Connection Down (If Used)
```bash
# Restart federation service
sudo systemctl restart ai-republic-fop

# Check federation health
curl -s http://127.0.0.1:8094/v1/health
```

---

## 📋 DAILY CHECKLIST (5 Minutes)

### Morning Check
- [ ] All services running (`systemctl status`)
- [ ] No tribunal alerts in logs
- [ ] Health checks pass
- [ ] Recent activity in audit logs

### Weekly Review
- [ ] Performance trends (response times, violation rates)
- [ ] System resource usage
- [ ] Federation status (if active)

---

## 🎯 WHAT HAPPENS AUTOMATICALLY (Don't Touch)

- ✅ Constitutional checks on every AI action
- ✅ Violation classification and responses
- ✅ Judicial decisions and enforcement
- ✅ Reputation updates
- ✅ Evidence exchange (federation)
- ✅ Log rotation and cleanup
- ✅ Health monitoring and alerts

---

## 🚨 EMERGENCY CONTACTS

**Only use these:**

### System Down
```bash
# Hard restart all
sudo systemctl restart ai-republic-constitutional
sudo systemctl restart ai-republic-judicial
sudo systemctl restart ai-republic-fop
```

### Security Alert
- Check: `grep "EMERGENCY\|QUARANTINE" /var/log/ai-republic/judicial_audit.log`
- Action: Isolate affected components immediately

### Data Loss
- Check: Recent backups in `/var/lib/ai-republic/`
- Action: Restore from latest backup

---

## 📊 KEY METRICS TO WATCH

| Metric | Normal Range | Warning | Critical |
|--------|-------------|---------|----------|
| Compliance Rate | >99.9% | 99.0-99.9% | <99.0% |
| Response Time | <50ms | 50-200ms | >200ms |
| Tribunal Events | 0-1/day | 2-5/day | >5/day |
| Service Uptime | >99.9% | 99.0-99.9% | <99.0% |

---

## 🧭 QUICK START (New Day)

```bash
# 1. Health check
systemctl status ai-republic-constitutional ai-republic-judicial

# 2. Check for alerts
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log

# 3. Monitor activity
tail -f /var/log/ai-republic/constitutional_audit.log
```

**That's it. The system runs itself. You only intervene for tribunal alerts.**

---

## 🔄 MONTHLY MAINTENANCE

### Update Checks
```bash
# Check for updates (if any)
ls /opt/ai-republic/ | grep -E "(phase|update)"

# Backup configs
cp /etc/ai-republic/*.json /var/backups/
```

### Performance Review
```bash
# Monthly metrics
grep "compliance_rate\|response_time" /var/log/ai-republic/constitutional_audit.log | tail -30
```

---

**Bottom line: Check status daily. Only act on tribunal alerts. Everything else is automatic.**

*Your AI Republic is now operational. It governs itself.* 🏛️⚖️🤖
