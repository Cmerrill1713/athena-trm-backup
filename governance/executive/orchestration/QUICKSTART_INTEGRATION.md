# QuickStart: Service Integration

## 🚀 Get Started in 3 Steps

### Step 1: Configure Xcode Scheme

Add environment variables to your Xcode scheme:

1. **Product** → **Scheme** → **Edit Scheme...**
2. Select **Run** → **Arguments**
3. Add these **Environment Variables**:
   ```
   API_BASE = http://127.0.0.1:8014
   FEATURE_RAG = 1
   FEATURE_VISION = 1
   FEATURE_VOICE = 1
   FEATURE_HEALTH_PROBE = 1
   ```

### Step 2: Start Backend Services

```bash
cd /Users/christianmerrill/Documents/GitHub
make stack-full
```

Expected services:
- Bridge: `:8014`
- Athena: `:8090`
- UAT: `:8181`
- Kokoro: `:8020`

### Step 3: Build & Run

```bash
cd NeuroForgeApp
xcodebuild -scheme NeuroForgeApp
# Or press ⌘R in Xcode
```

---

## 📱 UI Overview

### Quick Action Bar
Appears above text input (when features enabled):

```
[Health 🫀] [RAG 🔍] [Vision 👁️]
```

### Health Banner
Top banner shows service status:
- 🟢 **Green**: 3+ services up
- 🟡 **Yellow**: 1-2 services up
- 🔴 **Red**: 0 services up

---

## 🧪 Quick Test

### Test Health Probe
1. Launch app
2. Tap **Health** button
3. See 4 toasts:
   - `bridge: ✅`
   - `athena: ✅`
   - `uat: ✅`
   - `kokoro: ✅`

### Test RAG
1. Type: `"What is this project about?"`
2. Press Enter (send message)
3. Tap **RAG** button
4. Input field fills with context
5. Edit and send

### Test Vision
1. Tap **Vision** button
2. Select an image (PNG/JPG)
3. Input field fills with description
4. Edit and send

### Test Voice (Kokoro)
1. Hold **Space** or click **mic** button
2. Speak: `"Hello, can you hear me?"`
3. Release
4. Listen for Kokoro voice response

---

## 🔧 Validation Script

Run automated health check:

```bash
./scripts/validate_services.sh
```

Output:
```
🔍 Validating Service Integrations...

✅ Bridge ready
✅ Athena ready
✅ UAT ready
✅ Kokoro ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All services up: 4/4
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No quick action buttons | Enable feature flags in Xcode scheme |
| RAG button disabled | Send at least one message first |
| Service shows ⚠️ | Check service is running: `make stack-full` |
| Vision picker blank | Select PNG/JPG/TIFF/HEIC format |
| System voice instead of Kokoro | Start Kokoro: `cd kokoro && python serve.py` |

---

## 📂 Files Changed

```
NeuroForgeApp/
├── Sources/
│   ├── Config/
│   │   ├── ServiceRegistry.swift       ← NEW: Endpoint registry
│   │   └── Features.swift              ← NEW: Feature flags
│   ├── Network/
│   │   └── APIClient.swift             ← UPDATED: Added post/head helpers
│   ├── Features/
│   │   ├── ChatViewEnhanced.swift      ← UPDATED: Added quick actions
│   │   └── ImagePicker.swift           ← UPDATED: Added async helper
│   └── Diagnostics/
│       └── HealthBanner.swift          ← UPDATED: Multi-service check
└── scripts/
    └── validate_services.sh            ← NEW: Service validator
```

---

## ✅ What's Included
- ✅ RAG context injection
- ✅ Vision image description
- ✅ Kokoro voice (auto-detected)
- ✅ Multi-service health checks
- ✅ Toast notifications
- ✅ Feature flags

## ❌ What's NOT Included
- ❌ Trading (removed per requirements)
- ❌ New screens (inline features only)
- ❌ Provider dropdown (existing system used)
- ❌ Grafana trace links (future enhancement)

---

## 🎯 Next Steps

1. Test all integrations
2. Verify with feature flags OFF
3. Test error paths (services down)
4. Ship it! 🚀

