# NeuroForge Launch Guide

**Quick Start**: Get the app window on screen in 2 minutes
**Purpose**: Troubleshoot launch issues and verify all features

---

## ⚡ FASTEST WAY TO LAUNCH (CLI)

### **One-Command Launch:**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh
```

**What it does:**
- Builds the app (debug mode)
- Sets environment variables (API_BASE, QA_MODE)
- Launches the binary directly
- Shows app window with all features enabled

---

## 🚀 LAUNCH OPTIONS

### **Option 1: Helper Script (Recommended)**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh

# Expected:
# 🔨 Building NeuroForge...
# 🚀 Launching NeuroForge...
#    API_BASE: http://localhost:8014
#    QA_MODE: 1
# [App window appears]
```

### **Option 2: Direct Binary Launch**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp

# Build
swift build -c debug

# Launch with env vars
env API_BASE="http://localhost:8014" QA_MODE=1 \
  ./.build/debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp
```

### **Option 3: Xcode (For Debugging)**
```bash
# Open in Xcode
make open

# Configure scheme:
# Edit Scheme → Run → Arguments → Environment Variables:
# - API_BASE = http://localhost:8014
# - QA_MODE = 1

# Press ⌘R to run
```

### **Option 4: SwiftPM Run**
```bash
# Build and run (but env vars don't work well with swift run for GUI apps)
API_BASE=http://localhost:8014 QA_MODE=1 swift run

# If window doesn't appear, use Option 1 or 2
```

---

## ✅ QUICK VERIFICATION (90 SECONDS)

### **After Launch:**

**1. Window Appears (5s)**
- ✅ App window visible
- ✅ Health banner shows "Connected" (green) or "Disconnected" (red)
- ✅ Chat input visible and focusable

**2. Basic Chat (15s)**
```
- Type "ping" → Get reply
- Press Enter → Message sends
- Press Shift+Enter → Newline inserts
- Text is visible (not white/clear)
```

**3. Provider Inspector (30s)**
```
- Press ⌘⌥I → Inspector appears in bottom-right
- Click "FastVLM" → ACTIVE tag shows
- Press ⌘⇧R → Health indicators update
- Check colors: ≤150ms🟢, 151-600ms🟠, >600ms🔴
- Press ⌘⇧0 → Resets to Auto
```

**4. Prompt Sidebar (20s, if wired)**
```
- Press ⌘⇧T → Sidebar appears
- Select template → Preview shows
- Click "Insert" → Template fills input
- Test variable substitution
```

**5. Console Logs (20s)**
```
Check Terminal for:
[ProviderInspector] override=fastvlm source=client timestamp=...
[APIClient] POST /api/chat hdr:X-Provider-Override=fastvlm rtt=142ms code=200
```

---

## 🛠️ COMMON LAUNCH BLOCKERS

### **Blocker 1: No Window Appears**

**Symptom**: Build succeeds but no app window
**Cause**: Launched via `open` without env vars

**Fix**:
```bash
# Option A: Use run_frontend.sh
bash scripts/run_frontend.sh

# Option B: Launch binary directly
./.build/debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp

# Option C: Set launchctl env (persistent)
launchctl setenv API_BASE http://localhost:8014
launchctl setenv QA_MODE 1
open ./.build/debug/NeuroForgeApp.app
```

---

### **Blocker 2: "No Such Product" / Wrong Scheme**

**Symptom**: Xcode shows wrong target or can't find scheme
**Cause**: Xcode project not generated or wrong scheme selected

**Fix**:
```bash
# Regenerate Xcode project
xcodegen generate

# Open and select correct scheme
open NeuroForgeApp.xcodeproj
# Scheme dropdown → Select "NeuroForgeApp"
```

---

### **Blocker 3: Codesign / Quarantine Errors**

**Symptom**: App bounces in dock then dies
**Cause**: macOS Gatekeeper blocking unsigned app

**Fix**:
```bash
# Remove quarantine
xattr -dr com.apple.quarantine ./.build/debug/NeuroForgeApp.app

# Ad-hoc sign
codesign --force --deep --sign - ./.build/debug/NeuroForgeApp.app

# Launch again
bash scripts/run_frontend.sh
```

---

### **Blocker 4: Stale Build / DerivedData**

**Symptom**: Build succeeds but crashes or shows old UI
**Cause**: Stale build artifacts or DerivedData

**Fix**:
```bash
# Clean all build artifacts
rm -rf .build DerivedData
rm -rf ~/Library/Developer/Xcode/DerivedData/*NeuroForge*

# Rebuild fresh
swift build -c debug

# Launch
bash scripts/run_frontend.sh
```

---

### **Blocker 5: Assets / Resources Not Found**

**Symptom**: Missing images, icons, or resources
**Cause**: Wrong working directory or bundle path

**Fix**:
```bash
# Run from project root
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh

# Check bundle resources
ls -la ./.build/debug/NeuroForgeApp.app/Contents/Resources/
```

---

### **Blocker 6: Crash on Launch**

**Symptom**: App starts then immediately crashes
**Cause**: Missing env var, nil unwrap, or service unavailable

**Fix**:
```bash
# Watch live logs
log stream --predicate 'process == "NeuroForgeApp"' &

# Launch app
bash scripts/run_frontend.sh

# Check console for crash reason
# Common: "Fatal error: Unexpectedly found nil..."

# Verify services
make green
```

---

### **Blocker 7: "Disconnected" Banner**

**Symptom**: App launches but shows disconnected
**Cause**: Backend not running or wrong URL

**Fix**:
```bash
# Verify backend is up
curl -sf http://localhost:8014/health
# Expected: {"status":"ok"} or similar

# If down, start services
cd ..
make green

# Verify URL is correct
echo $API_BASE  # Should be http://localhost:8014

# Hardcode fallback temporarily (for testing)
# In Sources/Config/APIBase.swift:
# return URL(string: "http://localhost:8014")!
```

---

## 🧪 VERIFICATION MATRIX

### **Expected Behavior:**

| Action | Expected Result | Logs |
|--------|----------------|------|
| Launch app | Window appears | Process started |
| Health banner | "Connected" (green) | Health check passed |
| Type "ping" | Get reply | [APIClient] POST /api/chat |
| Press ⌘⌥I | Inspector appears | Provider Inspector visible |
| Select FastVLM | ACTIVE tag shows | [ProviderInspector] override=fastvlm |
| Send message | Response arrives | hdr:X-Provider-Override=fastvlm rtt=Xms |

### **Health Check Ports:**

| Service | URL | Expected |
|---------|-----|----------|
| Main API | http://localhost:8014/health | 200 OK |
| TTS | http://localhost:8888/health | 200 OK |
| FastVLM | http://127.0.0.1:8811/health | 200 OK |
| Ollama | http://127.0.0.1:11434/api/version | 200 OK + JSON |
| Weaviate | http://localhost:8090/v1/meta | 200 OK + JSON |

---

## 🔧 DEBUG COMMANDS

### **Check Build Output:**
```bash
swift build -c debug 2>&1 | grep -i error
# Should be empty if build succeeded
```

### **Find the Binary:**
```bash
find .build -name "NeuroForgeApp" -type f
# Expected: .build/debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp
```

### **Test Binary Directly:**
```bash
# Run without any wrappers
./.build/debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp &

# Check if process started
ps aux | grep NeuroForgeApp
```

### **Check Environment:**
```bash
# Verify env vars are set
env | grep -E "API_BASE|QA_MODE"

# Set if missing
export API_BASE=http://localhost:8014
export QA_MODE=1
```

---

## 🚀 MAKEFILE INTEGRATION

### **Add to Makefile:**
```makefile
# Quick launch target
.PHONY: launch
launch:
	@bash scripts/run_frontend.sh

# Build and launch
.PHONY: run-qa
run-qa:
	@API_BASE=http://localhost:8014 QA_MODE=1 swift run
```

### **Usage:**
```bash
make launch  # Build + run with env vars
make run-qa  # Quick launch in QA mode
```

---

## ✅ SUCCESS CHECKLIST

- [ ] App window appears on screen
- [ ] Health banner shows "Connected" (or "Disconnected" if backend down)
- [ ] Chat input is focusable and visible
- [ ] Typing shows visible text (not white)
- [ ] Enter key sends message
- [ ] Shift+Enter adds newline
- [ ] ⌘⌥I toggles Provider Inspector
- [ ] ⌘⇧T toggles Prompt Sidebar (if wired)
- [ ] Console logs show API calls
- [ ] No crashes or errors

---

## 🎯 READY TO USE

Your app should now:
- ✅ Launch successfully
- ✅ Show all UI features
- ✅ Connect to backend
- ✅ Handle user input
- ✅ Display responses
- ✅ Log routing decisions

**Launch it:**
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
bash scripts/run_frontend.sh

# Then test:
# ⌘⌥I - Provider Inspector
# ⌘⇧T - Prompt Sidebar
# Type and chat!
```

---

**LAUNCH GUIDE COMPLETE** ✅
**Next**: Run the app and verify all features! 🚀
