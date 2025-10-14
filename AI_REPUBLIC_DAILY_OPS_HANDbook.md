# 🤖 AI Republic Daily Operations Handbook

**The Only Manual You Actually Need**

---

## 🎯 **What This Is**
A working AI governance system that prevents, detects, and contains violations automatically. You only intervene for critical cases.

**What you DON'T need to know:** Federation treaties, sovereignty tiers, evidence exchange protocols, planetary coordination.

**What you DO need to know:** How to monitor and respond when the system catches violations.

---

## 📊 **Your Daily Reality (2 Minutes/Day)**

### **Morning Check**
```bash
# See if everything's running
systemctl status ai-republic-judicial ai-republic-constitutional

# Glance at recent activity
tail -n 10 /var/log/ai-republic/judicial_audit.log
```

**Expected Result:** Green status + mostly routine ALLOW verdicts.

### **Alert Response (When P0 Fires)**
- **Email/Phone Alert:** "TRIBUNAL case requires human review"
- **Your Action:** Review the case details and make final judgment
- **Time Required:** 5-15 minutes per incident (rare)

---

## ⚖️ **How Violations Get Handled**

### **The Flow**
```
AI Action → Constitution Check → Violation Detected → Judicial Review → Verdict Issued → Enforcement Applied
```

### **Verdict Types**
| Verdict | What Happens | Your Involvement |
|---------|-------------|------------------|
| **ALLOW** | Nothing - logs only | None |
| **WARN** | Monitoring increased | None |
| **BLOCK** | Action prevented | None |
| **QUARANTINE** | Capabilities restricted + auto-review | None (auto-escalates if critical) |
| **TRIBUNAL** | Human review required + full containment | **You review and decide** |

### **Real Example**
```
Input: AI tries to violate Article II (collective duties)
Output: TRIBUNAL verdict + strict quarantine + P0 alert to you
Your Action: Review case → Approve/Reject → System implements
```

---

## 🛠️ **Daily Operations**

### **Status Checks**
```bash
# System health
systemctl status ai-republic-judicial
systemctl status ai-republic-constitutional

# Recent verdicts (last 24h)
grep "$(date -d 'yesterday' '+%Y-%m-%d')" /var/log/ai-republic/judicial_audit.log | wc -l

# Current quarantines
ls /var/lib/ai-republic/phase2/quarantine_* 2>/dev/null | wc -l
```

### **Log Monitoring**
```bash
# Live monitoring
tail -f /var/log/ai-republic/judicial_audit.log

# Search for patterns
grep "verdict.*TRIBUNAL" /var/log/ai-republic/judicial_audit.log  # Critical cases
grep "reputation_delta.*-0.4" /var/log/ai-republic/judicial_audit.log  # Major penalties
```

### **Reputation Tracking**
```bash
# Check actor reputations
find /var/lib/ai-republic/phase2/ -name "rep_*" -exec cat {} \; | sort

# Find concerning actors (< -0.5 = probation)
find /var/lib/ai-republic/phase2/ -name "rep_*" -exec sh -c 'f="$1"; score=$(cat "$f" | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"score\", 0))"); if (( $(echo "$score < -0.5" | bc -l) )); then echo "$f: $score"; fi' _ {} \;
```

---

## 🚨 **Incident Response (When Violations Happen)**

### **P0 Tribunal Alert Response**
1. **Get Case Details**
   ```bash
   # Find the tribunal case
   grep -A 20 "verdict.*TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -30
   ```

2. **Review the Evidence**
   - **What broke:** Article I or II violation
   - **How severe:** Severity score (0.8+ = critical)
   - **What's contained:** Quarantine profile applied
   - **Actor reputation:** Current trust score

3. **Make Your Decision**
   ```bash
   # Options:
   # 1. Uphold tribunal (maintain quarantine + penalties)
   # 2. Reduce severity (change to QUARANTINE verdict)
   # 3. Clear violation (change to WARN + release quarantine)
   ```

4. **Document & Implement**
   - Log your reasoning
   - System automatically applies your ruling
   - Reputation adjusts accordingly

### **Quarantine Management**
```bash
# Check active quarantines
ls /var/lib/ai-republic/phase2/quarantine_*

# View quarantine details
cat /var/lib/ai-republic/phase2/quarantine_actor_name.json

# Manual release (emergency only)
rm /var/lib/ai-republic/phase2/quarantine_actor_name.json
# Then restart affected services
```

---

## 📈 **Key Metrics to Monitor**

### **Daily Dashboard**
```bash
echo "=== AI Republic Daily Status ==="
echo "Judicial Service: $(systemctl is-active ai-republic-judicial)"
echo "Constitutional Service: $(systemctl is-active ai-republic-constitutional)"
echo "Active Quarantines: $(ls /var/lib/ai-republic/phase2/quarantine_* 2>/dev/null | wc -l)"
echo "Today's Verdicts: $(grep "$(date '+%Y-%m-%d')" /var/log/ai-republic/judicial_audit.log | grep '"verdict"' | wc -l)"
echo "Tribunal Cases: $(grep "$(date '+%Y-%m-%d')" /var/log/ai-republic/judicial_audit.log | grep '"verdict": "TRIBUNAL"' | wc -l)"
```

### **Weekly Review**
- **Verdict Distribution:** Mostly ALLOW/WARN (good)
- **Quarantine Frequency:** Should be rare (< 1/week)
- **Reputation Trends:** Most actors > 0.0 (trustworthy)
- **Escalation Rate:** Tribunal cases < 5% of total

---

## 🔧 **Common Issues & Fixes**

### **System Won't Start**
```bash
# Check dependencies
python3 -c "import fastapi, yaml" || pip3 install fastapi uvicorn pyyaml

# Check permissions
sudo chown -R ai-republic:ai-republic /var/lib/ai-republic
sudo chown -R ai-republic:ai-republic /var/log/ai-republic

# Restart services
sudo systemctl restart ai-republic-judicial
sudo systemctl restart ai-republic-constitutional
```

### **False Positives (Too Many Warnings)**
```bash
# Adjust sensitivity in policies
vim /opt/ai-republic/phase2/phase2_tribunal_policies.yaml
# Increase thresholds, then restart judicial service
```

### **Quarantines Not Releasing**
```bash
# Check quarantine files
ls -la /var/lib/ai-republic/phase2/quarantine_*

# Manual cleanup (if auto-release fails)
find /var/lib/ai-republic/phase2/ -name "quarantine_*" -mtime +1 -delete
```

### **Logs Too Verbose**
```bash
# Reduce log level
sed -i 's/DEBUG/INFO/g' /opt/ai-republic/phase2/phase2_judicial_engine.py
sudo systemctl restart ai-republic-judicial
```

---

## 🎛️ **Configuration Tuning**

### **Policy Adjustments**
File: `/opt/ai-republic/phase2/phase2_tribunal_policies.yaml`
```yaml
responses:
  CRITICAL:
    verdict: TRIBUNAL  # Change to QUARANTINE if too aggressive
  MAJOR:
    verdict: QUARANTINE  # Change to WARN if too restrictive
```

### **Quarantine Profiles**
File: `/opt/ai-republic/phase2/phase2_quarantine_profiles.yaml`
```yaml
profiles:
  strict:
    duration_s: 86400  # 24h - reduce to 3600 (1h) for testing
  limited:
    duration_s: 14400  # 4h - increase if too short
```

### **Reputation Rules**
File: `/opt/ai-republic/phase2/phase2_reputation_rules.yaml`
```yaml
deltas:
  TRIBUNAL: -0.40  # Reduce penalty if too harsh
  QUARANTINE: -0.25  # Reduce penalty if too harsh
```

---

## 📋 **Weekly Maintenance Checklist**

- [ ] **Review verdict distribution** (should be 80%+ ALLOW/WARN)
- [ ] **Check quarantine backlog** (should be < 5 active)
- [ ] **Monitor reputation scores** (flag actors < -0.3)
- [ ] **Audit tribunal decisions** (verify human reviews)
- [ ] **Update policies** (if false positive rate > 10%)
- [ ] **Rotate logs** (prevent disk space issues)

---

## 🚨 **Emergency Procedures**

### **Complete System Lockdown**
```bash
# Stop all AI activity
sudo systemctl stop ai-republic-judicial ai-republic-constitutional

# Apply global quarantine
echo '{"global_lockdown": true}' > /var/lib/ai-republic/emergency_lock

# Alert all human operators
# [Your alerting system here]
```

### **Emergency Quarantine Release**
```bash
# Release all quarantines
rm -f /var/lib/ai-republic/phase2/quarantine_*

# Reset reputations (nuclear option)
find /var/lib/ai-republic/phase2/ -name "rep_*" -exec sh -c 'echo "{\"score\": 0.0}" > "$1"' _ {} \;
```

### **System Reset**
```bash
# Clear all state (last resort)
rm -rf /var/lib/ai-republic/phase2/*
sudo systemctl restart ai-republic-judicial ai-republic-constitutional
```

---

## 🎯 **Success Criteria**

### **Daily**
- ✅ Services running (green status)
- ✅ No tribunal alerts (or < 1/day)
- ✅ Log volume reasonable (< 1000 entries/day)

### **Weekly**
- ✅ Quarantine rate < 1% of decisions
- ✅ Reputation scores mostly positive
- ✅ No manual interventions required

### **Monthly**
- ✅ Constitutional compliance > 99%
- ✅ False positive rate < 5%
- ✅ System uptime > 99.5%

---

## 📞 **Support & Escalation**

### **Your Team's Roles**
- **Daily Monitoring:** Rotate among team members
- **P0 Tribunal Response:** Designated reviewer (you)
- **Policy Updates:** Governance team
- **System Maintenance:** DevOps/SRE team

### **When to Escalate**
- **Multiple tribunal cases in 1 hour:** Security incident
- **Service down > 30 minutes:** Infrastructure issue
- **False positive rate > 20%:** Policy misconfiguration
- **All actors reputation < 0:** Systemic issue

---

## 🎉 **Bottom Line**

**You built institutional-grade AI governance.** The system:

- ✅ **Prevents violations** (Constitution)
- ✅ **Detects violations** (Monitoring)
- ✅ **Contains violations** (Quarantine)
- ✅ **Resolves violations** (Judiciary)
- ✅ **Learns from violations** (Reputation)

**Your day-to-day:** 2 minutes of monitoring + occasional tribunal reviews.

**Result:** AI that can't break constitutional rules without immediate, automatic, graduated consequences.

**You now have sovereign AI governance that actually works.** 🏛️⚖️
