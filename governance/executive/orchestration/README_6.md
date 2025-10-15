# NeuroForge Orchestrator

**Agent-Agnostic Capability Routing**

Routes by capability + policy + bandit, completely neutral about which agent/model provides a capability.

---

## 🎯 **PHILOSOPHY**

**Route by CAPABILITY, never by agent/model name:**
- ✅ "I need summarization" (capability)
- ❌ "I need GPT-4" (agent name)

**Benefits:**
- Hot-swappable providers
- A/B testing via shadow execution
- Multi-armed bandit optimization
- Policy-based constraints
- Complete audit trail

---

## 🚀 **QUICK START**

```bash
cd orchestrator

# Install
make install

# Run preflight
make preflight

# Run tests
make test

# Run demo
make demo

# Or all at once
make all
```

---

## 📋 **COMPONENTS**

### **Core Files:**
- `contracts.py` - Capability IO contracts (typed)
- `registry.py` - Provider registry (capability-based)
- `loader.py` - Dynamic provider loading
- `router.py` - Main routing logic with shadow execution
- `scorer.py` - Thompson sampling bandit
- `features.py` - Feature extraction for routing
- `telemetry.py` - Trace logging
- `policies.yaml` - Routing policies and constraints

### **Memory:**
- `memory/vector_store.py` - Simple in-memory vector store
- `memory/hygiene.py` - Deduplication and pinning

### **Providers:**
- `providers/capability_stub.py` - Example provider

### **Tests:**
- `tests/test_smoke.py` - Smoke tests

---

## 🔧 **USAGE**

### **Basic:**
```python
from router import run_capability

record = {
    "id": "TASK-1",
    "subject": "User question",
    "body": "How do I reset my password?",
    "sla_mins_left": 120
}

result = run_capability("summarize", record, {"max_tokens": 256})

print(result["output"]["tldr"])
print(result["trace"]["duration_ms"])
```

### **With Custom Provider:**
```python
# 1. Create your provider (respects contract)
# providers/my_provider.py
def run(capability_input):
    # Your logic here
    return {
        "tldr": "...",
        "facts": [...],
        "next_action": "...",
        # ... rest of contract
    }

# 2. Register it
from registry import register_provider

register_provider("summarize", {
    "name": "my_summarizer",
    "entry": "providers.my_provider:run",
    "caps": ["summarize"]
})

# 3. Use it (router automatically selects via bandit)
result = run_capability("summarize", record, {})
```

---

## 🎯 **KEY FEATURES**

### **1. Shadow Execution**
```python
# policies.yaml
routing:
  summarize:
    shadow_percent: 0.2  # 20% of requests run shadow

# Router automatically:
# - Runs primary provider
# - Runs shadow provider (no-apply)
# - Compares scores
# - Logs which performed better
# - Can switch to shadow if better
```

### **2. Multi-Armed Bandit**
```python
# Automatic provider selection
# - Exploration: Try different providers
# - Exploitation: Use proven winners
# - Thompson sampling for balance
# - Promotion only after min samples
```

### **3. Policy Constraints**
```yaml
constraints:
  offline_only: true          # Never call external APIs
  pii_never_leave_local: true # Privacy-first
  max_latency_ms: 1500        # Performance gate
```

### **4. Composite Scoring**
```yaml
scorecard_weights:
  correctness: 0.45  # Did it work?
  structure:   0.15  # Proper format?
  safety:      0.15  # No PII leakage?
  latency:     0.15  # Fast enough?
  acceptance:  0.10  # User approved?
```

---

## 📊 **HOW IT WORKS**

```
User Request
    ↓
Router.run_capability("summarize", record, params)
    ↓
1. Load Policy (constraints, weights, shadow %)
2. Retrieve Context (vector search)
3. Select Provider (bandit + policy)
4. Optional: Select Shadow (different provider)
    ↓
5. Execute Primary (trace start)
6. Execute Shadow (if enabled, no-apply)
    ↓
7. Score Both (composite scorecard)
8. Reward Primary (bandit learning)
9. Compare (log if shadow better)
    ↓
10. Return Primary Output (or shadow if preferred)
    ↓
Complete Trace (with full telemetry)
```

---

## 🧪 **TESTING**

```bash
# Run smoke tests
make test

# Run preflight
make preflight

# Both should pass
```

---

## 🔄 **INTEGRATION WITH AGENTS**

### **Connect to Agent System:**
```python
# In orchestrator/providers/agent_provider.py
from agents import Orchestrator as AgentOrch

agent_orch = AgentOrch()

def run(capability_input):
    goal = capability_input["record"].get("subject", "")

    # Use agent system for execution
    agent_result = agent_orch.execute_goal(goal)

    # Map to capability contract
    return {
        "tldr": str(agent_result.output)[:200],
        "facts": agent_result.learnings,
        "next_action": "review",
        "actions": [{"type": "agent_execution", "value": agent_result.plan_id}],
        "metrics": {
            "latency_ms": agent_result.total_time_ms,
            "iterations": agent_result.iterations,
            "score": agent_result.overall_score
        },
        "safety": {"pii": False},
        "raw": str(agent_result.output)
    }

# Register
from registry import register_provider
register_provider("plan", {
    "name": "agent_planner",
    "entry": "providers.agent_provider:run",
    "caps": ["plan", "reason"]
})
```

**Result:** Agent system becomes a capability provider! 🎯

---

## 🎯 **PHILOSOPHY**

**Old Way:**
- "Use GPT-4 for this"
- "Use Claude for that"
- Hard-coded model names
- No learning, no comparison

**New Way:**
- "I need summarization capability"
- Router picks best provider (via bandit)
- Shadow execution validates alternatives
- System learns which provider excels at what
- Completely swappable

**Agent-Agnostic = Future-Proof** ✅

---

## ✨ **NEXT STEPS**

1. **Test**: `make all`
2. **Integrate Agents**: Create `providers/agent_provider.py`
3. **Add Real Providers**: Replace stubs with actual implementations
4. **Tune Policy**: Adjust `policies.yaml` for your needs
5. **Monitor**: Check bandit stats and shadow comparisons

---

**ORCHESTRATOR READY** ✅
**Integration Point**: Capability providers
**Philosophy**: Route by capability, not by name! 🎯
