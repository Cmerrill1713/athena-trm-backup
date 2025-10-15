# 🔒 Log Security Runbook

> **Incident response for log security issues**

---

## 🚨 SYMPTOM: Redaction Alert Fires

**Alert:** `LogRedactionSpike` (Prometheus)

**Meaning:** Redaction rate 3x above baseline  
**Potential Cause:** Someone attempting to expose secrets

### Action Plan

**1. Pull Sample (30 seconds)**
```bash
# Get recent logs that triggered alert
./scripts/validate_log_security.sh --sample

# Or manually
curl -s "http://127.0.0.1:8014/ops/logs?service=athena&tail=100"
```

**2. Identify Pattern (1 minute)**
```bash
# Check what's being redacted
grep "REDACTED" logs/athena_8090.log | tail -20

# Look for new secret types not yet covered
```

**3. Add Redaction Rule (2 minutes)**
```python
# bridge/logs_endpoint.py - redact_secrets()
text = re.sub(r'NEW_PATTERN_HERE', '***REDACTED***', text)
```

**4. Test (30 seconds)**
```bash
pytest tests/test_log_redaction.py -v
```

**5. Deploy (1 minute)**
```bash
make stack-restart
# Or hot-reload if supported
```

---

## 🚨 SYMPTOM: /ops/logs Slow or Timing Out

**Alert:** `LogReadTimeout` (Prometheus)

**Meaning:** Log reads taking >5s  
**Potential Cause:** Large files or slow disk

### Action Plan

**1. Check Service Health (30 seconds)**
```bash
# Open ops window
# Go to Health tab
# Check service status
```

**2. Reduce Lines (immediate)**
```bash
# In LogViewer: Use tail=100 instead of tail=2000
# Or in Bridge: Lower max from 2000 to 500
```

**3. Check File Size (1 minute)**
```bash
ls -lh logs/*.log

# If any > 100MB:
make fastvlm-logrotate  # Or equivalent for service
```

**4. Fallback Mode (if needed)**
```bash
# Use local file fallback instead of Bridge
# LogViewer already does this automatically
```

---

## 🚨 SYMPTOM: Ops Window "Too Chatty"

**Meaning:** Auto-opens too frequently  
**Cause:** Low confidence threshold too high

### Action Plan

**1. Adjust Settings (30 seconds)**
```
In app:
1. Open Ops window (Cmd+Option+O)
2. Go to Meta tab
3. Lower threshold (35% → 25%)
4. Or toggle "Auto-open" OFF
```

**2. Temporary Snooze (immediate)**
```bash
# In code (optional feature):
export OPS_SNOOZE_MINUTES=30
# Ops won't auto-open for 30 minutes
```

**3. Debounce Check**
```
Current: 5s debounce
Session cap: 5 auto-opens max
Then requires manual open
```

---

## 🚨 SYMPTOM: Confidence Panels Missing

**Meaning:** Meta panels not showing in chat  
**Cause:** Meta prompting not enabled

### Action Plan

**1. Check Backend (30 seconds)**
```bash
# Verify meta enabled
echo $META_PROMPTING  # Should be "1"

# If not:
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
make stack-restart
```

**2. Probe Headers (30 seconds)**
```bash
curl -is http://127.0.0.1:8014/api/probe/e2e | grep -i x-meta

# Should see:
x-meta-confidence: 0.85
x-meta-style: reasoned
```

**3. Check Frontend (if backend OK)**
```
In app settings:
• Ensure showMetaPanels = true
```

---

## 🚨 SYMPTOM: Athena Logs Empty or 404

**Meaning:** Log file not found or not readable

### Action Plan

**1. Check Log File (30 seconds)**
```bash
ls -la logs/athena_8090.log

# If missing:
make stack-up  # Creates log file
```

**2. Check Permissions**
```bash
# Ensure readable
chmod 644 logs/athena_8090.log
```

**3. Check Service Mapping**
```python
# bridge/logs_endpoint.py
SERVICE_LOGS = {
    "athena": "logs/athena_8090.log",  # ← Verify path correct
}
```

---

## 🚨 SYMPTOM: Secrets Visible in Logs

**CRITICAL:** Immediate action required

### Action Plan

**1. Stop Serving Logs (immediate)**
```bash
# Kill switch
export OPS_LOGS_ENABLED=0
make stack-restart
```

**2. Identify Leak (1 minute)**
```bash
# Find unredacted pattern
grep -E "Bearer [A-Za-z0-9]{20,}" logs/*.log

# Or
./scripts/validate_log_security.sh
```

**3. Add Redaction (2 minutes)**
```python
# bridge/logs_endpoint.py
text = re.sub(r'LEAKED_PATTERN', '***REDACTED***', text)
```

**4. Test (1 minute)**
```bash
pytest tests/test_log_redaction.py::test_new_pattern -v
```

**5. Re-enable (30 seconds)**
```bash
export OPS_LOGS_ENABLED=1
make stack-restart
```

**6. Audit (5 minutes)**
```bash
# Check who accessed logs recently
grep "/ops/logs" logs/bridge_8014.log | tail -20

# Rotate old logs
mv logs/*.log logs/archive/
make stack-restart
```

---

## 🛡️ PRODUCTION GUARDRAILS

### Feature Flags
```bash
# Ops auto-open
export FEATURE_OPS_AUTOOPEN=1  # Default: enabled

# Logs endpoint
export OPS_LOGS_ENABLED=1  # Default: enabled

# Meta prompting
export META_PROMPTING=1  # Default: enabled
```

### Security Limits
- Max tail: 2000 lines (enforced)
- Timeout: 5 seconds (enforced)
- Allowlist: 7 services (enforced)
- Redaction: 8+ patterns (tested)

### Monitoring
- 5 Prometheus alerts configured
- 12 unit tests for redaction
- CI matrix tests 3 profiles
- Security validation script

---

## 📞 ESCALATION

### If Security Issue
1. Kill switch: `export OPS_LOGS_ENABLED=0`
2. Investigate leak
3. Add redaction
4. Test thoroughly
5. Re-enable

### If Performance Issue
1. Reduce tail lines
2. Check disk I/O
3. Rotate large logs
4. Consider file fallback

### If Integration Issue
1. Check service health
2. Verify ports
3. Check allowlist
4. Review logs

---

## ✅ QUICK REFERENCE

| Issue | Fix | Time |
|-------|-----|------|
| Redaction alert | Add pattern + test | 5 min |
| Slow logs | Reduce tail | 30 sec |
| Too chatty | Lower threshold | 30 sec |
| Missing panels | Enable META_PROMPTING | 1 min |
| Logs 404 | Check file path | 1 min |
| Secrets visible | Kill switch + fix | 10 min |

---

**Runbook Version:** 1.0  
**Last Updated:** October 12, 2025  
**Maintained By:** Operations Team

🔒 **Production runbook ready!**

