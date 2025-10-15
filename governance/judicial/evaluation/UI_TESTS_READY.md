# NeuroForge UI Tests - READY TO RUN ✅

**Version**: v0.9.2-dev
**Commit**: 60b7bebf
**Status**: Code Complete - Permission Grant Required
**Date**: October 12, 2025

---

## ✅ WHAT'S READY

### **Source Code:**
- ✅ All Swift files compile cleanly
- ✅ SwiftPM build: SUCCESS (10.81s)
- ✅ Xcode project generated
- ✅ UI test targets configured
- ✅ All keyboard API issues fixed
- ✅ No compiler errors

### **Test Suite (11 Test Files):**
```
✅ BootAndHealthTests.swift      - App launch + health banner
✅ ChatBehaviorTests.swift        - Enter/Shift+Enter keyboard
✅ ErrorPathTests.swift           - Backend disconnect handling
✅ GoldenScreenshotTests.swift    - Visual regression (3 tests)
✅ IntegrationTests.swift         - End-to-end workflows
✅ ProviderInspectorTests.swift   - Runtime routing toggle
✅ PromptSidebarTests.swift       - Template library UI
✅ RAGTests.swift                 - RAG ingest/search
✅ VisionRAGTests.swift           - Vision + RAG integration
✅ TestHelpers.swift              - Shared utilities
✅ Golden/GoldenDiff.swift        - Pixel-diff comparison
```

### **Features Implemented:**
```
✅ Provider Inspector (⌘⌥I)
✅ Prompt Sidebar (⌘⇧T)
✅ Golden Screenshot Diffing
✅ Health Banner + Reconnect
✅ Model-Agnostic Routing
✅ Vision → RAG Integration
✅ QA Sweep (make qa)
✅ Launch Helper (run_frontend.sh)
```

---

## ⚡ **HOW TO RUN TESTS (FIRST TIME)**

### **ONE-TIME SETUP (30 seconds):**

**Step 1: Open in Xcode**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
open NeuroForgeApp.xcodeproj
```

**Step 2: Grant Permissions**
```
- Press ⌘U in Xcode
- macOS will prompt for Automation/Accessibility
- Click "OK" / "Allow" for all prompts
- Tests will run (may fail first time, that's OK)
```

**Step 3: Run from CLI (now stable)**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
make xctest

# Or directly:
xcodebuild -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -derivedDataPath DerivedData \
  test
```

---

## 🚀 **AFTER PERMISSIONS GRANTED**

### **Run Full QA Sweep:**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
make qa

# Expected output (~130s):
# 🔧 Verifying backend…
# [Services check]
# [Warmup]
# [Tests run]
# [Golden diff]
# ✅ QA SWEEP COMPLETE
```

### **Launch the App:**
```bash
bash scripts/run_frontend.sh

# App window appears with:
# - ⌘⌥I toggles Provider Inspector
# - ⌘⇧T toggles Prompt Sidebar
# - Type and chat!
```

---

## 📋 **CURRENT STATUS**

### **Build:**
```
SwiftPM:  ✅ 10.81s compile
Xcode:    ✅ Project generated
Tests:    ⏳ Permission grant needed (one-time)
```

### **Commits on v0.9.2-dev:**
```
Latest: 60b7bebf - fix(tests): keyboard API
Prev:   c67dd3a3 - feat(launch): launch helper
Total:  10 commits on v0.9.2-dev
```

### **Ready to Ship:**
```
✅ Code complete
✅ Documentation complete
✅ Guardrails active (pre-push hook)
⏳ Tests need permission grant
⏳ Final QA after permissions
```

---

## 🎯 **NEXT STEPS**

### **Immediate (5 min):**
1. Open `NeuroForgeApp.xcodeproj`
2. Press ⌘U (grant permissions)
3. Run `make qa` (verify green)

### **After Green QA:**
```bash
# Ship it
git checkout main
git merge --no-ff v0.9.2-dev -m "feat: v0.9.2"
git tag v0.9.2-green
git push && git push --tags
```

---

## 🧪 **WHAT TESTS WILL DO**

### **When You Press ⌘U:**
```
1. App launches in test mode
2. Tests verify:
   - Health banner shows
   - Chat input works
   - Enter sends, Shift+Enter newlines
   - Provider Inspector toggles
   - Prompt Sidebar toggles
   - Golden screenshots match
   - Error states display correctly

3. Results appear in Xcode Test Navigator
4. Screenshots saved to artifacts/
```

### **CLI Test Run:**
```bash
make xctest

# Outputs:
# - artifacts/NeuroForgeUI.xcresult (results bundle)
# - artifacts/xcodebuild-ui-tests.log (full log)
# - artifacts/UITestArtifacts.zip (screenshots)
```

---

## ✅ **EXPECTED RESULTS**

### **Test should compile, but may fail with "Early unexpected exit"**
**Why**: This is normal before permissions are granted
**Fix**: Run ⌘U once in Xcode (see above)

### **After Permissions:**
```
All tests: ✅ PASS (or SKIP if services not running)
Build:     ✅ SUCCESS
Time:      ~60s
Artifacts: Generated in artifacts/
```

---

## 🛠️ **TROUBLESHOOTING**

### **"Early unexpected exit"**
```
Status: EXPECTED - First run before permissions
Fix: Open Xcode, press ⌘U, grant permissions
```

### **"Cannot find 'X' in scope"**
```
Status: Should be fixed in commit 60b7bebf
Fix: If still occurring, run: xcodegen generate
```

### **"Build succeeded but tests don't run"**
```
Status: Permission issue
Fix: System Preferences → Privacy → Automation
     Add Terminal and Xcode
```

###**Tests SKIP instead of PASS**
```
Status: Backend services not running
Fix: make green (start all services)
```

---

## 📚 **DOCUMENTATION**

### **Guides:**
- `LAUNCH_GUIDE.md` - App launch troubleshooting
- `FINAL_SHIP_CHECKLIST.md` - Ship checklist
- `QA_SWEEP_GUIDE.md` - QA workflow
- `UI_TESTING_GUIDE.md` - Complete test guide
- `PERMISSIONS_SETUP.md` - macOS permissions

### **Quick Commands:**
```bash
# Build
swift build

# Run app
bash scripts/run_frontend.sh

# Run tests (after permissions)
make xctest

# Full QA
make qa

# Open in Xcode
open NeuroForgeApp.xcodeproj
```

---

## 🎉 **YOU'RE READY!**

**To run tests:**
1. `open NeuroForgeApp.xcodeproj`
2. Press ⌘U
3. Grant permissions
4. `make qa`

**To launch app:**
1. `bash scripts/run_frontend.sh`
2. Use ⌘⌥I and ⌘⇧T to test features

**To ship:**
1. Verify `make qa` is green
2. Run 3 ship commands
3. Create GitHub Release

---

**STATUS**: Ready for permission grant!
**NEXT**: Open Xcode and press ⌘U
**THEN**: make qa → ship! 🚀
