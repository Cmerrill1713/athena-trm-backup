# ✅ SHIP-IT CHECKLIST

**One-page verification before launch**

---

## 🚦 **GO/NO-GO GATES**

### **[ ] 1. Preflight SLA Green**
```bash
cd orchestrator
make preflight

# Expected:
# ✅ summarize OK (latency: ≤1500ms, score: ≥0.70)
# ✅ plan OK (latency: ≤1500ms, score: ≥0.70)
```

### **[ ] 2. Shadow Sanity Check**
```bash
# Edit policies.yaml temporarily:
# routing.summarize.shadow_percent: 1.0

make demo

# Check trace for "shadow_result" event
# Shadow should fire 100% of time
# Reset to 0.2 after verification
```

### **[ ] 3. Error Budget**
```bash
python3 scripts/load_test.py --requests 1000 --mode sequential

# Expected:
# ✅ Error rate ≤1%
# ✅ p95 latency ≤1500ms
```

### **[ ] 4. DMG Realism**
```bash
# On clean Mac:
cd NeuroForgeApp
make -f Makefile.dmg dmg

# Install DMG
# Run: orchestrator/preflight.sh
# Expected: All SLAs pass without Xcode
```

---

## 🔐 **SECURITY POSTURE**

### **[ ] 5. Localhost Only**
```bash
grep "127.0.0.1" orchestrator/api.py
# Should bind to localhost only
```

### **[ ] 6. Offline Lock ON**
```bash
grep "offline_only: true" orchestrator/policies.yaml
# Should be true
```

### **[ ] 7. PII Protection**
```bash
grep "pii_never_leave_local: true" orchestrator/policies.yaml
# Should be true
```

### **[ ] 8. No Egress in Traces**
```bash
sqlite3 orchestrator/state/telemetry.sqlite "
  SELECT COUNT(*) FROM traces
  WHERE raw_json LIKE '%external%' OR raw_json LIKE '%network%';
"
# Should return 0
```

---

## 🧪 **TESTING**

### **[ ] 9. Smoke Tests Pass**
```bash
cd orchestrator
make test

# Expected: 3/3 tests pass
```

### **[ ] 10. Load Test Pass**
```bash
python3 scripts/load_test.py --requests 100 --mode parallel --concurrency 10

# Expected:
# ✅ Error rate ≤1%
# ✅ p95 ≤1500ms
```

### **[ ] 11. Robustness Test Pass**
```bash
# Start API first
make api &
sleep 5

python3 scripts/robustness_test.py

# Expected:
# ✅ 100% pass rate
# ✅ 0 policy violations
```

---

## 💾 **STATE PERSISTENCE**

### **[ ] 12. Bandit State Persists**
```bash
# Check state exists
ls -la orchestrator/state/bandit.json

# Restart API
killall uvicorn
make api &
sleep 5

# Verify state loaded
cat orchestrator/state/bandit.json
# Should contain previous stats
```

### **[ ] 13. Telemetry Database Works**
```bash
sqlite3 orchestrator/state/telemetry.sqlite "SELECT count(*) FROM traces;"
# Should return >0 after tests
```

---

## 📦 **BUILD & RELEASE**

### **[ ] 14. Clean DMG Build**
```bash
cd NeuroForgeApp
make -f Makefile.dmg clean
make -f Makefile.dmg dmg

# Expected:
# ✅ DMG created
# ✅ Codesigned
# ✅ Notarized
# ✅ Stapled
```

### **[ ] 15. Checksum Generated**
```bash
shasum -a 256 NeuroForgeApp/build/NeuroForge.dmg > NeuroForgeApp/build/NeuroForge.dmg.sha256

cat NeuroForgeApp/build/NeuroForge.dmg.sha256
# Should show SHA256 hash
```

### **[ ] 16. State Snapshot**
```bash
mkdir -p releases/v$(cat VERSION)
cp orchestrator/state/bandit.json releases/v$(cat VERSION)/bandit.json
cp orchestrator/state/telemetry.sqlite releases/v$(cat VERSION)/telemetry.sqlite

ls -la releases/v$(cat VERSION)/
# Should show backups
```

---

## 📋 **DOCUMENTATION**

### **[ ] 17. Runbooks Ready**
```bash
ls -la orchestrator/RUNBOOKS.md
# Should exist

wc -l orchestrator/RUNBOOKS.md
# Should be comprehensive (>300 lines)
```

### **[ ] 18. Changelog Updated**
```bash
head -20 CHANGELOG.md
# Should show latest version with changes
```

### **[ ] 19. Release Notes**
```bash
cat > RELEASE_NOTES.md <<EOF
# NeuroForge v$(cat VERSION)

## What's New
- [List key features]

## Improvements
- [List improvements]

## Bug Fixes
- [List fixes]

## Known Issues
- [List any issues]

## Installation
1. Download NeuroForge.dmg
2. Verify: shasum -a 256 NeuroForge.dmg
3. Install and run

EOF

cat RELEASE_NOTES.md
```

---

## 🚀 **FINAL CHECKS**

### **[ ] 20. Shadow Ramped to 20%**
```yaml
# policies.yaml
routing:
  summarize:
    shadow_percent: 0.2  # ← should be 0.2
```

### **[ ] 21. Git Clean**
```bash
git status
# Should show no uncommitted changes in core files
```

### **[ ] 22. Version Tag**
```bash
git tag v$(cat VERSION)
git push origin v$(cat VERSION)
```

### **[ ] 23. GitHub Release**
```bash
# Create release on GitHub
# - Attach NeuroForge.dmg
# - Attach NeuroForge.dmg.sha256
# - Paste RELEASE_NOTES.md
# - Mark as "Latest Release"
```

---

## 🎯 **LAUNCH VERIFICATION**

### **[ ] 24. Fresh Install Test**
```bash
# On DIFFERENT Mac:
1. Download DMG from GitHub Release
2. Verify checksum
3. Install
4. Open app
5. Run preflight
6. All green? ✅ READY TO SHIP
```

---

## 📊 **SUCCESS CRITERIA**

**ALL items above must be checked before launch.**

**Expected Results:**
- ✅ All SLAs met (latency ≤1500ms, score ≥0.70)
- ✅ Error rate ≤1%
- ✅ Security posture validated
- ✅ State persists across restarts
- ✅ DMG installs and runs on clean Mac
- ✅ Runbooks printed and ready
- ✅ Release published with checksums

**If ANY check fails:** Stop, fix, re-run full checklist.

**When ALL checks pass:** 🚀 **SHIP IT!**

---

**CHECKLIST COMPLETE** ✅
**Date**: ___________
**Verified by**: ___________
**Version**: ___________
