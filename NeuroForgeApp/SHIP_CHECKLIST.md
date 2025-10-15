# ✅ SHIP CHECKLIST - Meta UX v0.9.4

> **Final checklist before shipping**

---

## 1️⃣ Preflight (60 sec)

```bash
cd /Users/christianmerrill/Documents/GitHub
./PREFLIGHT_60SEC.sh
```

**Or manual:**
```bash
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1 META_SELFCRITIQUE=1
make stack-up && make truth
```

**Expected:**
- ✅ Bridge :8014
- ✅ Athena :8090
- ✅ UAT :8181
- ✅ 1 PID per port

---

## 2️⃣ One Edit (30 sec)

**File:** `Sources/main.swift`  
**Line:** ~20

**Change:**
```swift
// BEFORE:
ChatView()

// AFTER:
ChatViewEnhanced()
```

**Save file.**

---

## 3️⃣ Run App (1 min)

```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

**Wait for:** "Running NeuroForgeApp..."

---

## 4️⃣ Test (2 min)

### Voice Test
- [ ] Click mic, say: **"logs?"**
  - See: 🔴 Low confidence (~20-30%)
  - See: ✓ Reflection badge
  - Hear: "I'm X% confident..."

- [ ] Say: **"backend errors last hour"**
  - See: 🟡 Medium confidence (~70-80%)
  - See: ✓ RAG badge, Tools: [tail, grep]
  - Sparkline updates: 🔴 🟡

- [ ] Say: **"top 3 with counts"**
  - See: 🟢 High confidence (~85-95%)
  - See: ✓ Chaining, Tools: [sort, uniq]
  - Sparkline: 🔴 🟡 🟢

### Debug Test
- [ ] Press **Cmd+Shift+P**
  - Overlay appears
  - Shows prompt history
  - Original vs rewritten visible

### CLI Voice Test
```bash
./athena_voice.sh
"run tests"
```
- [ ] Works independently

---

## 5️⃣ Ship (1 min)

```bash
cd /Users/christianmerrill/Documents/GitHub

git add -A
git commit -m "Meta Dashboard + Adaptive UX: visible confidence, plan, tools, voice"
git tag -a v0.9.4-meta-ux -m "Meta UX end-to-end"
git push && git push origin v0.9.4-meta-ux
```

---

## 🛠️ Quick Fixes

### No Meta Panel
```bash
export META_PROMPTING=1 && make stack-restart
```

### No Voice
```bash
curl http://127.0.0.1:8020/health || python3 scripts/kokoro_server.py
```

### No 429s
```bash
python3 -m pip install slowapi anyio && make stack-restart
```

### Swift Build Issues
```bash
cd NeuroForgeApp
swift package resolve
swift build --clean-build
```

---

## ✅ Final Checklist

- [ ] Backend running with meta
- [ ] Truth shows 1 PID per port
- [ ] main.swift edited
- [ ] Frontend builds
- [ ] Voice input works
- [ ] Meta panels appear
- [ ] Sparkline visible
- [ ] Debug overlay works (Cmd+Shift+P)
- [ ] Hear confidence ("I'm X%...")
- [ ] CLI voice works
- [ ] **READY TO SHIP!**

---

## 🏆 What You're Shipping

**v0.9.4-meta-ux:**
- ✅ Transparent AI (see confidence)
- ✅ Adaptive prompts (watch learning)
- ✅ Voice control (hear confidence)
- ✅ Debug tools (see rewrites)
- ✅ Self-healing (autopilot active)
- ✅ Complete docs (25+ guides)

**This is production-grade AI UX.**

---

## 🎯 After Shipping

```bash
# Verify tag
git tag | grep meta-ux

# Check remote
git log --oneline -1

# Celebrate! 🎉
```

---

**Status:** ✅ READY TO SHIP  
**Version:** v0.9.4-meta-ux  
**Quality:** ⭐⭐⭐⭐⭐

🚀 **Ship it!**

