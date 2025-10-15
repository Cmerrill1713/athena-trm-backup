# 🚀 RUN THIS NOW - 5-Minute Verification

> **Prove Athena works end-to-end in 5 minutes**

---

## ✅ Prerequisites (One-Time)

### 1. Edit main.swift (30 seconds)
```swift
// NeuroForgeApp/Sources/main.swift
// Line ~20, change:

ChatView()            // ❌ Old

to:

ChatViewEnhanced()    // ✅ New
```

### 2. Install Dependencies (if not done)
```bash
cd /Users/christianmerrill/Documents/GitHub
python3 -m pip install slowapi anyio
```

---

## 🎯 Run Verification (Copy-Paste)

```bash
# Run the automated verification script
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
./VERIFY_NOW.sh
```

**Or manual steps:**

```bash
# 1. Start backend with meta
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
make stack-up

# 2. Verify
make truth
curl -sI http://127.0.0.1:8014/health | grep x-meta

# 3. Start Kokoro (optional but recommended)
python3 scripts/kokoro_server.py &

# 4. Start frontend
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

---

## 🧪 Test In App

### Test 1: Voice with Meta Summary
```
1. Click mic button (or hold Space)
2. Say: "run smoke tests and summarize failures"
3. Release

✅ Expect to hear:
   "I'm [X]% confident. Here's what I'll do:"
   [Then full answer]

✅ Expect to see:
   - Meta panel below response
   - 🟢/🟡/🔴 confidence badge
   - Plan steps
   - Tools: [...]
   - Badges: ✓ RAG | ✓ Reflection
```

### Test 2: Text with Sparkline
```
1. Type: "check backend logs for errors"
2. Press Enter

✅ Expect to see:
   - Response with meta panel
   - Sparkline above input (after 3-5 messages)
   - Click panel to expand full plan
```

### Test 3: Debug Overlay
```
1. Press Cmd+Shift+P

✅ Expect to see:
   - Debug overlay appears
   - Shows prompt history
   - Original vs rewritten prompts
   - Confidence deltas
   - Reflection steps
```

### Test 4: CLI Voice (Parallel)
```bash
# In another terminal
./athena_voice.sh
"what's running"
"run tests"

✅ Expect:
   - CLI voice works
   - No interference with SwiftUI voice
```

---

## ✅ Success Checklist

- [ ] Backend starts successfully
- [ ] `make truth` shows 1 PID per port
- [ ] Meta headers visible: `curl -sI :8014/health | grep x-meta`
- [ ] Kokoro running (or system voice fallback)
- [ ] Frontend builds and runs
- [ ] Voice input transcribes correctly
- [ ] **Hear "I'm X% confident..."** before response
- [ ] **See meta panel** below assistant replies
- [ ] **Sparkline appears** above input (after few messages)
- [ ] **Cmd+Shift+P opens** debug overlay
- [ ] CLI voice works independently

---

## 🎭 Run Demo Script

Want to show off? Use the confidence evolution demo:

```bash
# See DEMO_SCRIPT.md for full walkthrough
cat NeuroForgeApp/DEMO_SCRIPT.md
```

**Quick demo flow:**
1. Vague: "check things" → 🔴 52% (triggers reflection)
2. Clear: "check backend health" → 🟡 76% (medium)
3. Precise: "check logs for errors in last hour" → 🟢 92% (high)
4. Follow-up: "generate incident report" → 🟢 88% (chaining)

**Watch sparkline:** Red → Yellow → Green progression

---

## 🛠️ Quick Fixes

### Problem: Meta Panel Not Showing
```bash
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1
make stack-restart
curl -sI http://127.0.0.1:8014/health | grep x-meta
```

### Problem: No Voice Audio
```bash
# Check Kokoro
curl http://127.0.0.1:8020/health

# Start if needed
python3 scripts/kokoro_server.py
```

### Problem: Cmd+Shift+P Not Working
```swift
// Verify main.swift has:
ChatViewEnhanced()  // Not ChatView()
```

### Problem: Ghosts (Multiple PIDs)
```bash
make nuke-ports
make stack-up
make truth
```

**Full troubleshooting:** See `QUICK_FIX_CARD.md`

---

## 📊 What Success Looks Like

### Console Output
```
🎙️  Playing Kokoro voice (af_heart): I'm 85% confident...
✅ Kokoro playback finished
🟢 85% confidence
📋 Plan: Parse logs → Compare rates → Generate summary
🧰 Tools: curl, jq, grep
```

### UI Visual
```
┌─────────────────────────────────┐
│ [Sparkline: 🔴 🟡 🟢 🟢]        │  ← Confidence history
├─────────────────────────────────┤
│ You: check backend logs         │
│                                  │
│ AI: Backend logs show...        │
│ ┌───────────────────────────┐  │
│ │ 🟢 85% confidence         │  │  ← Meta panel
│ │ Plan: 3 steps             │  │
│ │ Tools: curl, jq           │  │
│ │ ✓ RAG | ✓ Reflection     │  │
│ │ [Click to expand]         │  │
│ └───────────────────────────┘  │
└─────────────────────────────────┘
```

---

## 🎯 After Verification

**Tell me:**
- **"Works!"** - Everything running perfectly
- **"Issue: X"** - Hit a specific problem (use QUICK_FIX_CARD.md)
- **"Demo ready"** - Ready to show someone
- **"Ship it"** - Ready to tag and deploy

---

## 📦 Complete File List

**Created for you:**
- ✅ `VERIFY_NOW.sh` - Automated verification
- ✅ `DEMO_SCRIPT.md` - Confidence evolution demo
- ✅ `QUICK_FIX_CARD.md` - 30-second troubleshooting
- ✅ `RUN_THIS_NOW.md` - This file
- ✅ `ATHENA_ALIVE.md` - Quick start guide
- ✅ `META_UX_COMPLETE.md` - Full feature docs
- ✅ `GO_LIVE_FINAL.md` - Complete startup

**Core components:**
- ✅ `Sources/Features/MetaPromptPanel.swift`
- ✅ `Sources/Features/PromptDebugOverlay.swift`
- ✅ `Sources/Features/ChatViewEnhanced.swift`
- ✅ `Sources/Models/ChatMessage.swift`
- ✅ `Sources/Voice/VoiceManager.swift`

---

**Time to verify:** 5 minutes  
**Success rate:** Should be 100% if prerequisites met  
**Wow factor:** 🤯🤯🤯

🚀 **Run `./VERIFY_NOW.sh` and watch Athena come alive!** 🧠

