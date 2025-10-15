# NeuroForge Swift UI - Quick Start

## ✅ Setup Complete!

Your bulletproof Swift UI is ready to run. All files are in place:

```
NeuroForgeApp/
├── Package.swift              # Swift package config
├── run.sh                     # One-command launcher
├── Sources/
│   ├── main.swift            # @main app entry
│   ├── Config/
│   │   └── APIBase.swift     # Backend URL resolver (8014→8888→8013→8080)
│   ├── Network/
│   │   ├── APIClient.swift   # HTTP client with /health + /api/chat
│   │   └── APIError.swift    # Error handling
│   ├── Routing/
│   │   └── TaskClassifier.swift # ChatTask & ChatTaskKind enums
│   ├── Features/
│   │   ├── ChatView.swift    # Main chat interface
│   │   └── KeyCatchingTextView.swift # Enter/Shift+Enter magic
│   └── Diagnostics/
│       └── HealthBanner.swift # Green/red connection status
└── Tests/
    └── AppUITests/
        └── UITestHelpers.swift
```

---

## 🚀 Run It Now

### Option 1: Quick Script (Recommended)

```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
./run.sh
```

### Option 2: Swift CLI

```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
API_BASE=http://localhost:8014 swift run
```

### Option 3: Xcode

```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
xed .
```

Then **⌘R** to run.

---

## 🎯 What You Get

### ✅ Bulletproof Text Visibility
- No white/clear text issues
- `KeyCatchingNSTextView` sets:
  - `textColor = .labelColor`
  - `backgroundColor = .textBackgroundColor`
  - `insertionPointColor = .labelColor`

### ✅ Smart Keyboard Handling
- **Enter** → Send message
- **Shift+Enter** → Insert newline
- Uses `interpretKeyEvents` + `doCommand(by:)` for proper routing

### ✅ Model-Agnostic Routing
- No hard-coded model names in UI
- Sends `ChatTask` with `ChatTaskKind`:
  - `smalltalk` – Quick responses
  - `coding` – Code-related queries
  - `reasoning` – "Why" questions
  - `visionDescribe` – Image analysis
  - `ragQuery` – Document search

### ✅ Health Monitoring
- Green dot = Backend connected
- Red dot = Disconnected
- **Reconnect** button for manual check
- Auto-checks on launch via `.task {}`

### ✅ UI Test Ready
Accessibility identifiers:
- `health_banner`
- `chat_input`
- `chat_response`

---

## 🔧 Backend Requirements

Your backend needs these endpoints:

### GET /health
```bash
curl http://localhost:8014/health
# → 200 OK
```

### POST /api/chat
```bash
curl -X POST http://localhost:8014/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "smalltalk",
    "text": "Hello!",
    "imageBase64": null
  }'

# → { "text": "Hi there! How can I help?" }
```

---

## 🧪 Quick Test Checklist

1. ✅ **Backend running?**
   ```bash
   curl http://localhost:8014/health
   ```

2. ✅ **Launch app:**
   ```bash
   ./run.sh
   ```

3. ✅ **Text visible?**
   - Type in the input box
   - Text should be clearly visible (not white/clear)

4. ✅ **Enter sends?**
   - Type "Hello"
   - Press **Enter** → message sends

5. ✅ **Shift+Enter newlines?**
   - Type "Line 1"
   - Press **Shift+Enter** → cursor moves to new line
   - Type "Line 2"

6. ✅ **Health banner works?**
   - Green dot = connected
   - Click "Reconnect" → re-checks backend

7. ✅ **Messages appear?**
   - After sending, you see:
     - `You: [your message]`
     - `AI: [response]`

---

## 🐛 Troubleshooting

### Text is invisible/white
**Already fixed!** `KeyCatchingNSTextView.becomeFirstResponder()` sets all colors.

### Enter key doesn't send
**Already fixed!** Uses `interpretKeyEvents` instead of `onKeyDown`.

### Backend unreachable
1. Check health banner (red dot)
2. Verify backend: `curl http://localhost:8014/health`
3. Try fallback ports: 8888, 8013, 8080
4. Set custom: `API_BASE=http://localhost:9000 swift run`

### Build fails
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
swift build --clean-build
```

---

## 🎨 Next Steps

### Add Image Picker (Vision Support)

Want to add image uploads? Add to `ChatView.swift`:

```swift
@State private var selectedImage: NSImage?

// In body, before KeyCatchingTextView:
if let img = selectedImage {
    Image(nsImage: img)
        .resizable()
        .frame(height: 100)
}

Button("Pick Image") {
    let panel = NSOpenPanel()
    panel.allowedContentTypes = [.png, .jpeg]
    panel.begin { resp in
        if resp == .OK, let url = panel.url,
           let img = NSImage(contentsOf: url) {
            selectedImage = img
        }
    }
}
```

Then in `send()`:
```swift
let base64 = selectedImage?.tiffRepresentation?
    .base64EncodedString()
let task = ChatTask(kind: kind, text: text, imageBase64: base64)
```

### Add Dark Mode Toggle

Already works! SwiftUI respects system dark mode via `.labelColor` / `.textBackgroundColor`.

### Run UI Tests

1. Open in Xcode: `xed .`
2. Product → Test (⌘U)
3. Tests use `health_banner`, `chat_input`, `chat_response` identifiers

---

## 📦 File Summary

| File | Purpose |
|------|---------|
| `main.swift` | App entry with `@main` |
| `APIBase.swift` | Backend URL + fallback ports |
| `APIClient.swift` | HTTP client (`health()`, `chat()`) |
| `APIError.swift` | Error types |
| `TaskClassifier.swift` | `ChatTask` & `ChatTaskKind` |
| `HealthBanner.swift` | Connection status UI |
| `KeyCatchingTextView.swift` | Text input with Enter/Shift+Enter |
| `ChatView.swift` | Main chat interface |
| `run.sh` | One-command launcher |

---

## 🚢 Ready to Ship!

You now have:
- ✅ Model-agnostic routing
- ✅ Bulletproof text input
- ✅ Smart keyboard handling
- ✅ Health monitoring
- ✅ UI test scaffolding

**Run it:** `./run.sh`
**Test it:** Type, press Enter, watch it work
**Tinker:** Add image picker, custom themes, etc.

Enjoy! 🎉
