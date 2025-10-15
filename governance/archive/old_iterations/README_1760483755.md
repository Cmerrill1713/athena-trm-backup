# NeuroForge Swift UI

Clean, model-agnostic Swift frontend for your AI orchestration backend.

## Features

✅ **Model-agnostic routing** – No hard-coded model names, backend orchestrates
✅ **Bulletproof text input** – Fixed visibility, no white/clear text issues
✅ **Smart keyboard handling** – Enter to send, Shift+Enter for newlines
✅ **Health monitoring** – Live connection status with reconnect
✅ **UI test scaffolding** – Accessibility identifiers for automation

## Quick Start

### Run from Terminal

```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
API_BASE=http://localhost:8014 swift run
```

### Open in Xcode

```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
xed .
```

Then:
1. Select the **NeuroForgeApp** scheme
2. Product → Run (⌘R)
3. Optional: Edit Scheme → Environment Variables:
   - `API_BASE` = `http://localhost:8014`

## Architecture

```
Sources/
├── main.swift                    # App entry point
├── Config/
│   └── APIBase.swift            # Backend URL resolver
├── Network/
│   ├── APIClient.swift          # HTTP client
│   └── APIError.swift           # Error types
├── Routing/
│   └── TaskClassifier.swift    # Task routing types
├── Features/
│   ├── ChatView.swift           # Main chat UI
│   └── KeyCatchingTextView.swift # Smart text input
└── Diagnostics/
    └── HealthBanner.swift       # Connection status
```

## Backend Requirements

Your backend should expose:

- `GET /health` → 200 OK
- `POST /api/chat` → `{ "text": "response" }`

Request body:
```json
{
  "kind": "smalltalk|coding|reasoning|visionDescribe|ragQuery",
  "text": "user input",
  "imageBase64": null
}
```

## Keyboard Shortcuts

- **Enter** – Send message
- **Shift+Enter** – Insert newline
- **⌘Q** – Quit

## Sanity Checklist

1. ✅ Backend running at port 8014?
2. ✅ Run app with `API_BASE=http://localhost:8014`
3. ✅ Type in box → text visible (not white/clear)
4. ✅ Press Enter → message sends
5. ✅ Press Shift+Enter → newline inserted
6. ✅ Health banner shows "Connected"
7. ✅ "Reconnect" button works

## Fallback Ports

If `API_BASE` env var not set, tries these in order:
1. `http://localhost:8014` (default)
2. `http://localhost:8888`
3. `http://localhost:8013`
4. `http://localhost:8080`

## UI Testing

Accessibility identifiers for automation:
- `health_banner` – Connection status banner
- `chat_input` – Message input field
- `chat_response` – Latest response message

## Troubleshooting

**White/invisible text?**
→ Fixed via `KeyCatchingNSTextView.becomeFirstResponder()` color setup

**Enter not sending?**
→ Uses `interpretKeyEvents` + `doCommand(by:)` for proper key handling

**Backend unreachable?**
→ Check Health banner, click "Reconnect", verify port 8014 is listening

**Want to change backend URL?**
→ Set `API_BASE` environment variable before running
