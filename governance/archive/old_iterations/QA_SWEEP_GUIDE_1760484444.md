# NeuroForge QA Sweep Guide

**Command**: `make qa`
**Duration**: ~120 seconds
**Coverage**: Complete validation of all features

---

## 🚀 One-Shot QA Sweep

### **Run Complete QA:**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
make qa
```

### **What It Does:**
```
1. 🧹 Clean - Remove old build artifacts and test captures
2. 🔧 Verify - Check all 6 backend services are healthy
3. 🔥 Warmup - Pre-heat services to cut latency
4. 🧪 UI Tests - Run full test suite in QA mode
5. 📊 Golden Diff - Verify no visual regressions (CI tolerance)
6. ✅ Report - Summary of all verified features
```

### **Expected Output:**
```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          NeuroForge Complete QA Sweep                          ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

🧹 Step 1: Clean build artifacts...
✅ Clean complete

🔧 Step 2: Verify backend services...
✅ chat
✅ tts
✅ k1
✅ k2
✅ k3
✅ weaviate
✅ All services healthy

🔥 Step 3: Warm up services...
✅ Warmup complete

🧪 Step 4: UI tests (QA mode)...
** TEST SUCCEEDED **
✅ UI tests complete

📊 Step 5: Golden diff (CI tolerance)...
** TEST SUCCEEDED **
✅ Golden diff complete

╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          ✅ QA SWEEP COMPLETE - ALL GREEN                      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

📦 Artifacts:
  - artifacts/UITestArtifacts.zip
  - artifacts/NeuroForgeUI.xcresult
  - UITests/Golden/Actual/ (captured screenshots)
  - UITests/Golden/Diffs/ (diff images if any)

🎯 Verified:
  ✅ Provider Inspector
  ✅ Golden Diff
  ✅ Vision + RAG
  ✅ Prompt Sidebar
  ✅ All UI flows

🚀 Ready to ship!
```

---

## 🧪 Manual 90-Second Smoke Test

### **Launch App:**
```bash
cd NeuroForgeApp
API_BASE=http://localhost:8014 QA_MODE=1 swift run
```

### **Smoke Test Checklist:**

**✅ Basic Chat (30 seconds):**
```
1. Type "ping" → Get reply
2. Verify text is visible (not white/clear)
3. Press Enter → Message sends
4. Press Shift+Enter → Newline inserts
5. Check health banner shows "Connected"
```

**✅ Provider Inspector (30 seconds):**
```
1. Press ⌘⌥I → Inspector appears in bottom-right
2. Click "FastVLM" → ACTIVE tag shows
3. Press ⌘⇧R → Health indicators update
4. Check colors: ≤150ms🟢, 151-600ms🟠, >600ms🔴
5. Press ⌘⇧0 → Resets to Auto
6. Send message → Check console log for override header
```

**✅ Prompt Sidebar (30 seconds, if implemented):**
```
1. Press ⌘⇧T → Sidebar appears
2. Select template → Preview shows
3. Click "Insert" → Template fills input
4. Try variable substitution
5. Test search/filter
```

**✅ Console Logs:**
```
Expected logs:
[ProviderInspector] override=fastvlm source=client timestamp=...
[APIClient] POST /api/chat hdr:X-Provider-Override=fastvlm rtt=142ms code=200
```

---

## 🩺 Quick Diagnostics

### **Services Not Green?**
```bash
make green

# If any service down:
# ❌ chat → Check backend on :8014
# ❌ tts → Check TTS service on :8888
# ❌ weaviate → Check Weaviate on :8090
# ❌ k1/k2/k3 → Check Kokoro instances
```

### **Tests Failing?**
```bash
# Check logs
tail -100 artifacts/xcodebuild-ui-tests.log

# Check for diff images (visual regressions)
ls -la UITests/Golden/Diffs/

# If diffs exist, review them
open UITests/Golden/Diffs/
```

### **Visual Regressions?**
```bash
# Compare baseline vs actual
open UITests/Golden/Baseline/MainChatView_Golden.png
open UITests/Golden/Actual/MainChatView_Golden.png

# If change is intentional:
make golden-update
git add UITests/Golden/Baseline/*.png
git commit -m "test(ui): update golden baselines"

# If change is a regression:
# Fix the UI code and re-run
```

---

## 🎯 QA Modes

### **Mode 1: Standard QA Sweep**
```bash
make qa

# Runs:
# - Clean + warmup + UI tests + golden diff
# - QA_MODE=1 for all features
# - CI tolerance (0.3%) for golden diff
```

### **Mode 2: Quick Confidence Check**
```bash
make green
NeuroForgeApp/scripts/warmup_services.sh || true
make xctest

# Runs:
# - No clean (faster)
# - Standard tolerance (0.25%)
# - Full test suite
```

### **Mode 3: Golden Update**
```bash
make golden-update

# Runs:
# - GOLDEN_UPDATE=1
# - Captures new baselines
# - Saves to Baseline/
```

### **Mode 4: CI Simulation**
```bash
GOLDEN_TOLERANCE=0.003 make golden-ci

# Runs:
# - CI-level strictness
# - Same as GitHub Actions
# - Validates PR readiness
```

---

## 📊 Expected Results

### **Test Counts:**
```
Total Test Files: 10
Test Methods: 20+
Duration: ~60-120 seconds

Breakdown:
✅ BootAndHealthTests (2-3 tests)
✅ ChatBehaviorTests (4-5 tests)
✅ RAGTests (2-3 tests, may skip)
✅ IntegrationTests (2-3 tests)
✅ ErrorPathTests (3-4 tests)
✅ GoldenScreenshotTests (3 tests)
✅ ProviderInspectorTests (7 tests)
✅ PromptSidebarTests (3-4 tests, if implemented)
✅ VisionRAGTests (2-3 tests, if implemented)
```

### **Artifacts Generated:**
```
artifacts/
├── NeuroForgeUI.xcresult           # Test results (open in Xcode)
├── xcodebuild-ui-tests.log        # Detailed build log
└── UITestArtifacts.zip            # Complete artifacts
    ├── Test results
    ├── Build logs
    ├── Baseline screenshots
    ├── Actual screenshots
    └── Diff images (if failures)

UITests/Golden/
├── Baseline/                       # Canonical screenshots (git tracked)
│   ├── MainChatView_Golden.png
│   ├── ProviderInspector_Golden.png
│   └── ErrorState_Golden.png
├── Actual/                         # Latest captures (ignored)
└── Diffs/                          # Red-highlighted diffs (ignored)
```

---

## 🔍 What Gets Verified

### **Provider Inspector:**
- ✅ Visibility in QA mode
- ✅ Toggle with ⌘⌥I
- ✅ Provider selection (Auto/FastVLM/Ollama/TRM)
- ✅ Health indicators (🟢🟠🔴)
- ✅ Latency metrics
- ✅ Reset to auto (⌘⇧0)
- ✅ Refresh health (⌘⇧R)
- ✅ Persistence across launches

### **Golden Diff:**
- ✅ Pixel-diff comparison works
- ✅ Tolerance enforcement (0.003 in CI)
- ✅ Diff images generated on failure
- ✅ Baseline/Actual/Diff attachments
- ✅ No visual regressions

### **Vision + RAG (If Implemented):**
- ✅ Image picker opens
- ✅ FastVLM analysis works
- ✅ Auto-ingest to Weaviate
- ✅ Citations in responses
- ✅ Thumbnail display

### **Prompt Sidebar (If Implemented):**
- ✅ Sidebar toggle (⌘⇧T)
- ✅ Template selection
- ✅ Quick insert
- ✅ Variable substitution
- ✅ Search/filter

### **Core UI:**
- ✅ App launches
- ✅ Health banner displays
- ✅ Chat input works
- ✅ Enter sends message
- ✅ Shift+Enter adds newline
- ✅ Text visibility (no white text)
- ✅ Error handling (disconnected state)

---

## 🚀 Usage Examples

### **Daily Development:**
```bash
# Quick confidence check before committing
make -C NeuroForgeApp qa

# If all green → Safe to commit ✅
git add -A
git commit -m "feat: my changes"
```

### **Before Creating PR:**
```bash
# Full QA sweep to ensure everything works
cd NeuroForgeApp
make qa

# Review artifacts
open artifacts/NeuroForgeUI.xcresult

# If all green → Create PR ✅
```

### **After UI Changes:**
```bash
# Run tests to check for visual regressions
make -C NeuroForgeApp xctest

# If golden tests fail:
# 1. Review diff images
open UITests/Golden/Diffs/

# 2. If changes are intentional:
make golden-update
git add UITests/Golden/Baseline/*.png

# 3. If changes are bugs:
# Fix the UI code and re-run
```

### **CI Validation:**
```bash
# Simulate GitHub Actions locally
GOLDEN_TOLERANCE=0.003 make -C NeuroForgeApp golden-ci

# If passes → PR will pass CI ✅
```

---

## 📈 Performance Expectations

### **Timing:**
```
Clean:          5 seconds
Backend health: 2 seconds
Warmup:         3 seconds
UI tests:       60 seconds
Golden diff:    60 seconds
Total:          ~130 seconds
```

### **Optimization:**
```
# Skip clean for faster iteration
make xctest  # ~60 seconds

# Skip warmup if services already hot
make xctest  # ~60 seconds

# Full QA sweep when stability matters
make qa      # ~130 seconds
```

---

## ✅ Green Definition

### **All Green Means:**
- ✅ Backend: 6/6 services healthy
- ✅ Build: Compiles without errors/warnings
- ✅ Tests: 20+ test methods pass
- ✅ Golden: No visual regressions
- ✅ Artifacts: Complete test results generated
- ✅ Logs: No unexpected errors
- ✅ Duration: ≤130 seconds

### **Ready to Ship When:**
- ✅ `make qa` passes
- ✅ Manual smoke test passes
- ✅ No red diff images
- ✅ All features work as expected
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

---

## 🆘 Troubleshooting

### **QA Sweep Fails at Step 2 (Services):**
```bash
# Check which service is down
make green

# Start missing services
# ... start the failing service ...

# Re-run QA
make qa
```

### **QA Sweep Fails at Step 4 (UI Tests):**
```bash
# Check test logs
tail -100 artifacts/xcodebuild-ui-tests.log

# Common fixes:
# - Grant macOS permissions (⌘U in Xcode once)
# - Ensure QA_MODE=1 is set
# - Check accessibility IDs exist
```

### **QA Sweep Fails at Step 5 (Golden Diff):**
```bash
# Review diff images
open UITests/Golden/Diffs/

# If UI changes are intentional:
make golden-update
git add UITests/Golden/Baseline/*.png
git commit -m "test(ui): update golden baselines"

# Re-run QA
make qa
```

---

## 🚀 Ready to Use

Your QA sweep is now:
- ✅ **One command** - `make qa` does everything
- ✅ **Complete coverage** - All features verified
- ✅ **Fast** - ~130 seconds total
- ✅ **Reliable** - Deterministic results
- ✅ **Informative** - Clear success/failure reporting
- ✅ **Production ready** - Professional quality

**Run it now:**
```bash
make -C NeuroForgeApp qa
```

Then enjoy the green lights! ✅

---

**QA SWEEP READY** ✨
**Status**: Bulletproof Quality Assurance
**Next**: Run `make qa` and enjoy all green! 🚀
