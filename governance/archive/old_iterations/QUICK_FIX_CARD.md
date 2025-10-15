# 🛠️ Quick Fix Card - 30-Second Troubleshooting

> **Fast fixes for common issues**

---

## 🔴 Meta Panel Not Showing

### Symptom
- Assistant replies but no confidence panel appears
- No sparkline above input

### Fix
```bash
# 1. Check backend has meta enabled
echo $META_PROMPTING  # Should be "1"

# 2. If not, restart with meta
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
make stack-restart

# 3. Test meta headers
curl -si http://127.0.0.1:8014/health | grep -i 'x-meta'
```

### Verify
- Should see headers like `x-meta-confidence`, `x-meta-plan`
- If not, backend isn't returning meta data

---

## 🔴 No Voice Audio

### Symptom
- Click mic, transcript appears, but no voice response

### Fix A: Kokoro Not Running
```bash
# Check Kokoro
curl http://127.0.0.1:8020/health

# If fails, start it
python3 scripts/kokoro_server.py

# Or auto-start
launchctl load ~/Library/LaunchAgents/com.athena.kokoro.plist
```

### Fix B: System Voice Fallback
```bash
# Verify system voice works
say "Testing system voice"

# If works, app will use it when Kokoro unavailable
# Check console: "⚠️  Using system voice (Kokoro unavailable)"
```

### Fix C: Permissions
```bash
# Check mic permission
# System Settings → Privacy & Security → Microphone
# Ensure NeuroForgeApp is checked

# Restart app after granting permission
```

---

## 🔴 No 429s in Guardrail Test

### Symptom
```bash
make guardrails-smoke
# Shows all 200s, no 429s
```

### Fix
```bash
# Install rate limiting deps
python3 -m pip install slowapi anyio

# Restart backend
make stack-restart

# Test again
make guardrails-smoke
# Should now see some 429s
```

---

## 🔴 Cmd+Shift+P Not Opening Debug Overlay

### Symptom
- Press Cmd+Shift+P, nothing happens

### Fix A: Wrong View
```swift
// Check main.swift
// Should be:
ChatViewEnhanced()  // ✅

// Not:
ChatView()  // ❌
```

### Fix B: Keyboard Shortcut Conflict
```swift
// In ChatViewEnhanced.swift
// Try different shortcut if needed:
.keyboardShortcut("d", modifiers: [.command, .shift])
```

---

## 🔴 Backend Won't Start

### Symptom
```bash
make stack-up
# Errors about ports in use
```

### Fix
```bash
# Nuclear option - kill everything
make nuke-ports

# Clean start
make stack-up

# Verify
make truth
```

---

## 🔴 CLI Voice Not Working

### Symptom
```bash
./athena_voice.sh
# Command not found or permission denied
```

### Fix
```bash
# Make executable
chmod +x athena_voice.sh
chmod +x scripts/*.sh

# Source setup
bash setup_voice_control.sh
source ~/.zshrc  # or ~/.bashrc

# Test
athena "what's running"
```

---

## 🔴 Sparkline Not Updating

### Symptom
- Meta panels show, but sparkline above input is empty

### Fix
- **Sparkline requires 3-5 messages minimum**
- Send a few messages first
- Each assistant response with meta data adds a point
- Takes a few exchanges to populate

### Verify
```swift
// In ChatViewEnhanced
// Check this is present:
if !confidenceHistory.isEmpty && showMetaPanels {
    ConfidenceSparkline(history: confidenceHistory)
}
```

---

## 🔴 "Mock Mode" Instead of Real

### Symptom
- Headers show `x-mode: mock` instead of `x-mode: real`

### Fix
```bash
# Restart in real mode
make stack-down
USE_MOCK=0 ENV=dev make stack-up

# Verify
curl -sI http://127.0.0.1:8014/health | grep x-mode
# Should show: x-mode: real
```

---

## 🔴 Ghosts (Multiple PIDs per Port)

### Symptom
```bash
make truth
# Shows multiple PIDs on same port
```

### Fix
```bash
# The forensic ghostbuster
make nuke-ports
make stack-up
make truth
# Should show 1 PID per port now
```

---

## 🔴 SwiftUI Build Errors

### Symptom
```
Error: Cannot find 'MetaPromptPanel' in scope
```

### Fix
- Ensure all new files are added to Xcode project
- Or rebuild:
```bash
cd NeuroForgeApp
swift package clean
swift build
```

---

## 🔴 Voice Meta Summary Not Speaking

### Symptom
- Voice works, but no "I'm X% confident" spoken first

### Fix A: Setting Disabled
```swift
// Check in ChatViewEnhanced
@AppStorage("metaVoiceSummary") private var metaVoiceSummary = true
// Should be true
```

### Fix B: No Meta Data
- If backend not returning meta, summary can't be generated
- See "Meta Panel Not Showing" fix above

---

## 🔴 Timeout/504 Test Missing

### Symptom
```bash
make guardrails-smoke
# No timeout test runs
```

### Fix
```bash
# Set timeout env var
export REQ_TIMEOUT_S=30

# Restart
make stack-restart

# Test
make guardrails-smoke
```

---

## 🚀 Fast Validation After Fix

```bash
# Quick health check
make stack-status

# Full proof
make tier4-proof

# Meta headers
curl -si http://127.0.0.1:8014/health | grep -i x-meta

# Kokoro
curl http://127.0.0.1:8020/health

# CLI voice
athena "what's running"
```

---

## 📞 Still Stuck?

### Show Me These
```bash
# 1. Stack health
make truth

# 2. Meta headers
curl -sI http://127.0.0.1:8014/health | grep x-

# 3. Kokoro status
curl http://127.0.0.1:8020/health

# 4. Last 20 lines of logs
tail -20 logs/bridge_8014.log

# 5. Environment
env | grep META
```

**Paste these outputs and describe the symptom.**

---

**Most issues fix in < 30 seconds with the right command.** 🎯

