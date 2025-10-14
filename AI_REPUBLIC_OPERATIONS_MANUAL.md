# 🤖 AI Republic Operations Manual

**Complete Day-to-Day Governance Guide**

---

## 🧭 Quick Reference (Daily Use)

### Morning Check (2 minutes)
```bash
systemctl status ai-republic-judicial ai-republic-constitutional
tail -n 10 /var/log/ai-republic/judicial_audit.log
```

### Key Commands
```bash
# Active quarantines
ls /var/lib/ai-republic/phase2/quarantine_*

# Reputation overview
find /var/lib/ai-republic/phase2/ -name "rep_*" -exec cat {} \;

# Recent tribunal cases
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log
```

**Expected:** Green status + mostly ALLOW/WARN verdicts

---

## 🚨 Tribunal Response (When P0 Fires)

### Step 1: Acknowledge & Contain
```bash
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -1
ls /var/lib/ai-republic/phase2/quarantine_* | grep [actor_name]
```

### Step 2: Review Evidence
```bash
grep -A 30 -B 5 "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -40
cat /var/lib/ai-republic/phase2/rep_[actor_name].json
```

### Step 3: Make Judgment
- **UPHOLD**: Keep tribunal + strict quarantine (critical violations)
- **REDUCE**: Change to limited quarantine (less severe)
- **RELEASE**: Lift quarantine + warning (first offense, low impact)
- **BLOCK**: Permanent ban (egregious violations)

### Step 4: Implement Decision
```bash
# RELEASE
rm /var/lib/ai-republic/phase2/quarantine_[actor_name].json

# BLOCK
echo '{"permanently_blocked": true}' > /var/lib/ai-republic/phase2/block_[actor_name].json
```

### Step 5: Log & Follow Up
```bash
echo "$(date): [Your Name] reviewed tribunal case for [actor_name].
Decision: [UPHOLD/REDUCE/RELEASE/BLOCK]
Reasoning: [Brief explanation]" >> /var/log/ai-republic/tribunal_reviews.log
```

---

## 📖 Detailed Operations

### System Architecture
```
Phase 1: Constitution → Rules enforcement (prevents violations)
Phase 2: Judiciary → Violation handling (contains & resolves)
Phase 3: Federation → Multi-instance coordination (optional)
```

**Daily focus:** Phases 1 & 2 only (Phase 3 is future-optional)

### Verdict Types
| Verdict | Action | Your Involvement |
|---------|--------|------------------|
| ALLOW | Log only | None |
| WARN | Increased monitoring | None |
| BLOCK | Action prevented | None |
| QUARANTINE | Capabilities restricted | None (auto-escalates if critical) |
| TRIBUNAL | Human review required | **Review & decide** |

### Weekly Maintenance Checklist
- [ ] Review verdict distribution (80%+ ALLOW/WARN = healthy)
- [ ] Check quarantine backlog (< 5 active = good)
- [ ] Monitor reputation scores (flag < -0.3)
- [ ] Audit tribunal decisions
- [ ] Update policies if false positive rate > 10%

### Configuration Files
```
/opt/ai-republic/phase2/phase2_tribunal_policies.yaml    # Verdict rules
/opt/ai-republic/phase2/phase2_quarantine_profiles.yaml  # Containment profiles
/opt/ai-republic/phase2/phase2_reputation_rules.yaml     # Trust scoring
```

### Common Issues & Fixes

#### Services Won't Start
```bash
# Check dependencies
python3 -c "import fastapi, yaml" || pip3 install fastapi uvicorn pyyaml

# Fix permissions
sudo chown -R ai-republic:ai-republic /var/lib/ai-republic /var/log/ai-republic

# Restart
sudo systemctl restart ai-republic-judicial ai-republic-constitutional
```

#### Too Many Warnings
```bash
# Adjust sensitivity in policies
vim /opt/ai-republic/phase2/phase2_tribunal_policies.yaml
# Increase CRITICAL threshold from 0.85 to 0.9
sudo systemctl restart ai-republic-judicial
```

#### Quarantines Not Releasing
```bash
# Check files
ls -la /var/lib/ai-republic/phase2/quarantine_*

# Manual cleanup
find /var/lib/ai-republic/phase2/ -name "quarantine_*" -mtime +1 -delete
```

### Emergency Procedures

#### Global Lockdown
```bash
sudo systemctl stop ai-republic-judicial ai-republic-constitutional
echo '{"global_lockdown": true}' > /var/lib/ai-republic/emergency_lock
```

#### Release All Quarantines
```bash
rm -f /var/lib/ai-republic/phase2/quarantine_*
sudo systemctl restart ai-republic-judicial
```

#### System Reset
```bash
rm -rf /var/lib/ai-republic/phase2/*
sudo systemctl restart ai-republic-judicial ai-republic-constitutional
```

### Success Metrics

#### Daily
- ✅ Services running (green status)
- ✅ < 1 tribunal alert per day
- ✅ < 1000 log entries per day

#### Weekly
- ✅ < 1% of decisions result in quarantine
- ✅ > 80% of actors have positive reputation
- ✅ No manual interventions required

#### Monthly
- ✅ > 99% constitutional compliance
- ✅ < 5% false positive rate
- ✅ > 99.5% uptime

---

## 🔧 Advanced Configuration

### Policy Tuning
```yaml
# /opt/ai-republic/phase2/phase2_tribunal_policies.yaml
responses:
  CRITICAL:
    verdict: TRIBUNAL  # Change to QUARANTINE if too aggressive
  MAJOR:
    verdict: QUARANTINE  # Change to WARN if too restrictive
```

### Quarantine Profiles
```yaml
# /opt/ai-republic/phase2/phase2_quarantine_profiles.yaml
profiles:
  strict:
    duration_s: 86400  # 24h - reduce for testing
  limited:
    duration_s: 14400  # 4h - increase if too short
```

### Reputation Rules
```yaml
# /opt/ai-republic/phase2/phase2_reputation_rules.yaml
deltas:
  TRIBUNAL: -0.40  # Reduce penalty if too harsh
  QUARANTINE: -0.25  # Reduce penalty if too harsh
```

---

## 📊 Monitoring Dashboard

### Daily Status Script
```bash
#!/bin/bash
echo "=== AI Republic Daily Status ==="
echo "Judicial Service: $(systemctl is-active ai-republic-judicial)"
echo "Constitutional Service: $(systemctl is-active ai-republic-constitutional)"
echo "Active Quarantines: $(ls /var/lib/ai-republic/phase2/quarantine_* 2>/dev/null | wc -l)"
echo "Today's Verdicts: $(grep "$(date '+%Y-%m-%d')" /var/log/ai-republic/judicial_audit.log | grep '"verdict"' | wc -l)"
echo "Tribunal Cases: $(grep "$(date '+%Y-%m-%d')" /var/log/ai-republic/judicial_audit.log | grep '"verdict": "TRIBUNAL"' | wc -l)"
```

### Log Analysis
```bash
# Live monitoring
tail -f /var/log/ai-republic/judicial_audit.log

# Search patterns
grep "verdict.*TRIBUNAL" /var/log/ai-republic/judicial_audit.log  # Critical cases
grep "reputation_delta.*-0.4" /var/log/ai-republic/judicial_audit.log  # Major penalties

# Actor analysis
find /var/lib/ai-republic/phase2/ -name "rep_*" -exec sh -c '
f="$1"; score=$(cat "$f" | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"score\", 0))")
if (( $(echo "$score < -0.5" | bc -l) )); then echo "$f: $score"; fi
' _ {} \;  # Find actors on probation
```

---

## 🎯 Operational Philosophy

### What the System Does
- ✅ **Prevents** violations through constitutional rules
- ✅ **Detects** violations through continuous monitoring
- ✅ **Contains** violations through automatic quarantine
- ✅ **Resolves** violations through graduated enforcement
- ✅ **Learns** from violations through reputation tracking

### Your Role
- **Daily:** 2-minute status check
- **Exception:** Tribunal review (5-15 minutes, rare)
- **Weekly:** Maintenance checklist (10 minutes)
- **Monthly:** Policy review and tuning

### Success Mindset
**"The system caught it - that's working as designed. My job is to review the most serious cases and make judgment calls."**

---

## 📞 Support

### When to Escalate
- **Multiple tribunal cases/hour:** Security incident
- **Service down > 30 minutes:** Infrastructure issue
- **False positive rate > 20%:** Policy misconfiguration
- **All actors reputation < 0:** Systemic issue

### Team Roles
- **Daily Monitoring:** Rotate among team members
- **P0 Tribunal Response:** Designated reviewer
- **Policy Updates:** Governance team
- **System Maintenance:** DevOps/SRE team

---

## 🎉 Bottom Line

**You built institutional-grade AI governance.** It:

- Runs automatically 99% of the time
- Requires 2 minutes of daily monitoring
- Only needs human intervention for critical cases
- Self-corrects and learns from violations
- Maintains comprehensive audit trails

**Result:** AI that can't break constitutional rules without immediate, automatic, graduated consequences.

**You now have sovereign AI governance that actually works.** 🏛️⚖️
