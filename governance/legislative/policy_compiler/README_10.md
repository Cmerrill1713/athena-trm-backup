# NeuroForge Agent System

**Self-improving collaborative AI architecture**

---

## 🧠 **ARCHITECTURE**

### **4 Core Agents:**

**1. Planner Agent** (`planner_agent.py`)
- **Role**: Strategic task decomposition
- **Input**: User goal
- **Output**: Structured plan with steps and success criteria
- **Learning**: Uses historical patterns from Memory

**2. Executor Agent** (`executor_agent.py`)
- **Role**: Task execution
- **Input**: Plan from Planner
- **Output**: Execution results with metadata
- **Tools**: Code gen, file ops, API calls, reasoning

**3. Critic Agent** (`critic_agent.py`)
- **Role**: Quality assessment
- **Input**: Plan + Execution results
- **Output**: Scored feedback with suggestions
- **Learning**: Identifies patterns and improvements

**4. Memory Layer** (`memory_layer.py`)
- **Role**: Persistent learning storage
- **Input**: Plans, executions, reviews
- **Output**: Historical patterns and learnings
- **Storage**: SQLite database

### **Orchestrator** (`orchestrator.py`)
- **Role**: Agent coordination
- **Workflow**: Planner → Executor → Critic → Memory (iterate)
- **Output**: Final result with accumulated learnings

---

## 🔁 **THE LEARNING LOOP**

```
User Goal
    ↓
🧠 PLANNER (with historical context)
    ↓
Structured Plan
    ↓
🚀 EXECUTOR (with tools)
    ↓
Execution Results
    ↓
🕵️ CRITIC (quality review)
    ↓
Feedback + Learnings
    ↓
🗃️ MEMORY (store patterns)
    ↓
[Loop back to Planner with learnings]
    ↓
Improved Plan → Better Results
```

**Each iteration makes the system smarter!**

---

## 🚀 **QUICK START**

### **Install Dependencies:**
```bash
pip install requests  # For API calls (optional)
```

### **Basic Usage:**
```python
from agents import Orchestrator

# Create orchestrator
orchestrator = Orchestrator()

# Execute a goal
result = orchestrator.execute_goal("Write a validation script")

# Check results
print(f"Success: {result.success}")
print(f"Score: {result.overall_score:.2f}")
print(f"Learnings: {result.learnings}")
```

### **With Custom LLM:**
```python
from agents import Orchestrator

# Your LLM client (Ollama, LM Studio, etc.)
class MyLLM:
    def generate(self, prompt, temperature=0.7):
        # Your LLM call here
        return response

llm = MyLLM()
orchestrator = Orchestrator(llm_client=llm)
result = orchestrator.execute_goal("Your goal here")
```

---

## 🧪 **EXAMPLES**

### **Example 1: Simple Task**
```python
from agents import Orchestrator

orch = Orchestrator()
result = orch.execute_goal("Create a hello world script")

if result.success:
    print("✅ Task completed!")
    print(f"Output: {result.output}")
```

### **Example 2: With Learning**
```python
orchestrator = Orchestrator()

# First time - learns the pattern
result1 = orchestrator.execute_goal("Write a test script")

# Second time - uses learning from first attempt
result2 = orchestrator.execute_goal("Write a test script")

# Should be better/faster the second time!
print(f"First attempt: {result1.overall_score:.2f}")
print(f"Second attempt: {result2.overall_score:.2f}")
```

### **Example 3: Custom Tools**
```python
from agents import ExecutorAgent

def my_custom_tool(step):
    # Your tool logic
    return {"result": "success"}

executor = ExecutorAgent()
executor.register_tool("my_tool", my_custom_tool)

# Now executor can use your tool
```

---

## 📊 **AGENT RESPONSIBILITIES**

| **Agent** | **Teaches** | **Learns From** | **Improves** |
|-----------|-------------|-----------------|--------------|
| Planner | Executor (what to do) | Memory (patterns) | Task decomposition |
| Executor | Critic (what happened) | Planner (instructions) | Tool selection |
| Critic | Memory (what worked) | Execution (results) | Quality assessment |
| Memory | Planner (history) | Critic (feedback) | Pattern recognition |

**Everyone teaches, everyone learns!** 🔁

---

## 🎯 **KEY FEATURES**

### **Self-Improvement:**
- Plans get better over time
- Execution becomes more efficient
- Feedback becomes more precise
- Patterns are recognized faster

### **Structured Communication:**
- JSON-based protocol
- Clear data structures
- Type-safe interfaces
- Traceable workflows

### **Persistent Learning:**
- SQLite storage
- Historical pattern retrieval
- Success/failure analysis
- Confidence scoring

### **Flexible Integration:**
- Works with any LLM
- Pluggable tools
- Configurable memory
- Extensible architecture

---

## 🛠️ **CONFIGURATION**

### **Environment Variables:**
```bash
# Optional: Override defaults
export NEUROFORGE_MEMORY_PATH="custom/path/to/memory.db"
export NEUROFORGE_MAX_ITERATIONS=5
export NEUROFORGE_LLM_TEMPERATURE=0.3
```

### **Database Location:**
- Default: `memory/neuroforge.db`
- Created automatically on first run
- Contains: plans, executions, reviews, learnings, patterns

---

## 📈 **SCALING UP**

### **Current: Single Machine**
- All agents run locally
- SQLite for memory
- Fast, private, no API costs

### **Future: Distributed**
- Agents can run on different machines
- Shared memory via Postgres/Supabase
- Parallel execution
- Team collaboration

---

## 🧪 **TESTING**

### **Run Agent Tests:**
```bash
# Test individual agents
python agents/planner_agent.py
python agents/executor_agent.py
python agents/critic_agent.py
python agents/memory_layer.py

# Test orchestration
python agents/orchestrator.py
```

### **Run Full Loop:**
```python
from agents import Orchestrator

orch = Orchestrator()

# Execute and observe the loop
result = orch.execute_goal("Your test goal")

# Check memory stats
stats = orch.get_memory_stats()
print(stats)
```

---

## 🎓 **LEARNING EXAMPLES**

### **Pattern Recognition:**
```
Attempt 1: "Write a script" → 3 steps → Score: 0.6
Memory stores: "3-step pattern works for scripts"

Attempt 2: "Write a different script" → Uses 3-step pattern → Score: 0.85
Memory learns: "3-step pattern is reliable"

Attempt 3: "Write a complex script" → Adapts pattern → Score: 0.92
```

### **Failure Recovery:**
```
Attempt 1: Step 2 fails → Critic identifies issue
Memory stores: "Step 2 needs error handling"

Attempt 2: Planner adds error handling → Success
Memory learns: "Error handling required for this pattern"
```

---

## 🚀 **NEXT STEPS**

### **Immediate:**
1. Test agents individually
2. Run orchestrator demo
3. Observe learning loop
4. Check memory stats

### **Enhancement:**
1. Add vector embeddings for better similarity
2. Integrate with Ollama/LM Studio
3. Add more sophisticated tools
4. Implement meta-agent for strategy adjustment

---

## 📚 **FILES**

```
agents/
├── __init__.py               # Package exports
├── README.md                 # This file
├── planner_agent.py          # Strategic planning
├── executor_agent.py         # Task execution
├── critic_agent.py           # Quality review
├── memory_layer.py           # Persistent storage
├── orchestrator.py           # Agent coordination
└── tests/
    └── test_agents.py        # Unit tests (TODO)
```

---

## ✨ **THE VISION**

**Old Way:**
- Single LLM → hit or miss
- No learning between runs
- Manual improvement
- Static capabilities

**New Way:**
- Specialized agents → predictable results
- Continuous learning from every execution
- Automatic improvement
- Growing capabilities

**This is your local, self-improving AI ecosystem!** 🧠

---

**AGENT SYSTEM v0.1.0** ✅
**Status**: Foundation complete
**Next**: Test the loop! 🔥
