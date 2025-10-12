# NeuroForge E2E Validation Guide

**Purpose**: Validate complete frontend → backend integration before DMG build
**Time**: 5 minutes
**Critical**: Run this BEFORE distributing DMG

---

## 🎯 **WHY THIS MATTERS**

Before building a production DMG, we **must** verify:
- ✅ Frontend can reach backend
- ✅ All API endpoints respond
- ✅ Provider routing works
- ✅ RAG integration functional
- ✅ Vision pipeline operational
- ✅ Environment variables propagate correctly

**Without this:** DMG builds successfully but app doesn't work! ❌

---

## 🚀 **VALIDATION SEQUENCE**

### **1. Smoke Test (Infrastructure)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
bash scripts/smoke_test.sh
```

**Tests:**
- Backend service health (6 services)
- API endpoint availability
- Swift build verification
- Xcode project validation
- DMG prerequisites
- Configuration files
- Environment setup

**Expected:** `🎉 ALL SYSTEMS GO!`

---

### **2. E2E Integration Test (API)**

```bash
bash scripts/e2e_validation.sh
```

**Tests:**
- Basic chat endpoint
- Provider override headers (auto/fastvlm/ollama/trm)
- RAG search functionality
- Vision endpoint availability
- Router health probes
- Frontend build artifacts
- Network round-trip latency

**Expected:** `🎉 E2E VALIDATION PASSED!`

---

### **3. Manual Frontend Test (30s)**

```bash
bash scripts/run_frontend.sh
```

**Verify:**
- [ ] App window appears
- [ ] Health banner shows "Connected" (green)
- [ ] Type "ping" → Get response
- [ ] Press ⌘⌥I → Provider Inspector appears
- [ ] Press ⌘⇧T → Prompt Sidebar appears
- [ ] Select FastVLM → ACTIVE tag shows
- [ ] Console shows: `[APIClient] POST /api/chat ...`

---

### **4. DMG Build Validation (After DMG Created)**

```bash
# After: make -f Makefile.dmg dmg
bash scripts/validate_dmg_build.sh
```

**Tests:**
- DMG file exists and is readable
- App bundle structure valid
- Code signature verification
- Entitlements embedded correctly
- Notarization ticket stapled
- Gatekeeper assessment
- DMG mountable
- Applications symlink present
- Runtime launch test

**Expected:** `🎉 DMG VALIDATION PASSED!`

---

## 📋 **COMPLETE VALIDATION WORKFLOW**

### **Before DMG Build:**

```bash
cd ~/Documents/GitHub/NeuroForgeApp

# 1. Infrastructure check
bash scripts/smoke_test.sh
# Should exit 0 with "ALL SYSTEMS GO"

# 2. API integration check
bash scripts/e2e_validation.sh
# Should exit 0 with "E2E VALIDATION PASSED"

# 3. Manual frontend smoke test
bash scripts/run_frontend.sh
# Verify UI features work

# 4. Full UI test suite (after permission grant)
make xctest
# All tests should pass or skip gracefully
```

### **After DMG Build:**

```bash
# Build DMG
make -f Makefile.dmg dmg

# Validate DMG
bash scripts/validate_dmg_build.sh
# Should exit 0 with "DMG VALIDATION PASSED"

# Manual install test
open build-dmg/NeuroForgeApp.dmg
# Drag to Applications, launch, verify features
```

---

## 🛠️ **TROUBLESHOOTING**

### **Smoke Test Failures:**

**"Main API (8014) - Not responding"**
```bash
cd ~/Documents/GitHub
make green
```

**"SwiftPM debug build - Compilation errors"**
```bash
swift build 2>&1 | grep error
# Fix errors and retry
```

**"UI test target missing"**
```bash
xcodegen generate
```

---

### **E2E Test Failures:**

**"Chat endpoint failed"**
```bash
# Test directly
curl -sf -X POST http://localhost:8014/api/chat \
  -H "Content-Type: application/json" \
  -d '{"kind":"smalltalk","text":"test"}'

# If fails, check backend logs
```

**"Provider override not responding"**
```bash
# Check if provider service is running
curl -sf http://localhost:8811/health  # FastVLM
curl -sf http://localhost:11434/api/version  # Ollama
```

**"RAG search not available"**
```bash
# Check Weaviate
curl -sf http://localhost:8090/v1/meta

# Seed KB if needed
make weaviate-seed
```

---

### **DMG Validation Failures:**

**"Signature verification failed"**
```bash
# Re-sign
make -f Makefile.dmg sign verify
```

**"No stapled ticket"**
```bash
# Re-notarize and staple
make -f Makefile.dmg notarize staple
```

**"App crashed on launch"**
```bash
# Check launch log
cat /tmp/neuroforge_launch.log

# Common issues:
# - Missing entitlements (network access)
# - Backend not running
# - Invalid Info.plist
```

---

## ✅ **VALIDATION MATRIX**

| **Phase** | **Script** | **Duration** | **Critical** |
|-----------|-----------|--------------|--------------|
| Smoke Test | `smoke_test.sh` | 30s | ✅ Yes |
| E2E Integration | `e2e_validation.sh` | 60s | ✅ Yes |
| Manual UI Test | `run_frontend.sh` | 30s | ✅ Yes |
| DMG Validation | `validate_dmg_build.sh` | 30s | ✅ Yes |
| Full UI Tests | `make xctest` | 60s | ⚠️  After permissions |

**Total Pre-DMG Time:** ~3 minutes
**Total Post-DMG Time:** ~1 minute

---

## 🎯 **RECOMMENDED WORKFLOW**

### **Development Cycle:**
```bash
# 1. Make changes to code
# 2. Run smoke test
bash scripts/smoke_test.sh

# 3. Run E2E validation
bash scripts/e2e_validation.sh

# 4. Test UI manually
bash scripts/run_frontend.sh

# 5. Run full test suite
make xctest

# 6. Commit and push (pre-push hook runs qa)
git commit -m "feat: new feature"
git push
```

### **DMG Build Cycle:**
```bash
# 1. Validate integration
bash scripts/smoke_test.sh
bash scripts/e2e_validation.sh

# 2. Build DMG
make -f Makefile.dmg dmg

# 3. Validate DMG
bash scripts/validate_dmg_build.sh

# 4. Manual install test
open build-dmg/NeuroForgeApp.dmg

# 5. Upload to GitHub Release
```

---

## 🚀 **READY TO VALIDATE**

Run the complete pre-DMG validation:

```bash
cd ~/Documents/GitHub/NeuroForgeApp

echo "Running complete validation suite..."
bash scripts/smoke_test.sh && \
bash scripts/e2e_validation.sh && \
echo "" && \
echo "🎉 VALIDATION COMPLETE - READY FOR DMG BUILD!"
```

**If all pass:** You're ready for `make -f Makefile.dmg dmg`! 🚀

---

**E2E VALIDATION SYSTEM COMPLETE** ✅
**Scripts**: 3 comprehensive validators
**Coverage**: Infrastructure + Integration + Build
**Next**: Run validation, then build DMG! 🔥
