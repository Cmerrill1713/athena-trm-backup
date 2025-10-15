# Service Integration Guide

## Overview
The NeuroForge app now integrates with RAG, Vision, and Kokoro services through a unified Bridge endpoint at `http://127.0.0.1:8014`.

## Quick Start

### 1. Enable Feature Flags

Add these environment variables to your Xcode scheme or `.env`:

```bash
FEATURE_RAG=1
FEATURE_VISION=1
FEATURE_VOICE=1
FEATURE_HEALTH_PROBE=1
```

### 2. Start Services

```bash
# Core + RAG + Vision + Voice
make stack-full

# Or start individually
cd bridge && python app.py &
cd athena && python server.py &
cd kokoro && python serve.py &
```

### 3. Verify Services

In the app, tap the **Health** button to check all service statuses:
- ✅ = Service is up
- ⚠️ = Service is down

## Features

### 🔍 RAG Integration
- **Button**: RAG (doc.text.magnifyingglass icon)
- **Behavior**: Queries the last user message against the RAG knowledge base and injects context into the input field
- **Endpoint**: `POST /rag/query`
- **Payload**: `{"query": "user message", "top_k": 5}`
- **Response**: Plain text context string

### 👁️ Vision Integration
- **Button**: Vision (eye.circle icon)
- **Behavior**: Opens file picker, sends image to vision service, injects description into input field
- **Endpoint**: `POST /vision/describe`
- **Payload**: `{"image_base64": "..."}`
- **Response**: Plain text image description

### ❤️ Health Probe
- **Button**: Health (heart.circle icon)
- **Behavior**: Checks all services (bridge, athena, uat, kokoro) and displays status via toast
- **Endpoints**: 
  - `HEAD http://127.0.0.1:8014/ready` (Bridge)
  - `HEAD http://127.0.0.1:8090/ready` (Athena)
  - `HEAD http://127.0.0.1:8181/ready` (UAT)
  - `HEAD http://127.0.0.1:8020/health` (Kokoro)

### 🎙️ Voice (Already Integrated)
- **Kokoro TTS**: Auto-detected at `http://127.0.0.1:8020/tts`
- **Fallback**: System voice if Kokoro unavailable
- **Voice**: af_heart (Kokoro "serna" voice)

## Architecture

```
┌─────────────────┐
│  NeuroForge App │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ServiceRegistry │  ← Central endpoint registry
└────────┬────────┘
         │
         ├─► /rag/query       → RAG service
         ├─► /vision/describe → Vision service
         ├─► /ready           → Bridge health
         ├─► /athena/ready    → Athena health
         └─► /kokoro/health   → Kokoro health
```

## UI Components

### Quick Action Bar
Appears above the text input when feature flags are enabled:

```
[Health] [RAG] [Vision]
```

### Health Banner
Shows service status at the top:
- **Green**: 3+ services up
- **Yellow**: 1-2 services up
- **Red**: 0 services up
- **Text**: "N/M services up"

### Toast Notifications
Temporary bottom-screen notifications for:
- Health check results
- RAG success/error
- Vision success/error

## Testing

### Manual Test Flow

1. **Start services**:
   ```bash
   make stack-full
   ```

2. **Launch app** with feature flags enabled

3. **Test Health**:
   - Tap **Health** button
   - Verify 4 toasts appear with service statuses

4. **Test RAG**:
   - Send a message: "What is the project about?"
   - Tap **RAG** button
   - Verify context appears in input field
   - Send enhanced message

5. **Test Vision**:
   - Tap **Vision** button
   - Select an image file
   - Verify description appears in input field
   - Send message with image context

6. **Test Voice**:
   - Hold Space or click mic button
   - Speak a message
   - Verify Kokoro voice responds

### Validation Script

```bash
./scripts/validate_services.sh
```

Expected output:
```
✅ Bridge ready
✅ Athena ready
✅ UAT ready
✅ Kokoro health
✅ 4/4 services up
```

## Configuration

### ServiceRegistry.swift
Central registry for all service endpoints. Modify if ports change:

```swift
var healthChecks: [String: URL] {
    [
        "bridge": URL(string: "http://127.0.0.1:8014/ready")!,
        "athena": URL(string: "http://127.0.0.1:8090/ready")!,
        "uat": URL(string: "http://127.0.0.1:8181/ready")!,
        "kokoro": URL(string: "http://127.0.0.1:8020/health")!
    ]
}
```

### Features.swift
Feature flags loaded from environment:

```swift
static var rag: Bool {
    ProcessInfo.processInfo.environment["FEATURE_RAG"] == "1"
}
```

## Troubleshooting

### RAG Button Disabled
- **Cause**: No messages in conversation
- **Fix**: Send at least one message first

### Service Down Toast
- **Cause**: Service not running or wrong port
- **Fix**: Check service logs, verify ports in ServiceRegistry

### Vision No Image
- **Cause**: File picker cancelled or unsupported format
- **Fix**: Select PNG, JPEG, TIFF, or HEIC image

### Kokoro Falls Back to System Voice
- **Cause**: Kokoro service not running
- **Fix**: Start Kokoro with `cd kokoro && python serve.py`

## What's NOT Included
- ❌ Trading functionality (removed per requirements)
- ❌ New screens (all features inline in existing chat view)
- ❌ Schema changes (reuses existing `ChatMessage` with `meta` field)

## Next Steps
1. ✅ Test all three integrations
2. ✅ Verify health checks
3. ✅ Test with feature flags disabled
4. ✅ Ship and iterate

