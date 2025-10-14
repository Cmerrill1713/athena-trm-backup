# 🚀 Start Everything - Simple Guide

## Quick Start (Copy-Paste Each Block)

### 1. Start Athena (Terminal 1)
```bash
cd /Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools
source ../../.venv/bin/activate
ATH_TOKEN=supersecret python -m uvicorn athena.api:app --host 127.0.0.1 --port 8090
```
**Leave this running**. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8090
```

---

### 2. Start UAT (Terminal 2 - New Tab)
```bash
cd /Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools
source ../../.venv/bin/activate
UAT_TOKEN=supersecret UAT_AUTO_SEED=1 python -m uvicorn uat.api:app --host 127.0.0.1 --port 8181
```
**Leave this running**. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8181
✅ Seeded 170 traces
```

---

### 3. Start Bridge (Terminal 3 - New Tab)
```bash
cd /Users/christianmerrill/Documents/GitHub/bridge
source ../.venv/bin/activate
UAT_TOKEN=supersecret ATH_TOKEN=supersecret UAT_BASE=http://127.0.0.1:8181 ATHENA_BASE=http://127.0.0.1:8090 PYTHONPATH=.. python -m uvicorn adapter:app --host 0.0.0.0 --port 8014
```
**Leave this running**. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8014
```

---

### 4. Test Services (Terminal 4 - New Tab)
```bash
# Test Bridge
curl http://127.0.0.1:8014/health

# Should return:
# {"status":"healthy","adapter":"neuroforge-adapter-v1.0.0",...}
```

---

### 5. Launch App in Xcode

**Step 1**: Open the project
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
open Package.swift
```

**Step 2**: Set environment variable
- In Xcode: Product → Scheme → Edit Scheme
- Click "Run" on the left
- Select "Arguments" tab
- Under "Environment Variables" click **+**
- Add:
  - **Name**: `FEATURE_MODERN_UI`
  - **Value**: `1`
- Click "Close"

**Step 3**: Run the app
- Press **⌘R**

---

## ✨ What You Should See

### On Launch:
1. Modern glassmorphic UI
2. Service status badges (4 green dots if all services running)
3. Clean input field at bottom
4. Gradient background

### Test It:
1. **Press ⌘K** → Command palette appears
2. **Type "health"** → Press Enter → Toast shows "4/4 services up"
3. **Type a message** → Press Enter → Glassmorphic bubble appears
4. **Press ⌘⌥O** → Simple status window opens

---

## 🐛 Troubleshooting

### Services Won't Start
**Issue**: "Address already in use"
**Fix**:
```bash
# Kill anything on those ports
lsof -ti :8014 | xargs kill -9 2>/dev/null
lsof -ti :8090 | xargs kill -9 2>/dev/null
lsof -ti :8181 | xargs kill -9 2>/dev/null
# Then restart
```

### App Won't Build
**Issue**: Xcode errors
**Fix**:
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
rm -rf .build DerivedData
# Then press ⌘B in Xcode
```

### Modern UI Not Showing
**Issue**: Still seeing old UI
**Fix**:
- Verify `FEATURE_MODERN_UI=1` is set in scheme
- Clean build (⌘⇧K)
- Rebuild (⌘B)
- Run (⌘R)

---

## 🎯 Quick Verification

Once app is running, test these:

| Action | Shortcut | Expected Result |
|--------|----------|-----------------|
| Open palette | ⌘K | Frosted glass palette appears |
| Check health | ⌘K → type "health" | Toast shows status |
| Send message | Type + Enter | Glassmorphic bubble |
| Status window | ⌘⌥O | Simple 4-service panel |

---

## 📝 Summary

**Backend**: Start in 3 separate terminal tabs (Athena, UAT, Bridge)
**Frontend**: Open in Xcode, set `FEATURE_MODERN_UI=1`, press ⌘R
**Test**: Press ⌘K to verify it works

---

**Follow the steps above and let me know what happens!** 🚀
