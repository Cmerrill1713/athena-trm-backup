# 🎭 Athena Demo Script - Confidence Evolution

> **Show Athena thinking, planning, and growing more confident**

---

## Setup (30 seconds)

```bash
# Start everything
cd /Users/christianmerrill/Documents/GitHub
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1
make stack-up

# Start Kokoro (optional but recommended for demo)
python3 scripts/kokoro_server.py &

# Start frontend (after editing main.swift)
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

---

## Demo Flow (3 minutes)

### Scene 1: Vague Query → Reflection Triggered

**You:** [Click mic] "check things"

**Athena thinks:**
- 🔴 Confidence: ~50% (low)
- Triggers reflection ("too vague")

**Athena speaks:** 
*"I'm 52% confident. Let me clarify what you need:"*

**Meta panel shows:**
- 🔴 52% confidence
- Plan: 
  1. Identify ambiguous request
  2. Request clarification
  3. Offer common checks
- Tools: []
- ✓ Reflection (triggered due to vagueness)

**Sparkline:** Red dot appears

---

### Scene 2: Clearer Query → Medium Confidence

**You:** [Click mic] "check backend health"

**Athena thinks:**
- 🟡 Confidence: ~75% (medium)
- More specific, less reflection needed

**Athena speaks:**
*"I'm 76% confident. Here's what I'll do:"*

**Meta panel shows:**
- 🟡 76% confidence
- Plan:
  1. Query backend health endpoint
  2. Check response status
  3. Parse health indicators
- Tools: [curl]
- ✓ RAG (pulling endpoint docs)

**Sparkline:** Yellow dot added (trending up)

---

### Scene 3: Precise Query → High Confidence

**You:** [Click mic] "check backend logs for errors in the last hour and summarize top 3 failures"

**Athena thinks:**
- 🟢 Confidence: ~92% (high)
- Clear, specific, actionable

**Athena speaks:**
*"I'm 92% confident. Here's my plan:"*

**Meta panel shows:**
- 🟢 92% confidence
- Plan:
  1. Tail backend logs from last hour
  2. Filter for ERROR level
  3. Group by error message
  4. Sort by frequency
  5. Return top 3 with counts
- Tools: [tail, grep, sort, uniq]
- ✓ RAG | ✓ Reflection | ✓ Self-critique

**Sparkline:** Green dot added (high confidence achieved)

---

### Scene 4: Meta-Aware Follow-up

**You:** [Click mic] "now generate an incident report"

**Athena thinks:**
- 🟢 Confidence: ~88% (high, using context)
- Leverages previous query results

**Athena speaks:**
*"I'm 88% confident. I'll use the previous findings:"*

**Meta panel shows:**
- 🟢 88% confidence
- Plan:
  1. Use cached error analysis
  2. Add timestamps and context
  3. Format as incident report
  4. Include mitigation steps
- Tools: [jq, date]
- ✓ Chaining (using previous results)
- ✓ RAG (incident report template)

**Sparkline:** Green trend continues

---

## Key Moments to Point Out

### 1. **Confidence Evolution** (Visual)
```
Scene 1: 🔴 52%  (vague → reflection)
Scene 2: 🟡 76%  (clearer → medium)
Scene 3: 🟢 92%  (precise → high)
Scene 4: 🟢 88%  (context → chaining)
```

**Sparkline shows:** Red → Yellow → Green trend

### 2. **Meta Voice Summary** (Audio)
Each response starts with:
- "I'm X% confident..."
- Gives you trust signal before answer

### 3. **Expandable Details** (Interaction)
- Click meta panel → see full plan
- See exactly what tools Athena will use
- Understand her reasoning process

### 4. **Debug Overlay** (Developer Mode)
Press Cmd+Shift+P:
- See "check things" → "Check backend health metrics, error rates, and service status"
- Confidence delta: +40%
- Reflection steps: ["Clarify ambiguous terms", "Add timeframe", "Specify outputs"]

### 5. **Parallel CLI Voice** (No Conflicts)
While app is open, in terminal:
```bash
./athena_voice.sh
"run smoke tests"    # Works independently
"enable watchdog"    # No interference
```

---

## Talking Points

### For Technical Audience
> "Notice how confidence increases as queries become more specific. Low confidence triggers reflection—Athena literally asks herself 'is this clear enough?' before responding. The meta panel shows her reasoning: plan steps, tools she'll use, and which AI techniques are active (RAG, reflection, self-critique)."

### For Business Audience
> "Athena doesn't just answer—she shows her work. You see her confidence level, her plan, and what tools she's using. If she's uncertain, she tells you and reflects on how to clarify. It's like having a transparent ops engineer who explains their thinking."

### For Demo Wow Moment
> "Watch the sparkline—red to yellow to green. That's Athena learning to understand you better. And hear how she speaks: 'I'm 92% confident' before answering. That's trust, not black-box AI."

---

## Fallback Scenarios

### If Kokoro Not Running
- System voice speaks instead
- Still says "I'm X% confident"
- Meta panel still works
- Just less natural sounding

### If Meta Headers Missing
- Console shows: "⚠️ No meta data"
- Panel won't render
- Fix: Restart backend with `META_PROMPTING=1`

### If Sparkline Empty
- Send 3-5 messages first
- Takes a few exchanges to populate
- Each response adds a dot

---

## Quick Reset (Between Demos)

```bash
# Clear history
make stack-down
make stack-up

# Restart frontend
# App will start fresh
```

---

## One-Liner Summary

*"Athena now thinks out loud, shows her confidence in real-time, and explains her plan before executing. It's transparent AI—you see and hear her reasoning process."*

---

**Demo Time:** ~3 minutes  
**Setup Time:** ~30 seconds  
**Wow Factor:** 🤯🤯🤯

🎙️ **Let Athena show herself thinking.** 🧠✨

