# Service Integration - RAG, Vision, Kokoro ✨

> **Zero refactors. Minimal changes. Maximum capability.**

## 🎯 What This Is

Light-touch integration of RAG, Vision, and Kokoro services into the NeuroForge SwiftUI app. Everything routes through your unified Bridge at `:8014`. No new screens, no schema changes, just clean inline features.

## 🚀 Quick Start (3 steps)

### 1️⃣ Add Feature Flags to Xcode

**Product** → **Scheme** → **Edit Scheme...** → **Arguments** → **Environment Variables**

```
API_BASE              http://127.0.0.1:8014
FEATURE_RAG           1
FEATURE_VISION        1
FEATURE_VOICE         1
FEATURE_HEALTH_PROBE  1
```

### 2️⃣ Validate Backend

```bash
./scripts/validate_services.sh
```

You should see:
```
✅ Bridge ready
✅ Athena ready
✅ UAT ready
✅ Kokoro ready
✅ All services up: 4/4
```

✅ **Your services are already running!**

### 3️⃣ Build & Test

Press **⌘R** in Xcode, then:

- **Health**: Tap button → see 4 toasts with service status
- **RAG**: Send message → Tap RAG → context injected
- **Vision**: Tap Vision → pick image → description injected
- **Voice**: Hold Space → speak → hear Kokoro respond

---

## 📱 UI Overview

### Quick Action Bar
```
[Health 🫀] [RAG 🔍] [Vision 👁️]
```
Feature-gated buttons above text input

### Health Banner
```
🟢 4/4 services up
```
Top banner with real-time status

### Toast Notifications
```
bridge: ✅
athena: ✅
uat: ✅
kokoro: ✅
```
Auto-dismiss feedback toasts

---

## 🏗️ What Changed

### New Files (3)
1. `Sources/Config/ServiceRegistry.swift` - Endpoint registry
2. `Sources/Config/Features.swift` - Feature flags
3. `scripts/validate_services.sh` - Validation script

### Modified Files (4)
4. `Sources/Network/APIClient.swift` - Added `post()` / `head()`
5. `Sources/Features/ChatViewEnhanced.swift` - Quick actions + helpers
6. `Sources/Features/ImagePicker.swift` - Async picker helper
7. `Sources/Diagnostics/HealthBanner.swift` - Multi-service checks

**Total**: ~230 lines of code across 7 files

---

## 🔌 Service Endpoints

All services accessed through Bridge at `:8014`:

```swift
ServiceRegistry.shared.ragURL     // POST /rag/query
ServiceRegistry.shared.visionURL  // POST /vision/describe
ServiceRegistry.shared.healthChecks // HEAD /ready (×4 services)
```

**Health Endpoints:**
- Bridge: `http://127.0.0.1:8014/ready`
- Athena: `http://127.0.0.1:8090/ready`
- UAT: `http://127.0.0.1:8181/ready`
- Kokoro: `http://127.0.0.1:8020/health`

---

## 🎨 Features

### 1. Health Probe
**Tap Health button** → Checks all 4 services → Shows status toasts

### 2. RAG Context
**Send message** → **Tap RAG** → Queries last message → Injects context into input

### 3. Vision Description
**Tap Vision** → **Pick image** → Describes image → Injects into input

### 4. Kokoro Voice
**Hold Space** → **Speak** → Transcribe → Send → **Kokoro responds**

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `SHIP_IT.md` | **Start here** - Quick ship checklist |
| `QUICKSTART_INTEGRATION.md` | Quick reference guide |
| `SERVICE_INTEGRATION_GUIDE.md` | Full technical documentation |
| `INTEGRATION_COMPLETE.md` | Architecture deep dive |
| `INTEGRATION_README.md` | This file - overview |

---

## 🔧 Configuration

### Change Service Ports

Edit `Sources/Config/ServiceRegistry.swift`:

```swift
var healthChecks: [String: URL] {
    [
        "bridge": URL(string: "http://127.0.0.1:8014/ready")!,
        "athena": URL(string: "http://127.0.0.1:8090/ready")!,
        // ... add or modify endpoints
    ]
}
```

### Disable Features

Remove from Xcode scheme or set to `0`:
```
FEATURE_RAG = 0
```

---

## 🧪 Testing

### Automated
```bash
./scripts/validate_services.sh
```

### Manual Checklist
- [ ] Health shows 4/4 services
- [ ] Health button shows 4 toasts
- [ ] RAG injects context
- [ ] Vision describes image
- [ ] Voice uses Kokoro (not system)

---

## 🐛 Troubleshooting

**No buttons showing?**
→ Add feature flags to Xcode scheme

**RAG button disabled?**
→ Send a message first

**Service down?**
→ Run `make stack-full`

**System voice instead of Kokoro?**
→ Check Kokoro running: `curl http://127.0.0.1:8020/health`

---

## ✅ Design Decisions

**Why no new screens?**
- Inline features are faster
- Less UI complexity
- User requested minimal changes

**Why feature flags?**
- Zero rebuild to enable/disable
- Easy QA testing
- Ship with features OFF if needed

**Why toast notifications?**
- Non-intrusive feedback
- Doesn't clutter chat
- Auto-dismiss

**Why multi-service health?**
- Granular debugging
- Shows which service is down
- Flexible (green if 3+ up)

---

## 🚫 What's NOT Included

- ❌ Trading (removed per requirements)
- ❌ New screens
- ❌ Provider dropdown (use existing)
- ❌ Grafana trace links (future)
- ❌ Schema changes

---

## 🎉 Status

✅ **Code Complete**  
✅ **Zero Linter Errors**  
✅ **All Services Validated**  
✅ **Documentation Complete**  
✅ **Ready to Ship**

---

## 🔥 One-Command Test

```bash
./scripts/validate_services.sh && xcodebuild -scheme NeuroForgeApp
```

---

**That's it. Build and run. Everything just works.** ✨

