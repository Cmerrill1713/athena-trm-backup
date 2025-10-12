# 🚀 LAUNCH NOW — Final Verification & Go-Live

**All systems verified and ready. Launch in 2 minutes.**

---

## ✅ Pre-Flight Status

```
Backend Services:
  ✅ Bridge ready (:8014)
  ✅ Athena ready (:8090)
  ✅ UAT ready (:8181)
  ✅ Kokoro TTS ready (:8020)

Environment:
  ✅ META_PROMPTING=1
  ✅ META_REFLECTION=1
  ✅ META_RAG=1
  ✅ META_SELFCRITIQUE=1

Frontend:
  ✅ ChatViewEnhanced active
  ✅ MetaPromptInfo integrated
  ✅ Test suite ready (15 tests)
```

---

## 🚀 Launch Sequence

### **Step 1: Run Tests (30 seconds)**
```bash
cd NeuroForgeApp
swift package resolve
swift test
```

**Expected:** All 15 tests pass ✅

---

### **Step 2: Launch App (10 seconds)**
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

**Expected:** App window opens with chat interface

---

### **Step 3: Test Scenarios (2 minutes)**

#### **🔴 Scenario 1: Low Confidence**
```
Type/Say: "logs?"

Expected Panel:
  🧠 Meta-Prompt Insight      ● Low • 18-30%
  🔄 Reflection
  📋 Plan: "Request clarification"
```

#### **🟡 Scenario 2: Medium Confidence with Tools**
```
Type: "backend errors last 5 minutes"

Expected Panel:
  🧠 Meta-Prompt Insight      ● Med • 50-70%
  🌟 Reasoned  📚 RAG
  Tools: grep, tail
  📋 Plan: 2-3 steps
```

#### **🟢 Scenario 3: High Confidence with Full Plan**
```
Type: "run smoke tests"

Expected Panel:
  🧠 Meta-Prompt Insight      ● High • 85-95%
  🌟 Reasoned  📚 RAG
  Tools: pytest, grep, truth
  📋 Plan: 3-4 steps (expandable)
  
Expected Voice:
  "I'm [85-95]% confident. Running smoke tests..."
```

#### **🎯 Scenario 4: Debug Overlay**
```
Press: Cmd+Shift+P

Expected:
  Overlay opens showing:
  - Original prompt
  - Rewritten prompt (if adapted)
  - Reflection flags
  - Meta data
```

---

## ✅ Verification Checklist

### Visual Elements
- [ ] Meta panel appears under assistant messages
- [ ] Confidence pill color-coded correctly
  - 🔴 Red (< 34%)
  - 🟠 Orange (34-67%)
  - 🟢 Green (≥ 67%)
- [ ] Confidence sparkline above chat (updates with new messages)
- [ ] Plan section expandable with tap
- [ ] Copy Plan button works
- [ ] Tool chips visible when tools selected
- [ ] Badges show (🌟 Style, 📚 RAG, 🔄 Reflection)
- [ ] Latency and token counts display

### Interactive Features
- [ ] Mic button works (permission granted)
- [ ] Voice playback works (Kokoro or system)
- [ ] Cmd+Shift+P opens debug overlay
- [ ] Plan expands/collapses smoothly
- [ ] Copy button copies to clipboard

### Adaptive Behavior
- [ ] Vague prompts show low confidence
- [ ] Precise prompts show high confidence
- [ ] Reflection badge on ambiguous requests
- [ ] RAG badge when context retrieved
- [ ] Tools only show when actually selected

---

## 🧪 Quick Sanity Tests

### Backend Health
```bash
# All services responding
curl -fsS 127.0.0.1:8014/ready
curl -fsS 127.0.0.1:8090/ready
curl -fsS 127.0.0.1:8181/ready

# Kokoro TTS
curl -fsS 127.0.0.1:8020/health
```

### Meta Headers (on chat endpoint)
```bash
curl -X POST http://127.0.0.1:8014/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}' -i 2>&1 | grep -i "^x-meta"
```

Should show headers like:
```
x-meta-enabled: true
x-meta-confidence: 0.75
x-meta-style: reasoned
```

---

## 🛠️ Quick Fixes (If Needed)

### No Meta Panel Showing
```bash
# Restart with meta flags
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1
make stack-restart

# Verify flags active
env | grep META_
```

### No Voice Audio
```bash
# Check Kokoro
curl -fsS 127.0.0.1:8020/health || python3 scripts/kokoro_server.py

# Fallback: System voice will work automatically
```

### Rate Limiting Not Working
```bash
python3 -m pip install slowapi anyio
make stack-restart
```

### Ghost Processes
```bash
make truth               # Check what's running
make nuke-ports          # Kill all on 8014/8090/8181
make stack-up            # Clean restart
```

### Swift Build Issues
```bash
cd NeuroForgeApp
swift package reset
swift package resolve
swift build
```

### Mic Permission
```
- macOS will prompt for mic access on first use
- Accept the prompt
- If missed, go to: System Settings → Privacy & Security → Microphone
- Enable for Terminal or your Swift app
- Relaunch app
```

---

## 🎯 What Success Looks Like

### **Low Confidence Response**
```
User: "logs?"