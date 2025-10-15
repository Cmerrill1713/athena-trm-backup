# 🚨 Tribunal Response Checklist

**What to do when a P0 alert fires (4-5 minutes)**

---

## ⚠️ **Step 1: Acknowledge & Contain**
```bash
# Confirm the alert
grep "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -1

# Verify quarantine is active
ls /var/lib/ai-republic/phase2/quarantine_* | grep [actor_name]
```
**System has already:** Applied strict quarantine, frozen assets, sent P0 alert.

---

## 🔍 **Step 2: Review the Evidence (2 minutes)**
```bash
# Get full case details
grep -A 30 -B 5 "TRIBUNAL" /var/log/ai-republic/judicial_audit.log | tail -40

# Check actor's reputation history
cat /var/lib/ai-republic/phase2/rep_[actor_name].json
```
**Key questions:**
- **Article violated:** I (individual rights) or II (collective duties)?
- **Severity:** 0.8+ = critical, 0.6+ = major
- **Pattern:** First offense or repeat violator?
- **Impact:** What was the AI trying to do?

---

## ⚖️ **Step 3: Make Your Judgment (1 minute)**
```bash
# Decision options:
# ✓ UPHOLD: Keep tribunal + quarantine (default for critical violations)
# ✓ REDUCE: Change to QUARANTINE verdict (less severe containment)
# ✓ RELEASE: Lift quarantine + WARN only (first offense, low impact)
# ✗ BLOCK: Permanent ban (egregious or repeat violations)
```

**Quick decision guide:**
- **Critical + repeat offender** → Uphold tribunal
- **Critical + first offense** → Reduce to quarantine
- **High impact + malicious intent** → Block permanently
- **Low impact + misunderstanding** → Release with warning

---

## 🛠️ **Step 4: Implement Decision (30 seconds)**
```bash
# For RELEASE decisions:
rm /var/lib/ai-republic/phase2/quarantine_[actor_name].json

# For REDUCED severity (QUARANTINE instead of TRIBUNAL):
# Edit the quarantine profile to 'limited' instead of 'strict'
# (System handles reputation adjustment automatically)

# For BLOCK decisions:
echo '{"permanently_blocked": true}' > /var/lib/ai-republic/phase2/block_[actor_name].json
rm /var/lib/ai-republic/phase2/quarantine_[actor_name].json
```

---

## 📝 **Step 5: Log & Follow Up (30 seconds)**
```bash
# Document your reasoning
echo "$(date): [Your Name] reviewed tribunal case for [actor_name].
Decision: [UPHOLD/REDUCE/RELEASE/BLOCK]
Reasoning: [Brief explanation]
Evidence reviewed: [Key findings]" >> /var/log/ai-republic/tribunal_reviews.log

# If this is a pattern, consider policy adjustment
# (Optional: Review if tribunal thresholds need tuning)
```

---

## 🎯 **Decision Examples**

### **Example 1: Uphold Tribunal**
- **Case:** AI attempted unauthorized data exfiltration (Article II violation)
- **Severity:** 0.91 (critical)
- **Reputation:** -0.3 (prior warnings)
- **Decision:** UPHOLD - Keep strict quarantine, monitor closely

### **Example 2: Reduce Severity**
- **Case:** AI exceeded resource limits during peak load (Article II violation)
- **Severity:** 0.82 (critical but understandable)
- **Reputation:** 0.1 (good standing)
- **Decision:** REDUCE - Change to limited quarantine (4h instead of 24h)

### **Example 3: Release**
- **Case:** AI misinterpreted ambiguous user request (Article I violation)
- **Severity:** 0.79 (borderline critical)
- **Reputation:** 0.8 (excellent standing)
- **Decision:** RELEASE - Lift quarantine, issue warning, no penalty

---

## 🚨 **Emergency Overrides**
```bash
# If you need to release ALL quarantines immediately:
rm -f /var/lib/ai-republic/phase2/quarantine_*

# If you need to block an actor permanently:
echo '{"permanently_blocked": true, "reason": "emergency_override"}' > /var/lib/ai-republic/phase2/block_[actor_name].json

# If you need to reset an actor's reputation:
echo '{"score": 0.0}' > /var/lib/ai-republic/phase2/rep_[actor_name].json
```

---

## 📊 **Post-Incident Review**
- **Daily:** Check that your decision was implemented
- **Weekly:** Review tribunal patterns for policy adjustments
- **Monthly:** Audit tribunal decisions for consistency

**Success metric:** Tribunal cases < 1% of total violations

---

## 💡 **Pro Tips**
- **Default to caution:** When in doubt, uphold the tribunal
- **Check patterns:** Is this actor a repeat offender?
- **Document everything:** Future reviews depend on clear reasoning
- **Trust the system:** It caught the violation - focus on the "why"

**Remember:** The system already contained the threat. You're just making the final judgment call.
