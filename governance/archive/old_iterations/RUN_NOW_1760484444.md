# NeuroForge - RUN NOW Guide 🚀

**Purpose**: Get Swift UI tests running + launch the frontend in 5 minutes
**Date**: October 12, 2025
**Version**: v0.9.2-dev

---

## ⚡ **FASTEST PATH TO RUNNING**

### **Step 1: Grant Permissions (ONE TIME - 60 seconds)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
open NeuroForgeApp.xcodeproj
```

**In Xcode:**
1. Press `⌘U` (Run Tests)
2. Click "Allow" on Automation/Accessibility prompts
3. Edit Scheme → Test → Environment Variables:
   - `API_BASE` = `http://localhost:8014`
   - `QA_MODE` = `1`
4. Close Xcode

**Why**: macOS blocks UI testing until you grant permissions once

---

### **Step 2: Start Backend Services (30 seconds)**

```bash
cd ~/Documents/GitHub
make green

# Expected:
# ✅ chat
# ✅ tts
# ✅ k1, k2, k3
# ✅ weaviate
```

```bash
~/Documents/GitHub/NeuroForgeApp/scripts/warmup_services.sh || true

# Expected:
# 🔧 Warming up NeuroForge services...
# ✅ Main API, TTS, FastVLM, Weaviate
```

---

### **Step 3: Run UI Tests (PROOF + ARTIFACTS)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
rm -rf artifacts DerivedData
mkdir -p artifacts

xcodebuild \
  -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -derivedDataPath DerivedData \
  -resultBundlePath artifacts/NeuroForgeUI.xcresult \
  test | tee artifacts/xcodebuild-ui-tests.log
```

**What You'll See:**
```
Building for testing...
Build succeeded.

Testing started
Test Suite 'All tests' started...
  BootAndHealthTests
  ChatBehaviorTests
  ErrorPathTests
  GoldenScreenshotTests
  IntegrationTests
  ProviderInspectorTests
  PromptSidebarTests
  RAGTests
  VisionRAGTests

** TEST SUCCEEDED **
```

---

### **Step 4: Verify Artifacts**

```bash
# Check test results
tail -100 artifacts/xcodebuild-ui-tests.log | grep "TEST"

# Open results bundle in Xcode
open artifacts/NeuroForgeUI.xcresult

# List artifacts
ls -lh artifacts/
```

**Expected Files:**
```
artifacts/
├── NeuroForgeUI.xcresult/     # Full test results
├── xcodebuild-ui-tests.log    # Complete log
└── UITestArtifacts.zip        # Screenshots + logs (if created)
```

---

### **Step 5: Launch the Frontend**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh
```

**Expected:**
```
🔨 Building NeuroForge...
[1/26] Compiling...
Build complete! (10.81s)

🚀 Launching NeuroForge...
   API_BASE: http://localhost:8014
   QA_MODE: 1

[App window appears]
```

**Test Features:**
- Press `⌘⌥I` → Provider Inspector
- Press `⌘⇧T` → Prompt Sidebar
- Type "ping" → Get response
- Check console logs

---

## 🧪 **ONE-COMMAND QA (After First Run)**

```bash
make -C ~/Documents/GitHub/NeuroForgeApp qa

# Full sweep (~130s):
# ✅ Clean
# ✅ Health check
# ✅ Warmup
# ✅ UI tests
# ✅ Golden diff
# ✅ Artifacts
```

---

## 🛠️ **COMMON FIXES**

### **"Early unexpected exit"**
```
Status: EXPECTED before permissions granted
Fix:
1. open NeuroForgeApp.xcodeproj
2. Press ⌘U
3. Click "Allow" on prompts
4. Try again
```

### **"No tests found" / "Build uses old project"**
```bash
cd ~/Documents/GitHub/NeuroForgeApp
xcodegen generate
xcodebuild -project NeuroForgeApp.xcodeproj -list
# Re-run step 3
```

### **"Cannot find 'PromptStore'"**
```bash
# Verify files exist
ls -la Sources/Prompts/

# Regenerate project
xcodegen generate

# Clean and rebuild
rm -rf DerivedData .build
swift build
```

### **Backend not responding**
```bash
# Check services
cd ~/Documents/GitHub
make green

# If down, restart:
make start-all  # or start individual services
```

### **Permission issues after granting**
```
System Settings → Privacy & Security → Automation
Enable:
- Xcode
- Xcode Helper
- Terminal

Then re-run tests
```

---

## 📊 **WHAT TO LOOK FOR**

### **In xcodebuild-ui-tests.log:**
```bash
tail -100 artifacts/xcodebuild-ui-tests.log

# Look for:
** TEST SUCCEEDED **  ✅
# or
** TEST FAILED **     ❌

# Test counts:
Test Suite 'All tests' passed at...
Executed XX tests, with 0 failures (0 unexpected)
```

### **In Xcode Results (open artifacts/NeuroForgeUI.xcresult):**
- Green checkmarks = PASS ✅
- Red X = FAIL ❌
- Gray dash = SKIPPED (OK if services not running)
- Screenshots attached to tests

### **In Console (when app runs):**
```
[ProviderInspector] override=fastvlm source=client...
[APIClient] POST /api/chat hdr:X-Provider-Override=fastvlm rtt=142ms code=200
```

---

## ✅ **SUCCESS CHECKLIST**

After running all steps above:

- [ ] Xcode permissions granted (step 1)
- [ ] Backend services green (step 2)
- [ ] UI tests ran from CLI (step 3)
- [ ] Saw "** TEST SUCCEEDED **" in log
- [ ] artifacts/NeuroForgeUI.xcresult exists
- [ ] App window launched (step 5)
- [ ] Provider Inspector works (⌘⌥I)
- [ ] Prompt Sidebar works (⌘⇧T)
- [ ] Chat responds to "ping"

---

## 🚀 **NEXT: SHIP IT**

### **After Tests Pass:**
```bash
# Full QA sweep
make -C ~/Documents/GitHub/NeuroForgeApp qa

# Should show:
# ✅ QA SWEEP COMPLETE - ALL GREEN
```

### **Ship to Main:**
```bash
cd ~/Documents/GitHub

git checkout main
git merge --no-ff v0.9.2-dev -m "feat: v0.9.2 (Provider Inspector, Golden Diff, Prompt Sidebar, QA Sweep)"
git tag v0.9.2-green
git push && git push --tags
```

---

## 📚 **HELPFUL DOCS**

- `LAUNCH_GUIDE.md` - Launch troubleshooting
- `UI_TESTS_READY.md` - Test guide
- `FINAL_SHIP_CHECKLIST.md` - Ship checklist
- `QA_SWEEP_GUIDE.md` - QA workflow

---

## 🎯 **START HERE**

```bash
# 1. Grant permissions (one-time)
cd ~/Documents/GitHub/NeuroForgeApp
open NeuroForgeApp.xcodeproj
# Press ⌘U, click Allow

# 2. Run backend
cd ~/Documents/GitHub
make green

# 3. Run tests
cd ~/Documents/GitHub/NeuroForgeApp
make xctest

# 4. Launch app
bash scripts/run_frontend.sh
```

---

**READY TO RUN** ✅
**Time**: ~5 minutes total
**Status**: All code shipped, permission grant needed
**Next**: Run the 4 commands above! 🚀
