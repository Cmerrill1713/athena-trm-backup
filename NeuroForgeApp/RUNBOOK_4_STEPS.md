# NeuroForge - 4-Step Runbook 🚀

**Get Swift UI tests running + launch frontend in 5 minutes**

---

## 📋 **4-STEP RUNBOOK (COPY/PASTE)**

### **Step 1: ONE-TIME Xcode Permissions (60s)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
open NeuroForgeApp.xcodeproj
```

**In Xcode:**
1. Press `⌘U` (run tests)
2. Click **Allow** on Accessibility/Automation prompts
3. **Scheme → Edit Scheme… → Test → Environment:**
   - `API_BASE` = `http://localhost:8014`
   - `QA_MODE` = `1`
4. Close Xcode

---

### **Step 2: Backend Up + Warm (30s)**

```bash
cd ~/Documents/GitHub
make green

~/Documents/GitHub/NeuroForgeApp/scripts/warmup_services.sh || true
```

**Expected:**
```
✅ chat
✅ tts
✅ k1, k2, k3
✅ weaviate
🎉 Service warmup complete!
```

---

### **Step 3: Run Swift UI Tests (60s)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
make xctest
```

**Or verbose:**
```bash
xcodebuild -project NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -derivedDataPath DerivedData \
  test | tee artifacts/xcodebuild-ui-tests.log
```

**Verify Success:**
```bash
# Check results
tail -100 artifacts/xcodebuild-ui-tests.log | grep "TEST"
# Should show: ** TEST SUCCEEDED **

# Open results bundle
open artifacts/NeuroForgeUI.xcresult
```

---

### **Step 4: Launch the App (10s)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh
```

**Expected:**
```
🔨 Building NeuroForge...
Build complete! (10.81s)

🚀 Launching NeuroForge...
[App window appears]
```

**Test Features:**
- `⌘⌥I` → Provider Inspector
- `⌘⇧T` → Prompt Sidebar
- Type "ping" → Get response
- Watch console: `[APIClient] POST /api/chat ...`

---

## ✅ **60-90s Smoke Test**

After app launches:

- [ ] Banner shows "Connected" ✅
- [ ] Enter sends message / Shift+Enter adds newline ✅
- [ ] Inspector: force FastVLM, press Refresh (latency colors update) ✅
- [ ] Sidebar: insert template → input fills ✅
- [ ] (Optional) "Attach Image" → caption + citations ✅

---

## 🛠️ **FAST FIXES**

### **"Early unexpected exit"**
```
Fix: Open Xcode, press ⌘U again to re-grant permissions
```

### **"Elements not found"**
```
Fix: Ensure QA_MODE=1 is set in scheme environment
```

### **"Services red"**
```bash
Fix: make green && re-run tests
```

### **"Golden diff fails"**
```bash
# Check what changed
open UITests/Golden/Diffs/

# If intentional UI change:
make golden-update
```

---

## 📁 **ARTIFACTS**

After tests run:

```
NeuroForgeApp/artifacts/
├── NeuroForgeUI.xcresult      # Open in Xcode
├── xcodebuild-ui-tests.log    # Full build log
└── UITestArtifacts.zip        # Screenshots/logs
```

**View:**
```bash
open artifacts/NeuroForgeUI.xcresult
cat artifacts/xcodebuild-ui-tests.log
```

---

## 🎯 **COPY-PASTE COMPLETE RUN**

```bash
# ============================================
# NEUROFORGE - COMPLETE RUN (4 STEPS)
# ============================================

# STEP 1: Permissions (one-time)
cd ~/Documents/GitHub/NeuroForgeApp
open NeuroForgeApp.xcodeproj
# In Xcode: ⌘U → Allow → Set env vars → Close

# STEP 2: Backend
cd ~/Documents/GitHub
make green
~/Documents/GitHub/NeuroForgeApp/scripts/warmup_services.sh || true

# STEP 3: UI Tests
cd ~/Documents/GitHub/NeuroForgeApp
make xctest
tail -100 artifacts/xcodebuild-ui-tests.log | grep "TEST"
open artifacts/NeuroForgeUI.xcresult

# STEP 4: Launch Frontend
bash scripts/run_frontend.sh
# ⌘⌥I for Inspector, ⌘⇧T for Sidebar
```

---

## 🚀 **AFTER GREEN**

### **Full QA Sweep:**
```bash
make -C ~/Documents/GitHub/NeuroForgeApp qa
# ~130s complete validation
```

### **Ship to Main:**
```bash
cd ~/Documents/GitHub
git checkout main
git merge --no-ff v0.9.2-dev -m "feat: v0.9.2 complete"
git tag v0.9.2-green
git push && git push --tags
```

---

## ✨ **YOU'RE READY**

**Status:**
- ✅ v0.9.2-dev pushed (12 commits)
- ✅ Pre-push hook active (validated!)
- ✅ All code compiles
- ✅ Tests ready (permission grant → run)
- ✅ Launch ready

**Next:**
1. Run Step 1 (permissions)
2. Run Steps 2-4 (backend, tests, launch)
3. Enjoy! 🎉

**If anything fails:** Paste the error line and I'll fix it instantly.

---

**START HERE:** Run the 4 steps above! ⚡
**Time:** 5 minutes to full green
**Result:** Tests passing + app running ✅
