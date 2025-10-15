# ✅ Athena "Feels Done" - Complete Implementation Guide

## 🎯 Mission: Kill "Can't Type" Bug + Lock Swift Build + Wire Full Stack

---

## 📋 30-Minute Implementation Checklist

### ✅ **1. Fix Input Focus (@FocusState)**
- [ ] Add `@FocusState` to ChatInputBar
- [ ] Add `.focused($isFocused)` to TextField
- [ ] Add `.onAppear` to set focus
- [ ] Add `.onReceive` for app activation events

**File:** `NeuroForgeApp/Views/ChatInputBar.swift` (or equivalent)

**Implementation:** See `ATHENA_FOCUS_FIX.md` section 1

---

### ✅ **2. Fix Pop-Out Windows (Don't Steal Focus)**
- [ ] Create `configureNonStealingWindow(_:)` helper
- [ ] Apply to Critical Alert window
- [ ] Apply to Tribunal window
- [ ] Apply to Emergency window

**Files:** Where you create pop-out NSWindow instances

**Implementation:** See `ATHENA_FOCUS_FIX.md` section 2

---

### ✅ **3. Tag Main Window**
- [ ] Add `id: "main-window"` to main Window
- [ ] Verify window ID in window creation

**File:** `NeuroForgeApp/AthenaApp.swift` (or main app file)

**Implementation:** See `ATHENA_FOCUS_FIX.md` section 3

---

### ✅ **4. Add Refocus Keyboard Shortcut**
- [ ] Create `AppCommands` struct
- [ ] Add "Refocus Input" command
- [ ] Wire to Cmd+Shift+L
- [ ] Register in App body

**File:** `NeuroForgeApp/AthenaApp.swift`

**Implementation:** See `ATHENA_FOCUS_FIX.md` section 4

---

### ✅ **5. Xcode Hygiene (Clean Duplicates)**
- [ ] Remove duplicate files from Compile Sources
- [ ] Keep only one `@main` entry point
- [ ] Guard all PreviewProvider with `#if DEBUG`
- [ ] Fix VoiceManager duplicates (use protocol)
- [ ] Check Target Membership for all files
- [ ] Remove old shim files

**Reference:** See `XCODE_HYGIENE_CHECKLIST.md`

---

### ✅ **6. Cursor Integration**
- [ ] Build script created: `scripts/xcode_build_debug.sh` ✅
- [ ] Run script created: `scripts/xcode_run_app.sh` ✅
- [ ] Demo script created: `scripts/athena_demo_events.sh` ✅
- [ ] Cursor tasks added: `cursor.json` ✅

---

## 🚀 **Quick Test Sequence**

### **After Implementing Fixes:**

```bash
# 1. Clean build
rm -rf ~/Library/Developer/Xcode/DerivedData/*
bash scripts/xcode_build_debug.sh

# 2. Run app
bash scripts/xcode_run_app.sh

# 3. Test typing
# → Open Athena
# → Type in input field
# → Should work!

# 4. Test pop-outs (if backend running)
make backend-dev  # In separate terminal
bash scripts/athena_demo_events.sh

# 5. Verify focus behavior
# → Pop-out should appear
# → Input field should still accept typing
# → If lost, press Cmd+Shift+L to refocus
```

---

## 🛠️ **Cursor Commands Now Available**

From Cursor → Terminal → Run Task:
- **"Athena: Build (Debug)"** - Build the app
- **"Athena: Run App"** - Launch the app
- **"Athena: Demo Pop-outs"** - Fire test events
- **"Athena: Full Stack Test"** - Backend + Frontend + Events

---

## 📊 **What This Fixes**

| Issue | Fix | Status |
|-------|-----|--------|
| **Can't type after pop-out** | `@FocusState` + focus management | ✅ Ready |
| **Pop-outs steal focus** | `configureNonStealingWindow()` | ✅ Ready |
| **Build regressions** | Xcode hygiene checklist | ✅ Ready |
| **Duplicate symbols** | Remove duplicates, one `@main` | ✅ Ready |
| **VoiceManager conflicts** | Protocol injection | ✅ Ready |
| **No Cursor controls** | Build/run/demo scripts | ✅ Complete |
| **Manual testing** | Automated demo events | ✅ Complete |

---

## 🎯 **Priority Order**

### **Do First (High Impact):**
1. ✅ Fix input focus (`@FocusState`)
2. ✅ Fix pop-out windows (`configureNonStealingWindow`)
3. ✅ Tag main window (`id: "main-window"`)

### **Do Second (Stability):**
4. ✅ Clean Xcode duplicates
5. ✅ Remove extra `@main` entries
6. ✅ Guard previews

### **Do Third (Nice to Have):**
7. ✅ Add refocus shortcut (Cmd+Shift+L)
8. ✅ Fix VoiceManager with protocol

---

## 🎊 **Success Criteria**

**Athena "Feels Done" When:**
- ✅ You can type reliably in input field
- ✅ Pop-outs appear without stealing focus
- ✅ Build succeeds with zero warnings
- ✅ Cursor can build/run/demo with one click
- ✅ Backend events trigger pop-outs
- ✅ Refocus shortcut works (Cmd+Shift+L)

---

## 💡 **Implementation Time Estimate**

- **Focus fixes**: 10 minutes
- **Pop-out fixes**: 10 minutes
- **Xcode hygiene**: 10 minutes
- **Testing**: 5 minutes

**Total**: ~35 minutes to "Athena feels done"

---

## 🚀 **Next Steps**

1. **Implement focus fixes** (sections 1-4 from ATHENA_FOCUS_FIX.md)
2. **Clean Xcode project** (XCODE_HYGIENE_CHECKLIST.md)
3. **Test with Cursor** (use new tasks)
4. **Run demo sequence** (backend + app + events)

**Tell me which section to implement first, or say "implement all" and I'll push the complete fixes!** 🚀

---

**All scripts are ready - just need to apply the Swift code fixes!**
