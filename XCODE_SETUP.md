# 🎯 Xcode Setup - Enable Modern UI

## Quick Steps

### 1. Open Project
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
open Package.swift
```

Or in Finder:
- Navigate to `Documents/GitHub/NeuroForgeApp`
- Double-click `Package.swift`

---

### 2. Configure Environment Variable

**In Xcode Menu Bar**:
1. Click **Product** → **Scheme** → **Edit Scheme...**
2. On the left sidebar, click **Run**
3. Select the **Arguments** tab at the top
4. Under **Environment Variables**, click the **+** button
5. Add:
   - **Name**: `FEATURE_MODERN_UI`
   - **Value**: `1`
6. Click **Close**

**Visual Guide**:
```
Product Menu
  └─ Scheme
      └─ Edit Scheme...
          └─ Run (left sidebar)
              └─ Arguments (top tab)
                  └─ Environment Variables
                      └─ Click +
                          └─ FEATURE_MODERN_UI = 1
```

---

### 3. Build & Run

**Option A**: Keyboard (fastest)
- Press **⌘B** to build
- Press **⌘R** to run

**Option B**: Menu
- Product → Build (⌘B)
- Product → Run (⌘R)

---

### 4. Verify Modern UI Loaded

When app launches, you should see:

✅ **Service status badges** in header (4 colored dots)  
✅ **Glassmorphic background** (frosted glass effect)  
✅ **Modern input area** at bottom  
✅ **Gradient colors** throughout  

If you see the **old plain UI**, the environment variable didn't load. Try:
- Clean build: **⌘⇧K**
- Rebuild: **⌘B**
- Run: **⌘R**

---

## 🧪 Quick Test

Once app is running:

### Test 1: Command Palette
1. Press **⌘K**
2. Type "health"
3. Press **Enter**
4. Should see toast: "X/4 services up"

### Test 2: Send Message
1. Type "hello" in input
2. Press **Enter**
3. Should see glassmorphic bubble appear

### Test 3: Status Window
1. Press **⌘⌥O**
2. Should see simple window with 4 services

---

## 🔧 Troubleshooting

### "Cannot find ModernChatView"
**Fix**: Clean and rebuild
```
⌘⇧K (Clean Build Folder)
⌘B (Build)
⌘R (Run)
```

### "Environment variable not working"
**Fix**: Double-check spelling
- Must be exactly: `FEATURE_MODERN_UI`
- Value must be: `1`
- Not `true`, not `yes`, just `1`

### App crashes on launch
**Check Console.app**:
1. Open Console.app
2. Filter: "NeuroForge"
3. Look for error messages
4. Share with me if you find errors

---

## 📋 Environment Variables (All Optional)

Add these if you want to enable features:

| Variable | Value | Effect |
|----------|-------|--------|
| `FEATURE_MODERN_UI` | `1` | Enable modern UI ⭐ |
| `FEATURE_RAG` | `1` | Enable RAG button |
| `FEATURE_VISION` | `1` | Enable Vision button |
| `FEATURE_VOICE` | `1` | Enable voice input |
| `FEATURE_HEALTH_PROBE` | `1` | Enable health checks |

**For this test, just set `FEATURE_MODERN_UI=1`**

---

## ✅ Success Criteria

App is working if you see:

1. ✅ App window opens (doesn't crash)
2. ✅ Modern UI visible (not plain/basic)
3. ✅ Service badges in header
4. ✅ ⌘K opens command palette
5. ✅ Messages display as bubbles

**If all 5 pass → Success!** 🎉

---

## 🚀 Ready?

1. **Backend running?** → Check `START_EVERYTHING.md`
2. **Xcode open?** → `open Package.swift`
3. **Env var set?** → `FEATURE_MODERN_UI=1`
4. **Press ⌘R** → Launch!

**Let me know what happens!** 🎯

