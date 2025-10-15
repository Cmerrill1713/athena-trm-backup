# 🤖 AI REPUBLIC OPERATIONS REFERENCE

**Complete Operational Guide for Constitutional AI Governance**

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Daily Operations](#daily-operations)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Intervention Procedures](#intervention-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)
8. [Quick Reference Cheat Sheet](#quick-reference-cheat-sheet)
9. [Emergency Contacts](#emergency-contacts)

---

## EXECUTIVE SUMMARY

### What This System Does
The AI Republic provides constitutional governance for autonomous AI systems through:
- **Phase 1**: Constitutional runtime enforcement (non-bypassable checks)
- **Phase 2**: Judicial court system (automatic violation classification and response)
- **Phase 3**: Federation gateway (optional multi-jurisdiction cooperation)

### Operational Philosophy
- **Self-Governing**: System handles 99% of operations automatically
- **Human Oversight**: Intervention only required for critical tribunal alerts
- **Minimal Maintenance**: 5-minute daily checks, weekly reviews

### Key Metrics
- **Uptime**: >99.9% target
- **Compliance Rate**: >99.9% target
- **Tribunal Events**: 0-1 per day normal
- **Response Time**: <50ms for constitutional checks

---

## SYSTEM ARCHITECTURE

### Core Components
- **ai-republic-constitutional**: Phase 1 constitutional runtime
- **ai-republic-judicial**: Phase 2 judicial enforcement system
- **ai-republic-fop**: Phase 3 federation gateway (optional)

### Data Flow
```
AI Action → Constitutional Check → Judicial Review → Enforcement Action
```

### Log Locations
- `/var/log/ai-republic/constitutional_audit.log`: All constitutional checks
- `/var/log/ai-republic/judicial_audit.log`: Court decisions and actions
- `/var/log/ai-republic/fop_deployment.log`: Federation operations

---

## DAILY OPERATIONS

### Morning Health Check (5 minutes)

#### 1. Service Status
```bash
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

**Expected Output:**
```
● ai-republic-constitutional.service - Sovereign AI Constitutional Republic Runtime
     Active: active (running) since Mon 2024-12-19 09:00:00 UTC

● ai-republic-judicial.service - Sovereign AI Republic Judicial System
     Active: active (running) since Mon 2024-12-19 09:00:00 UTC
```

#### 2. Recent Activity
```bash
tail -10 /var/log/ai-republic/constitutional_audit.log
```

**What to Look For:**
- Recent JUDICIAL VERDICT entries
- Compliance scores >0.95
- No EMERGENCY or TRIBUNAL alerts

#### 3. Alert Check
```bash
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log || echo "✅ No critical alerts"
```

### Weekly Review (15 minutes)

#### Performance Metrics
```bash
# Compliance trends
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -50 | awk '{print $NF}' | sort -n | tail -5

# Tribunal frequency
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | wc -l
```

#### System Resources
```bash
# CPU/Memory usage
ps aux | grep ai-republic | head -3

# Disk space
df -h /var/log /opt/ai-republic
```

---

## MONITORING & ALERTS

### Real-Time Monitoring

#### Live Activity Stream
```bash
tail -f /var/log/ai-republic/constitutional_audit.log
```

#### Health Dashboard
```bash
/opt/ai-republic/monitor_constitutional_health.sh
/opt/ai-republic/phase2/monitor_judicial_health.sh
```

### Alert Levels

#### Normal (Green)
- Services running
- Compliance >99.9%
- No tribunal alerts
- Response times <50ms

#### Warning (Yellow)
- Compliance 99.0-99.9%
- Tribunals 2-5 per day
- Response times 50-200ms
- Minor service hiccups

#### Critical (Red)
- Compliance <99.0%
- Tribunals >5 per day
- Services down
- Response times >200ms

---

## INTERVENTION PROCEDURES

### Tribunal Alerts (P0 - Immediate Action)

#### Detection
```bash
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -1
```

#### Assessment
1. **Review Context**: Check violation details and compliance score
2. **Evaluate Severity**: Determine if system recommendation is appropriate
3. **Check Pattern**: Look for repeated violations from same source

#### Response Options

**Option 1: Approve System Action (Most Common)**
- Allow automatic quarantine/block as determined
- Document approval for audit trail

**Option 2: Override (Rare - False Positives Only)**
```bash
# If false positive detected
echo "Override approved: [reason]" >> /var/log/ai-republic/human_override.log
# System will allow operation but flag for monitoring
```

**Option 3: Escalate to Council**
- Contact oversight council for complex ethical decisions
- Provide full context and system recommendation
- Await council guidance

### Service Failures (P1)

#### Single Service Down
```bash
# Identify which service
systemctl status ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Restart specific service
sudo systemctl restart ai-republic-[service_name]
```

#### Multiple Services Down
```bash
# Full system restart
sudo systemctl restart ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Verify recovery
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

### Performance Issues (P2)

#### High Violation Rate
```bash
# Check patterns
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -20

# Identify common violations
grep "VIOLATION" /var/log/ai-republic/judicial_audit.log | tail -10 | cut -d' ' -f5- | sort | uniq -c
```

#### Slow Response Times
```bash
# Check system load
uptime
free -h
top -bn1 | head -20
```

---

## TROUBLESHOOTING

### Common Issues

#### Issue: Service Won't Start
```bash
# Check logs for errors
journalctl -u ai-republic-constitutional --since "1 hour ago" | tail -20

# Check dependencies
systemctl status ai-republic-constitutional ai-republic-judicial

# Verify files exist
ls -la /opt/ai-republic/ /var/log/ai-republic/
```

#### Issue: High False Positive Rate
```bash
# Review recent judgments
grep "JUDICIAL VERDICT" /var/log/ai-republic/constitutional_audit.log | tail -20

# Check for configuration drift
diff /etc/ai-republic/runtime.json /opt/ai-republic/phase1_config.json
```

#### Issue: Federation Connection Issues (If Used)
```bash
# Check federation health
curl -s http://127.0.0.1:8094/v1/health

# Restart federation service
sudo systemctl restart ai-republic-fop

# Check federation logs
tail -20 /var/log/ai-republic/fop_deployment.log
```

### Diagnostic Commands

#### Full System Health
```bash
#!/bin/bash
echo "=== AI REPUBLIC HEALTH CHECK ==="
echo

echo "Services:"
systemctl status ai-republic-constitutional ai-republic-judicial ai-republic-fop --no-pager | grep -E "(Active|Status)"
echo

echo "Recent Activity:"
tail -5 /var/log/ai-republic/constitutional_audit.log
echo

echo "Tribunal Check:"
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -3 || echo "None"
echo

echo "Compliance Rate:"
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -10 | awk '{sum+=$NF; count++} END {print sum/count "%"}'
```

---

## MAINTENANCE

### Daily Tasks
- [ ] Service status check
- [ ] Alert review
- [ ] Activity log scan
- [ ] Performance metrics check

### Weekly Tasks
- [ ] Full health assessment
- [ ] Log rotation verification
- [ ] Performance trend analysis
- [ ] Configuration backup

### Monthly Tasks
- [ ] Comprehensive audit review
- [ ] Security patch application
- [ ] Performance optimization
- [ ] Documentation update

### Quarterly Tasks
- [ ] Major version updates
- [ ] Cryptographic key rotation
- [ ] Disaster recovery testing
- [ ] Federation expansion review (if applicable)

### Backup Procedures
```bash
# Configuration backup
cp /etc/ai-republic/*.json /var/backups/config_$(date +%Y%m%d).json

# Reputation data backup
cp /var/lib/ai-republic/reputation_state.json /var/backups/reputation_$(date +%Y%m%d).json

# Audit log archival
gzip /var/log/ai-republic/constitutional_audit.log.$(date +%Y%m%d)
```

---

## QUICK REFERENCE CHEAT SHEET

### 💚 Daily Check (2 minutes)
```bash
# Health
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager

# Activity
tail -5 /var/log/ai-republic/constitutional_audit.log

# Alerts
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log || echo "✅ Clean"
```

### 🚨 Tribunal Alert? (DO THIS)
```bash
# Check details
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -3

# Options:
# 1. APPROVE (let system handle)
# 2. OVERRIDE (rare, false positive)
# 3. ESCALATE (oversight council)
```

### 🔧 System Down?
```bash
# Restart all
sudo systemctl restart ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Verify
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

### 📊 Quick Status
```bash
# Full health
/opt/ai-republic/monitor_constitutional_health.sh && /opt/ai-republic/phase2/monitor_judicial_health.sh

# Logs
tail -f /var/log/ai-republic/constitutional_audit.log
```

### 🎯 Key Metrics

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Compliance Rate | >99.9% | 99.0-99.9% | <99.0% |
| Response Time | <50ms | 50-200ms | >200ms |
| Tribunal Events | 0-1/day | 2-5/day | >5/day |
| Service Uptime | >99.9% | 99.0-99.9% | <99.0% |

---

## EMERGENCY CONTACTS

### System Administration
- **Primary**: system-admin@ai-republic.org
- **Backup**: devops@ai-republic.org
- **On-Call**: +1-555-0123 (24/7)

### Security Incidents
- **Security Team**: security@ai-republic.org
- **Emergency**: +1-555-0124 (24/7)
- **Escalation**: ciso@ai-republic.org

### Constitutional Oversight
- **Council Chair**: oversight-chair@ai-republic.org
- **Legal**: legal@ai-republic.org
- **Ethics**: ethics@ai-republic.org

### Federation Issues (If Applicable)
- **Federation Coordinator**: federation@ai-republic.org
- **Technical**: federation-tech@ai-republic.org

---

## FINAL NOTES

### Operational Philosophy
- **Trust the System**: It handles routine governance automatically
- **Monitor, Don't Micromanage**: Focus on trends and alerts
- **Intervene Selectively**: Only override for clear false positives
- **Document Decisions**: Log all human interventions

### Success Indicators
- **Stability**: System runs without daily intervention
- **Compliance**: High constitutional adherence rates
- **Minimal Alerts**: Few tribunal events requiring human review
- **Performance**: Consistent sub-50ms response times

### Scaling Considerations
- **Federation**: Add jurisdictions via Phase 3 FOP gateway
- **Performance**: Monitor resource usage as load increases
- **Maintenance**: Schedule grows with system complexity
- **Documentation**: Keep procedures updated with changes

---

**This document provides complete operational procedures for the AI Republic constitutional governance system. Keep it current and use it as the authoritative source for all operational decisions.**

*Version 1.0 - Effective Date: 2024-12-19* 🏛️⚖️🤖
