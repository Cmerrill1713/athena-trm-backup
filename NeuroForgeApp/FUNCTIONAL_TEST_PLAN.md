# 🧪 Functional Test Plan - Modern Home App UI

## ✅ What to Test

Since automated testing is limited, here's a manual test plan you can execute in 5 minutes.

---

## 🚀 Prerequisites

### 1. Start Backend Services
```bash
cd /Users/christianmerrill/Documents/GitHub
make stack-up
# Wait 10 seconds for services to start
```

### 2. Enable Modern UI
In Xcode:
- Product → Scheme → Edit Scheme
- Run → Environment Variables
- Add: `FEATURE_MODERN_UI` = `1`
- Close

### 3. Build & Run
- Press ⌘B to build
- Press ⌘R to run

---

## 📋 Test Checklist

### Test 1: App Launch ✓
**Expected**: App launches with modern UI
- [ ] Glassmorphic background visible
- [ ] Service status badges in header
- [ ] No crash on launch

**Pass/Fail**: ______

---

### Test 2: Service Health Indicators ✓
**Expected**: Badges show real status
- [ ] 4 badges visible (Bridge, Athena, UAT, Kokoro)
- [ ] Green dots = online, Red dots = offline
- [ ] Pulsing animation on dots

**Pass/Fail**: ______

**Services up**: ___/4

---

### Test 3: Command Palette (⌘K) ✓
**Steps**:
1. Press ⌘K
2. Type "health"
3. Press Enter

**Expected**:
- [ ] Palette opens with frosted glass
- [ ] Commands filter as you type
- [ ] Toast appears: "X/4 services up"
- [ ] Palette closes after execution

**Pass/Fail**: ______

---

### Test 4: Status Window (⌘⌥O) ✓
**Steps**:
1. Press ⌘⌥O

**Expected**:
- [ ] New window opens
- [ ] Shows 4 services with status
- [ ] Green/red indicators match header
- [ ] "Refresh Status" button works

**Pass/Fail**: ______

---

### Test 5: Send Message ✓
**Steps**:
1. Type "Hello" in input
2. Press Enter

**Expected**:
- [ ] Message appears as bubble (right side)
- [ ] Glassmorphic bubble with gradient
- [ ] Smooth animation
- [ ] Input clears

**Pass/Fail**: ______

---

### Test 6: RAG Integration ✓
**Prerequisites**: RAG service running on :8015

**Steps**:
1. Send a message: "test query"
2. Press ⌘K
3. Type "rag"
4. Press Enter

**Expected**:
- [ ] Toast: "✅ Added X results" OR "⚠️ RAG offline"
- [ ] If online: Context injected in input field
- [ ] If offline: Graceful error message

**Pass/Fail**: ______

---

### Test 7: Vision Integration ✓
**Prerequisites**: Vision service running on :8016

**Steps**:
1. Press ⌘K
2. Type "describe"
3. Press Enter
4. Select an image (any .png/.jpg)

**Expected**:
- [ ] Image picker opens
- [ ] After selecting: Toast "✅ Image described" OR "⚠️ Vision offline"
- [ ] If online: Description added to input
- [ ] If offline: Graceful error

**Pass/Fail**: ______

---

### Test 8: Visual Polish ✓
**Check**:
- [ ] Glassmorphism visible (frosted glass effects)
- [ ] Smooth animations (no jank)
- [ ] Colors look good in dark mode
- [ ] No visual glitches
- [ ] Text is readable

**Pass/Fail**: ______

---

### Test 9: Keyboard Shortcuts ✓
**Try each**:
- [ ] ⌘K → Command palette
- [ ] ⌘⌥O → Status window
- [ ] Space → Voice (if configured)
- [ ] Enter → Send message
- [ ] ⇧Enter → New line
- [ ] Escape → Close palette

**Pass/Fail**: ______

---

### Test 10: Error Handling ✓
**Steps**:
1. Stop all services: `make stack-down`
2. Press ⌘K → "Check Service Health"

**Expected**:
- [ ] Toast: "0/4 services up"
- [ ] Red dots on all badges
- [ ] No crash
- [ ] App remains usable

**Pass/Fail**: ______

---

## 📊 Test Results Summary

```
Total Tests: 10
Passed: ___
Failed: ___
Skipped: ___

Pass Rate: ___%
```

---

## 🐛 Known Issues to Watch For

1. **Services offline** → Should show red dots, not crash
2. **RAG/Vision timeout** → Should show "offline" toast
3. **Image too large** → Should handle gracefully
4. **Fast clicking** → Should not spawn multiple windows
5. **Dark mode** → Colors should remain visible

---

## ✅ Success Criteria

**Minimum to pass**:
- [ ] App launches without crash
- [ ] Modern UI visible (glassmorphism)
- [ ] Service badges show status
- [ ] ⌘K palette works
- [ ] Messages display correctly

**Nice to have**:
- [ ] RAG integration works
- [ ] Vision integration works
- [ ] All animations smooth
- [ ] No visual glitches

---

## 🔧 Troubleshooting

### App won't build
```bash
cd NeuroForgeApp
rm -rf .build DerivedData
swift package clean
swift build
```

### Modern UI not showing
- Check environment variable is set: `FEATURE_MODERN_UI=1`
- Rebuild app (⌘B)
- Restart Xcode

### Services appear offline
```bash
cd /Users/christianmerrill/Documents/GitHub
make stack-status  # Check what's running
make stack-up      # Restart if needed
```

### Command palette not opening
- Try clicking menu: (if available)
- Check Console.app for errors
- Restart app

---

## 📝 Report Template

```
## Test Report

Date: ___________
Tester: ___________
Build: Debug

### Environment
- macOS: ___________
- Xcode: ___________
- Swift: ___________

### Results
- Tests Passed: ___/10
- Critical Issues: ___
- Minor Issues: ___

### Notes:
___________
___________
___________

### Recommendation:
[ ] Ready to ship
[ ] Needs fixes
[ ] Blocked by: ___________
```

---

## 🎯 Quick Smoke Test (30 seconds)

If you're short on time, test these 3 things:

1. **Launch** → Press ⌘R → App opens ✓
2. **Palette** → Press ⌘K → Opens with commands ✓
3. **Message** → Type "test" → Press Enter → Bubble appears ✓

If all 3 pass → **Probably good to go!** ✅

---

## 📞 Next Steps

After testing:

**If all tests pass** → Update `HOME_APP_UI_READY.md` with "TESTED ✅"

**If issues found** → Document in GitHub issues or here

**If ready** → Tag as `v1.0-modern-ui` and ship! 🚀

---

**Good luck with testing!** 🧪✨
