# 🟢 GO / VERIFY / ROLLBACK - v0.9.4-meta-ux

> **1-page launch card - copy-paste ready**

---

## 1️⃣ GO (Copy-Paste)

```bash
cd /Users/christianmerrill/Documents/GitHub
./GREEN_LIGHTS.sh  # All green ✅

# Start stack with meta on
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1 META_SELFCRITIQUE=1
make stack-up && make truth

# Optional TTS (or rely on system voice)
python3 scripts/kokoro_server.py || true &

# Run the app
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

**✅ Prerequisite:** `main.swift` line ~20: `ChatView()` → `ChatViewEnhanced()`

---

## 2️⃣ FRONTEND ACCEPTANCE (2 min)

**Do these 4 in the app. If all hit → SHIP IT:**

### Test 1: Voice Low→High Confidence Ramp
- Say **"logs?"** → 🔴 Low confidence + ✓ Reflection badge
- Say **"backend errors"** → 🟡 Medium + ✓ RAG badge
- Say **"top 3"** → 🟢 High + plan + tool chips

### Test 2: Meta Panel Shows
- Confidence pill (color-coded)
- Badges (RAG, Reflection, Chaining)
- Tools (tail, grep, sort)
- Plan (expand/collapse)

### Test 3: Debug Overlay
- Press **Cmd+Shift+P**
- Shows original vs rewritten prompts
- Shows confidence deltas

### Test 4: Audio
- Hear: **"I'm X% confident..."**
- Kokoro voice (or system voice fallback)

---

## 3️⃣ SHIP

```bash
cd /Users/christianmerrill/Documents/GitHub
git add -A
git commit -m "Meta Dashboard + Adaptive UX: confidence, plan, tools, voice"
git tag -a v0.9.4-meta-ux -m "Meta UX end-to-end"
git push && git push origin v0.9.4-meta-ux
```

---

## 🛠️ FAST FIXES (30s each)

```bash
# No meta panel
export META_PROMPTING=1 && make stack-restart

# No voice
python3 scripts/kokoro_server.py

# No 429s in guardrails test
python3 -m pip install slowapi anyio && make stack-restart

# Weird results / ghosts
make truth && make nuke-ports && make stack-up

# Swift deps glitch
cd NeuroForgeApp && swift package resolve
```

---

## ✅ WHAT "GREEN" MEANS (Objective)

- `/ready` returns `{"status":"ready"}` for :8014, :8090, :8181
- Meta panel renders for assistant replies (confidence + plan + tools)
- Kokoro (or system voice) speaks confidence preamble
- Debug overlay opens (Cmd+Shift+P) and shows rewritten prompt
- Confidence sparkline moves 🔴 → 🟡 → 🟢 during 3-message ramp

---

## 🔙 ROLLBACK (10s, safe)

```bash
git reset --hard v0.9.3-tier3-4
make stack-restart
# (Optional) switch main.swift back to ChatView()
```

---

## 👀 POST-LAUNCH WATCH (First 15 min)

```bash
# Prometheus (error rate <1%, p95 <250ms)
open http://localhost:9090

# Grafana (SLO dashboard)
open http://localhost:3001

# Watch adaptations
tail -f logs/athena_8090.log | grep -i meta

# Auto-heal status
make auto-heal-status
# Should stay "healthy", heals <60s if chaos triggered
```

---

## 🎭 BONUS QUICK DEMO (90s)

**Perfect for showing off:**

1. Say: **"logs?"**
   - See: 🔴 Low confidence
   - See: ✓ Reflection badge
   - Hear: "I'm 18% confident. What logs should I check?"

2. Say: **"backend errors"**
   - See: 🟡 Medium confidence
   - See: ✓ RAG badge
   - See: Tools: [tail, grep]
   - Sparkline: 🔴 🟡

3. Say: **"last hour top 3"**
   - See: 🟢 High confidence
   - See: 3-4 step plan
   - See: Tools: [sort, uniq]
   - Sparkline: 🔴 🟡 🟢

4. Press **Cmd+Shift+P**
   - Show rewrite history
   - Audience sees "brain working"
   - Original: "logs?"
   - Rewritten: "Check backend logs for ERROR level entries in last hour..."
   - Δ +44% confidence

---

## 📊 SUCCESS METRICS

**Immediate (2 min):**
- ✅ All 4 acceptance tests pass
- ✅ Sparkline shows learning trend
- ✅ Voice conveys confidence
- ✅ Debug overlay works

**Post-launch (15 min):**
- ✅ Error rate <1%
- ✅ P95 latency <250ms
- ✅ Auto-heal <60s recovery
- ✅ Meta adaptations logged

---

## 🎯 IF ANYTHING HICCUPS

**Paste one line describing symptom:**
- "Meta panel not showing"
- "Voice not speaking"
- "Debug overlay won't open"
- "Sparkline empty"

**I'll give pinpoint fix.**

---

## 🏆 WHAT YOU'RE SHIPPING

**v0.9.4-meta-ux:**
- 🧠 Transparent AI (see thinking)
- 📊 Confidence tracking (🔴→🟡→🟢)
- 🎙️ Voice control (hear confidence)
- 🔍 Prompt debugging (see rewrites)
- 🤖 Self-healing (autopilot)
- 📚 Complete docs (30+ guides)

**This is next-level AI UX.**

---

## ✅ FINAL CHECKLIST

- [ ] `./GREEN_LIGHTS.sh` passes
- [ ] main.swift edited
- [ ] 4 acceptance tests pass
- [ ] Meta panels visible
- [ ] Sparkline updates
- [ ] Debug overlay works
- [ ] Voice speaks confidence
- [ ] **READY TO SHIP**

---

**Status:** 🟢 GO FOR LAUNCH  
**Version:** v0.9.4-meta-ux  
**Rollback:** v0.9.3-tier3-4

🚀 **LAUNCH, VERIFY, TAG!**

