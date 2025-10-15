# 🚀 Athena Focus Fixes - Verification Guide

## Fast Verify (Build → UI Test → Run)

### **1. Build**
```bash
cd /Users/christianmerrill/Documents/GitHub
bash scripts/xcode_build_debug.sh
```

**Expected:** `✅ Build complete: build/Build/Products/Debug/NeuroForgeApp.app`

---

### **2. Run Focus UI Tests**
```bash
make ui-test-focus
```

**Or with full result bundle:**
```bash
xcodebuild \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -only-testing:TypingFocusTests \
  -resultBundlePath ./artifacts/FocusUITests.xcresult \
  test

open ./artifacts/FocusUITests.xcresult  # Inspect detailed results
```

**Expected:** 3/3 tests passing

---

### **3. Launch App**
```bash
bash scripts/xcode_run_app.sh
```

**Manual Verification:**
- ✅ Type in main composer
- ✅ Trigger pop-outs (from demo script/backend)
- ✅ Confirm typing still works
- ✅ Cmd+Shift+L refocuses instantly

---

## 🔧 Troubleshooting Toggles (No Code Edits)

### **A. Verify Files in Target**
**In Xcode:**
1. Project → NeuroForgeApp target → Build Phases → Compile Sources
2. Verify these files are listed:
   - `WindowHelper.swift`
   - `InputFocusCoordinator.swift`
   - `main.swift`
3. For test file: NeuroForgeAppUITests target should include:
   - `TypingFocusTests.swift`

---

### **B. macOS Permissions**
**System Settings → Privacy & Security:**

- **Automation:**
  - ✅ Allow Terminal to control Messages
  - ✅ Allow Xcode to control Messages and Finder

- **Accessibility:**
  - ✅ Enable Xcode
  - ✅ Enable Terminal

- **Developer Tools:**
  - ✅ Trust Xcode command-line tools

---

### **C. Run UI Tests Headlessly**
If `TypingFocusTests` flakes with pop-outs:

```bash
POPUPS_ENABLED=0 make ui-test-focus
```

---

### **D. Specify Scheme Explicitly**
If CI/test picker is confused:

```bash
SCHEME=NeuroForgeApp make ui-test-focus
```

---

## 🎯 Quick Triage Cheatsheet

### **Build Succeeds but App Won't Type**
- Run refocus shortcut: **Cmd+Shift+L**
- If that fixes it, `WindowHelper` is working
- Check any custom windows still calling `makeKeyAndOrderFront` without helper
- Swap to `configureNonStealingWindow(_:)`

---

### **UI Tests Fail Immediately**
- **Nearly always permissions**
- Open any macOS system prompt
- Grant Xcode/Terminal Automation & Accessibility
- Rerun tests

---

### **Pop-outs Steal Focus in Tests**
- Launch tests with `POPUPS_ENABLED=0`
- Or delay pop-out posting by 300-500ms in test harness

---

### **Xcode Says "File Not Found"**
- **Target membership issue**
- Select file in Project Navigator
- File Inspector → Target Membership
- Check NeuroForgeApp (and NeuroForgeAppUITests for test files)

---

## ✅ What "Good" Looks Like

### **Build:**
```
✅ Build complete: build/Build/Products/Debug/NeuroForgeApp.app
```

### **UI Tests:**
```
Test Suite 'TypingFocusTests' passed at ...
Executed 3 tests, with 0 failures (0 unexpected)
```

### **Running App:**
- ✅ Composer accepts typing
- ✅ Pop-outs render without blocking input
- ✅ Cmd+K or Cmd+Shift+L always restores focus
- ✅ No "can't type" issues

### **Cursor Tasks:**
- ✅ Can build, run, and trigger demos without leaving editor

---

## 🚀 Full Stack Demo (Optional)

```bash
# Terminal 1: Start backend
make backend-dev

# Terminal 2: Launch app and fire events
bash scripts/xcode_run_app.sh
sleep 3
bash scripts/athena_demo_events.sh

# Verify:
# → Critical alert pop-out appears
# → Tribunal decision pop-out appears
# → Emergency alert pop-out appears
# → Main input STILL accepts typing throughout ✅
```

---

## 📋 Cursor Integration

**From Cursor → Terminal → Run Task:**
- **"Athena: Build Debug"** - Clean build
- **"Athena: UI Focus Tests"** - Run focus regression tests
- **"Athena: Run App"** - Launch app
- **"Athena: Demo Pop-outs"** - Fire test events

---

## 🎊 Success Criteria

When all checks pass:
- ✅ Build completes cleanly
- ✅ 3/3 UI tests pass
- ✅ App runs and accepts typing
- ✅ Pop-outs don't steal focus
- ✅ Refocus shortcuts work
- ✅ No regressions possible (tests protect)

---

## 💡 Report Back

**After running the verification sequence, tell me:**

1. **Build result:** Success/fail?
2. **UI test result:** 3/3 pass or which failed?
3. **App typing works:** Yes/no?
4. **Pop-outs tested:** Yes/no (need backend)?
5. **Any errors:** Paste last 40 lines

**Then we'll know Athena truly "feels done"!** 🚀✨
