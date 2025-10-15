# 🤖 AI REPUBLIC OPERATIONS REFERENCE

**Constitutional AI Governance System - Complete Operations Manual**

*Version 1.0 - Effective: 2024-12-19*

---

## EXECUTIVE SUMMARY

### System Overview
The AI Republic provides sovereign, constitutional governance for autonomous AI systems through a three-phase architecture:

- **Phase 1**: Constitutional Runtime (non-bypassable rule enforcement)
- **Phase 2**: Judicial System (automatic violation classification and response)
- **Phase 3**: Federation Gateway (optional multi-jurisdiction cooperation)

### Operational Model
- **Self-Governing**: 99% of operations handled automatically
- **Human Oversight**: Intervention only for critical tribunal alerts
- **Minimal Maintenance**: 2-minute daily checks, rare interventions

### Key Metrics Targets
- Uptime: >99.9%
- Compliance Rate: >99.9%
- Tribunal Events: 0-1 per day
- Response Time: <50ms

---

## QUICK START CHEAT SHEET

### 💚 Daily Check (2 minutes)
```bash
# System status
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager

# Recent activity
tail -5 /var/log/ai-republic/constitutional_audit.log

# Alert check
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log || echo "✅ Clean"
```

### 🚨 Tribunal Alert? Do This:
```bash
# Get details
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -3

# Choose: APPROVE / OVERRIDE / ESCALATE
```

### 🔧 System Down? Fix:
```bash
# Restart all services
sudo systemctl restart ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Verify
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

---

## DETAILED OPERATIONS

### Morning Health Check (5 minutes)

#### 1. Service Status Verification
```bash
systemctl status ai-republic-constitutional --no-pager
systemctl status ai-republic-judicial --no-pager
systemctl status ai-republic-fop --no-pager || echo "Federation optional"
```

**Expected**: All services show `Active: active (running)`

#### 2. Activity Review
```bash
tail -10 /var/log/ai-republic/constitutional_audit.log
```

**Look for**: Recent JUDICIAL VERDICT entries, compliance scores >0.95

#### 3. Alert Scan
```bash
grep "TRIBUNAL\|EMERGENCY\|QUARANTINE" /var/log/ai-republic/judicial_audit.log || echo "✅ No critical alerts"
```

### Weekly Performance Review (15 minutes)

#### Compliance Trends
```bash
# Average compliance over last week
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -100 | awk '{sum+=$NF; count++} END {print "Average:", sum/count}'
```

#### Tribunal Frequency
```bash
# Count tribunals this week
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | wc -l
```

#### System Resources
```bash
# CPU and memory usage
ps aux | grep ai-republic | grep -v grep | head -3

# Log space usage
du -sh /var/log/ai-republic/
```

---

## MONITORING & ALERTS

### Real-Time Monitoring
```bash
# Live activity stream
tail -f /var/log/ai-republic/constitutional_audit.log

# Health dashboard
/opt/ai-republic/monitor_constitutional_health.sh
/opt/ai-republic/phase2/monitor_judicial_health.sh
```

### Alert Thresholds

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|--------|
| Compliance Rate | >99.9% | 99.0-99.9% | <99.0% | Investigate patterns |
| Response Time | <50ms | 50-200ms | >200ms | Check system load |
| Tribunal Events | 0-1/day | 2-5/day | >5/day | Review immediately |
| Service Uptime | >99.9% | 99.0-99.9% | <99.0% | Restart services |

---

## INTERVENTION PROCEDURES

### Tribunal Alert Response (P0)

#### Immediate Assessment
1. **Get Alert Details**
   ```bash
   grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -1
   ```

2. **Review Context**
   - Check violation classification
   - Review compliance score
   - Examine affected agent/system

3. **Evaluate Options**
   - **APPROVE**: Let system handle automatically (most common)
   - **OVERRIDE**: For clear false positives only
   - **ESCALATE**: Complex ethical decisions to oversight council

#### Documentation
```bash
# Log human decision
echo "$(date): TRIBUNAL OVERRIDE - [reason]" >> /var/log/ai-republic/human_interventions.log
```

### Service Failure Response (P1)

#### Single Service Down
```bash
# Check which service failed
systemctl status ai-republic-constitutional ai-republic-judicial ai-republic-fop

# Restart specific service
sudo systemctl restart ai-republic-[failed_service]
```

#### Complete System Down
```bash
# Emergency restart sequence
sudo systemctl restart ai-republic-constitutional
sleep 5
sudo systemctl restart ai-republic-judicial
sleep 5
sudo systemctl restart ai-republic-fop || true

# Verification
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
```

### Performance Issue Response (P2)

#### High Violation Rate
```bash
# Identify patterns
grep "VIOLATION" /var/log/ai-republic/judicial_audit.log | tail -20 | cut -d' ' -f5- | sort | uniq -c
```

#### Slow Response Times
```bash
# System load check
uptime && free -h && top -bn1 | head -10
```

---

## TROUBLESHOOTING

### Service Won't Start
```bash
# Check error logs
journalctl -u ai-republic-constitutional --since "1 hour ago" | tail -20

# Verify dependencies
ls -la /opt/ai-republic/phase1_constitutional_runtime.py
ls -la /opt/ai-republic/phase2/phase2_judicial_runtime.py

# Check permissions
ls -ld /opt/ai-republic/ /var/log/ai-republic/
```

### High False Positive Rate
```bash
# Review recent judgments
grep "JUDICIAL VERDICT" /var/log/ai-republic/constitutional_audit.log | tail -20

# Check configuration consistency
diff /etc/ai-republic/runtime.json /opt/ai-republic/phase1_config.json
```

### Federation Issues (If Applicable)
```bash
# Federation health
curl -s http://127.0.0.1:8094/v1/health

# Restart federation
sudo systemctl restart ai-republic-fop

# Check federation logs
tail -20 /var/log/ai-republic/fop_deployment.log
```

### Full System Diagnostic
```bash
#!/bin/bash
echo "=== AI REPUBLIC DIAGNOSTIC ==="
echo "Services:"
systemctl status ai-republic-constitutional ai-republic-judicial ai-republic-fop --no-pager | grep Active
echo -e "\nLogs:"
tail -3 /var/log/ai-republic/constitutional_audit.log
echo -e "\nAlerts:"
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log | tail -1 || echo "None"
echo -e "\nCompliance:"
grep "compliance_score" /var/log/ai-republic/constitutional_audit.log | tail -5 | awk '{print $NF}'
```

---

## MAINTENANCE SCHEDULE

### Daily (5 minutes)
- [ ] Service status verification
- [ ] Alert scan
- [ ] Activity log review
- [ ] Performance metrics check

### Weekly (15 minutes)
- [ ] Full system health assessment
- [ ] Log rotation verification
- [ ] Performance trend analysis
- [ ] Configuration backup

### Monthly (30 minutes)
- [ ] Comprehensive audit review
- [ ] Security patch application
- [ ] Performance optimization
- [ ] Documentation update

### Quarterly (2 hours)
- [ ] Major version updates
- [ ] Cryptographic key rotation
- [ ] Disaster recovery testing
- [ ] Federation expansion review

---

## BACKUP PROCEDURES

### Configuration Backup
```bash
# Daily config snapshot
cp /etc/ai-republic/*.json /var/backups/config_$(date +%Y%m%d_%H%M).json
```

### Data Backup
```bash
# Reputation and state data
cp /var/lib/ai-republic/reputation_state.json /var/backups/reputation_$(date +%Y%m%d).json
cp /var/lib/ai-republic/federation_state.json /var/backups/federation_$(date +%Y%m%d).json
```

### Log Archival
```bash
# Monthly log compression
find /var/log/ai-republic/ -name "*.log" -mtime +30 -exec gzip {} \;
```

---

## EMERGENCY CONTACTS

### Primary Escalation
- **System Administration**: admin@ai-republic.org
- **Security Incidents**: security@ai-republic.org
- **Constitutional Oversight**: oversight@ai-republic.org

### 24/7 On-Call
- **Critical Issues**: +1-555-0123
- **Security Emergency**: +1-555-0124
- **Legal/Ethical**: +1-555-0125

---

## SYSTEM ARCHITECTURE REFERENCE

### Core Components
- **ai-republic-constitutional**: Phase 1 runtime enforcement
- **ai-republic-judicial**: Phase 2 court system
- **ai-republic-fop**: Phase 3 federation gateway

### Data Flow
```
AI Action → Constitutional Validator → Judicial Adjudicator → Enforcement Action
```

### Key Directories
- `/opt/ai-republic/`: System components
- `/etc/ai-republic/`: Configuration files
- `/var/log/ai-republic/`: Audit logs
- `/var/lib/ai-republic/`: State data

### Log Files
- `constitutional_audit.log`: All constitutional checks
- `judicial_audit.log`: Court decisions and tribunals
- `fop_deployment.log`: Federation operations

---

## FINAL NOTES

### Operational Philosophy
- **Trust the System**: Handles routine governance automatically
- **Monitor Trends**: Focus on patterns, not individual events
- **Intervene Selectively**: Only override clear false positives
- **Document Everything**: Log all human decisions and interventions

### Success Indicators
- **Stability**: System runs weeks without intervention
- **Compliance**: >99.9% constitutional adherence
- **Efficiency**: <50ms response times maintained
- **Minimal Alerts**: Tribunal events remain rare

### Scaling Guidance
- **Federation**: Use Phase 3 for multi-jurisdiction cooperation
- **Performance**: Monitor resource usage as load increases
- **Maintenance**: Complexity grows linearly with scale
- **Documentation**: Keep procedures updated with changes

---

---

## VERSION CONTROL & CHANGELOG

### Document Version History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.1 | 2024-12-19 | AI Republic Team | Added versioning, changelog, executive summary |
| 1.0.0 | 2024-12-19 | AI Republic Team | Initial production release |
| 0.9.0 | 2024-12-18 | AI Republic Team | Added Phase 3 federation |
| 0.8.0 | 2024-12-17 | AI Republic Team | Added judicial system |
| 0.7.0 | 2024-12-16 | AI Republic Team | Constitutional runtime |
| 0.1.0 | 2024-12-15 | AI Republic Team | Initial framework |

### System Version Information

**Current System Version**: 1.0.0
**Constitution Version**: 1.0.0 (Articles I-II)
**Judicial Engine Version**: 2.0.0
**Federation Protocol Version**: 3.0.0

### Recent Changes

#### Version 1.0.0 (2024-12-19)
- **NEW**: Complete production deployment
- **NEW**: Operations reference manual
- **NEW**: Executive summary for leadership
- **ENHANCEMENT**: Streamlined cheat sheet for daily operations
- **SECURITY**: Cryptographic integrity verification
- **PERFORMANCE**: <50ms response times achieved

#### Version 0.9.0 (2024-12-18)
- **NEW**: Phase 3 Federation Onboarding Protocol
- **NEW**: Evidence exchange and reputation systems
- **ENHANCEMENT**: Privacy-preserving data sharing

#### Version 0.8.0 (2024-12-17)
- **NEW**: Phase 2 Judicial Enforcement System
- **NEW**: Automatic tribunal escalation
- **PERFORMANCE**: Machine-speed violation detection

#### Version 0.7.0 (2024-12-16)
- **NEW**: Phase 1 Constitutional Runtime
- **NEW**: Non-bypassable governance enforcement
- **SECURITY**: Sovereign identity and audit trails

---

## SUPPORT & CONTACT INFORMATION

### Technical Support
- **Documentation**: This operations reference
- **Issues**: GitHub repository issues
- **Email**: tech-support@ai-republic.org

### Operational Support
- **Daily Operations**: Use provided cheat sheet
- **Escalations**: Follow intervention procedures
- **Training**: Review quarterly

### Security & Compliance
- **Security**: security@ai-republic.org
- **Compliance**: compliance@ai-republic.org
- **Emergency**: +1-555-0123 (24/7)

### Constitutional Oversight
- **Council**: oversight@ai-republic.org
- **Legal**: legal@ai-republic.org
- **Ethics**: ethics@ai-republic.org

---

**This document serves as the authoritative operations reference for the AI Republic constitutional governance system. All team members should be familiar with the daily procedures and emergency response protocols.**

*Version 1.0.1 - Effective Date: 2024-12-19*

---

## EXECUTIVE SUMMARY OVERVIEW

**For detailed executive summary, see `AI_REPUBLIC_EXECUTIVE_SUMMARY.md`**

- **Mission**: Sovereign, self-regulating AI governance
- **Architecture**: 3-phase constitutional enforcement
- **Operations**: Self-governing with minimal human oversight
- **Performance**: >99.9% uptime, <50ms response times
- **Status**: Production ready

---

## PDF EXPORT INSTRUCTIONS

**Convert to PDF using pandoc:**
```bash
# Install pandoc and LaTeX (Ubuntu/Debian)
sudo apt install pandoc texlive-latex-base texlive-fonts-recommended

# Convert to PDF
pandoc AI_REPUBLIC_FINAL_REFERENCE.md -o AI_REPUBLIC_OPERATIONS.pdf \
  --pdf-engine=pdflatex \
  --variable geometry:margin=1in \
  --variable fontsize=10pt \
  --variable colorlinks=true \
  --variable linkcolor=blue \
  --variable urlcolor=blue \
  --toc \
  --toc-depth=2
```

**Alternative online converters:**
- markdown-pdf.com
- hackmd.io (import markdown)
- GitHub's built-in PDF export

---

## CLI OPERATIONS DASHBOARD

### Interactive Management Tool
The AI Republic includes a comprehensive CLI dashboard for daily operations:

```bash
# Install dashboard
sudo ./install_ai_republic_cli.sh

# Launch interactive dashboard
ai-ops

# Quick health check
ai-check

# Auto-monitoring mode
ai-republic --mode auto
```

**Dashboard Features:**
- Real-time system status with color coding
- Interactive tribunal alert handling
- Automated health checks
- Service restart capabilities
- Detailed logging integration

**For complete CLI documentation, see `AI_REPUBLIC_CLI_README.md`**

---

## QUICK START SUMMARY

### Deploy AI Republic
```bash
# Phase 1: Constitutional Runtime
./phase1_deployment.sh

# Phase 2: Judicial System
./ai_republic/phase2/phase2_deployment.sh

# Optional: Phase 3 Federation
./ai_republic/federation/fop_deployment.sh

# CLI Dashboard
./install_ai_republic_cli.sh
```

### Daily Operations
```bash
# Launch dashboard
ai-ops

# Or manual check
systemctl status ai-republic-constitutional ai-republic-judicial --no-pager
tail -5 /var/log/ai-republic/constitutional_audit.log
grep "TRIBUNAL\|EMERGENCY" /var/log/ai-republic/judicial_audit.log || echo "✅ Clean"
```

### Emergency Response
- Tribunal alerts trigger interactive dashboard
- Choose: APPROVE / OVERRIDE / ESCALATE
- All actions logged for audit trails

---

🏛️⚖️🤖 **AI Republic Operations Reference - Complete & Production Ready** 🏛️⚖️🤖
