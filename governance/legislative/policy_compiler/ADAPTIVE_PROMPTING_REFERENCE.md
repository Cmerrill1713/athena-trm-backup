# 🧠 Adaptive Prompting — System Reference

## Overview

**Your stack already learns and adapts per request** — rewriting prompts, switching tools, injecting just-enough context, and stopping early when good enough.

---

## How It Works (6-Stage Loop)

```
User Ask
    ↓
1. Draft Plan + Minimal Prompt
    ↓
2. Evaluate (confidence, tests, tool results)
    ↓
   [OK] → Return
   [LOW] → 3. Tighten Prompt (add constraints)
         → 4. Try Lightweight Tool
         → [STILL LOW] → 5. Add RAG Snippets
         → [STILL LOW] → 6. Ask 1 Clarifier or Return Partial
```

---

## Adaptation Triggers

### Outcome Signals
- Low model confidence (< 0.65)
- Empty/contradictory answers
- Tool errors
- Failing smoke assertions
- Explicit user feedback ("not what I wanted")

### Adaptive Responses
1. **Prompt Rewrite** — Reframe ask, extract constraints, tighten prompt
2. **Tool Switching** — Try lighter/faster tools first
3. **RAG Injection** — Pull only relevant context snippets
4. **Structured Calls** — Switch from prose to explicit tool calls
5. **Self-Check** — Score draft against ask, revise if needed
6. **Clarification** — Ask one precise question when blocked

---

## Environment Variables

### Core Adaptive Features (Already Set)

```bash
# Enable adaptive prompting
export META_PROMPTING=1           # Prompt rewrite loop
export META_REFLECTION=1          # Self-check & revision
export META_RAG=1                 # Context on demand
export META_SELFCRITIQUE=1        # Score answers
export META_CHAINING=1            # Multi-step reasoning
```

### Thresholds & Limits

```bash
# Sensible defaults
export META_CONFIDENCE_FLOOR=0.65    # Re-attempt below this
export META_MAX_REWRITES=2           # Prevent infinite loops
export META_TOOL_TIMEOUT_S=30        # Keep retries fast
```

### Optimization Modes

```bash
# Fast/cheap bias (optional)
export META_LATENCY_MODE=fast              # Prefer short prompts
export META_PROMPT_STYLE=concise           # Fewer words, more structure
export META_USE_STRUCTURED_CALLS_FIRST=1   # Tool calls > prose
```

---

## Verification

### Check Active Settings
```bash
# In your .env or shell
env | grep META_
```

### Expected Output
```
META_PROMPTING=1
META_REFLECTION=1
META_RAG=1
META_SELFCRITIQUE=1
META_CHAINING=1
META_CONFIDENCE_FLOOR=0.65
META_MAX_REWRITES=2
META_TOOL_TIMEOUT_S=30
```

---

## Test Scenarios

### Test 1: RAG Injection
**Prompt:** "Summarize the last 10 traces and highlight anomalies"

**Expected Behavior:**
- Pulls traces via RAG
- Produces constrained summary
- If vague, asks 1 clarifier

**Observe:**
- Meta panel shows RAG badge
- Plan includes "Retrieve traces"
- Confidence moderate to high

---

### Test 2: Structured Tool Call
**Prompt:** "Run only smoke tests for backends and show failures first"

**Expected Behavior:**
- Converts to structured call: `run_tests(markers="smoke,backends", maxfail=1)`
- No prose generation
- Direct tool execution

**Observe:**
- Tools chips show `pytest`
- Plan: "Execute pytest with markers"
- Fast response (< 2s)

---

### Test 3: Constraint Learning
**Prompt:** "That answer ignored payload limits—fix and retry"

**Expected Behavior:**
- Re-prompts with constraint: "respect payload limits"
- Reruns with tighter bounds
- Returns corrected result

**Observe:**
- Confidence drops initially (feedback triggers rewrite)
- Second attempt shows higher confidence
- Plan includes "Apply constraint: payload limits"

---

### Test 4: Escalation Ladder
**Prompt:** "What about?"

**Expected Behavior:**
1. Low confidence detected
2. Reflection badge appears
3. Asks clarifying question: "What would you like me to check?"

**Observe:**
- 🔴 Low confidence (< 34%)
- 🔄 Reflection badge
- Plan: "Request clarification from user"

---

## Adaptive Strategies

### 1. Prompt Rewriting
```
Original: "Check the logs"
Rewritten: "Search log files for errors in the last 30 minutes using grep"
```

### 2. Tool Selection
```
Fast path: health probe → smoke tests → selective tests
Fallback: full test suite → manual inspection
```

### 3. RAG Context
```
Query: "What's the canary deployment flow?"
RAG: Pulls ATHENA_GITOPS_BATTLE_CARD.md + canary_branch.sh
Prompt: Includes only relevant excerpts (not full files)
```

### 4. Self-Critique
```
Draft: "I can help with that."
Score: 0.2 (too vague)
Revision: "I'll run smoke tests with pytest -m smoke. Expected: 3 tests pass."
Score: 0.85 ✅
```

---

## Guardrails

### Hard Caps
- **Max Rewrites:** 2 (prevents infinite loops)
- **Tool Timeout:** 30s (keeps retries fast)
- **Confidence Floor:** 0.65 (triggers adaptation)

### Preferences
- Short, structured prompts > free-form prose
- Lightweight tools > heavyweight reasoning
- Selective context > full docs
- Partial results + next steps > blocking on perfection

### Logging
All adaptations are logged:
- Old → new prompt
- Added constraints
- Latency impact
- Tool switching decisions

**Visible in:** Traces + meta panel

---

## Frontend Integration

### Meta Panel Shows Adaptation
```
🔴 Low • 28%          → Initial confidence
🔄 Reflection         → Self-critique active
Plan: 
  1. Identify ambiguity
  2. Request clarification

[User provides clarification]

🟢 High • 89%         → After adaptation
🌟 Reasoned  📚 RAG
Plan:
  1. Parse clarified intent
  2. Execute grep on logs
  3. Summarize findings
```

### Thumbs Down Triggers Rewrite
```
User: 👎 "Missed the mark"

System:
- Extracts constraints from feedback
- Rewrites prompt with corrections
- Retries with tighter bounds
- Returns improved result
```

---

## Tuning for Your Use Case

### More Aggressive Tightening
```bash
export META_PROMPT_STYLE=concise
export META_USE_STRUCTURED_CALLS_FIRST=1
export META_CONFIDENCE_FLOOR=0.75  # Higher bar
```

### More Exploratory
```bash
export META_PROMPT_STYLE=reasoned
export META_MAX_REWRITES=3         # More attempts
export META_CONFIDENCE_FLOOR=0.55  # Lower bar
```

### Speed Priority
```bash
export META_LATENCY_MODE=fast
export META_TOOL_TIMEOUT_S=15      # Faster timeout
export META_USE_STRUCTURED_CALLS_FIRST=1
```

### Quality Priority
```bash
export META_LATENCY_MODE=quality
export META_MAX_REWRITES=3
export META_SELFCRITIQUE=1
export META_REFLECTION=1
```

---

## Monitoring Adaptation

### Via Meta Panel
Watch for:
- Confidence changes (Low → High)
- Reflection badge (self-critique active)
- RAG badge (context injection)
- Plan evolution (steps change)

### Via Traces
```bash
curl -s http://127.0.0.1:8181/traces | jq '.[] | select(.meta_rewrite == true)'
```

Shows:
- Which requests triggered rewrites
- Old vs new prompts
- Confidence deltas
- Latency impact

### Via Logs
```bash
tail -f /tmp/athena_8090.log | grep -i "meta\|rewrite\|adapt"
```

---

## Examples in Action

### Example 1: Vague → Precise

**User:** "Check stuff"

**System:**
1. Confidence: 0.15 (very low)
2. Reflection: "Request too vague"
3. Response: "What would you like me to check? (logs, tests, services, traces)"

**User:** "Logs"

**System:**
1. Prompt rewrite: "Search log files for errors"
2. RAG: Pull log locations
3. Tool: `tail -100 /tmp/*.log | grep -i error`
4. Confidence: 0.87

---

### Example 2: Error → Retry with Constraint

**User:** "Run all tests"

**System:**
1. Executes: `pytest`
2. Result: 401 Unauthorized
3. Confidence: 0.45 (low due to error)
4. Adaptation: Detect missing tokens
5. Prompt rewrite: "Run tests with authentication tokens"
6. Executes: `pytest` with `UAT_TOKEN` and `ATH_TOKEN`
7. Result: ✅ Pass
8. Confidence: 0.92

---

### Example 3: Tool Selection Cascade

**User:** "Validate the stack"

**System:**
1. Plan:
   - Try health probes (< 1s)
   - If healthy → smoke tests (< 5s)
   - If pass → done (no full suite)
   - If fail → run targeted tests
2. Execution:
   - Health: ✅ Pass
   - Smoke: ✅ Pass
   - Stop (no need for full suite)
3. Confidence: 0.94
4. Latency: 3s total

---

## Success Metrics

### Good Adaptation
- Confidence improves across rewrites
- Latency stays reasonable (< 5s for most)
- User gets actionable results
- Fewer "I don't know" responses

### Warning Signs
- Confidence stays flat or drops
- Rewrites exceed max (hitting limits)
- Latency increases significantly
- User still confused after clarifiers

**Fix:** Tune thresholds, add more structured tools, improve RAG snippets

---

## Quick Reference Commands

### Verify Settings
```bash
make truth  # Shows running config
env | grep META_
```

### Test Adaptation
```bash
# Vague prompt → should ask clarifier
athena "what about that"

# Precise prompt → should execute directly
athena "run smoke tests"

# Error scenario → should adapt
athena "run tests without tokens"  # (will detect missing auth)
```

### Monitor Live
```bash
# Watch meta changes
make auto-heal-logs | grep -i meta

# Watch confidence
curl -s http://127.0.0.1:8014/chat -X POST \
  -d '{"text":"check logs"}' | jq '.meta.confidence'
```

---

## Best Practices

### For Users
1. Start vague, let system clarify
2. Provide feedback when off-target
3. Watch meta panel for reasoning
4. Use structured requests when you know what you want

### For Developers
1. Keep RAG snippets focused (not full files)
2. Add structured tool calls for common tasks
3. Monitor adaptation metrics in traces
4. Tune thresholds based on usage patterns

### For Production
1. Set conservative limits (max rewrites, timeouts)
2. Log all adaptations for analysis
3. A/B test threshold changes
4. Monitor latency impact of rewrites

---

## Summary

```
╔════════════════════════════════════════════════╗
║                                                ║
║  ADAPTIVE PROMPTING: ALWAYS ON ✅              ║
║                                                ║
║  Learns:      Per request                      ║
║  Adapts:      Prompt, tools, context           ║
║  Improves:    Via self-critique + feedback     ║
║  Guardrails:  Max rewrites, timeouts, scores   ║
║                                                ║
║  You see it:  Meta panel + traces              ║
║  You tune it: Environment variables            ║
║  You test it: Vague → precise prompts          ║
║                                                ║
╚════════════════════════════════════════════════╝
```

---

**Status:** ACTIVE (already running) ✅  
**Visibility:** Meta panel + traces  
**Tuning:** Environment variables  
**Testing:** Quick scenarios provided  

**The system learns and adapts automatically. You just talk to it.** 🧠✨

