# 🧠 TRM Training Integration Plan

## Overview

**Goal:** Integrate TRM (Tiny Recursive Models) training capabilities with the LLM system for continuous self-improvement.

## Current TRM Capabilities

Based on `knowledge_base/trm_tiny_recursive_models.md`:

- **Model Size:** 7M parameters (tiny!)
- **Performance:** 45% on ARC-AGI-1, 8% on ARC-AGI-2
- **Architecture:** Recursive reasoning (H_cycles=3, L_cycles=4-6)
- **Training Time:** 24-72 hours on GPUs

## Integration Strategy

### Phase 1: TRM Model Training Infrastructure

**Location:** New service `services/trm-trainer/`

**Capabilities:**
1. Dataset preparation (ARC-AGI, Sudoku, Maze)
2. Model training (pretrain.py)
3. Model evaluation
4. Model serving (inference)

### Phase 2: Integration with Router

**Connect TRM as a reasoning provider:**
```
Router → TRM (for reasoning tasks)
      → LLM (for language tasks)
      → Hybrid (TRM + LLM for complex reasoning)
```

### Phase 3: Continuous Learning

**Feedback loop:**
```
User query → TRM/LLM response → Feedback → Store in training data
          → Periodic retraining → Improved model → Deploy
```

---

## Implementation Plan

### Service Architecture

```python
# services/trm-trainer/app.py

@app.post("/train")
async def train_trm(dataset: str, epochs: int, config: dict):
    """Train TRM model on dataset"""
    # Run pretrain.py with config
    # Monitor progress
    # Return model ID

@app.post("/evaluate")
async def evaluate_trm(model_id: str, dataset: str):
    """Evaluate TRM model"""
    # Run evaluation
    # Return metrics

@app.post("/deploy")
async def deploy_trm(model_id: str):
    """Deploy TRM model to router"""
    # Copy model to serving location
    # Update router configuration
    # Return deployment status

@app.post("/inference")
async def trm_inference(query: dict):
    """Run inference with TRM"""
    # Load model
    # Run recursive reasoning
    # Return result
```

### Router Integration

```python
# Add to services/router/providers/

class TRMProvider:
    def __init__(self, model_path: str):
        self.model = load_trm_model(model_path)
    
    async def reason(self, query: str, max_cycles: int = 10):
        """Recursive reasoning with TRM"""
        # Initialize with query embedding
        # Run recursive cycles
        # Return refined answer
    
    def should_use_trm(self, query: str) -> bool:
        """Decide if query needs TRM reasoning"""
        # Complex logical tasks → TRM
        # Simple text → LLM
        return detect_reasoning_task(query)
```

---

## TRM + LLM Hybrid Architecture

```
User Query
    ↓
Router Analysis
    ↓
┌─────────────┬──────────────┐
│  TRM Path   │   LLM Path   │
│             │              │
│ Logical     │  Language    │
│ Reasoning   │  Generation  │
│             │              │
│ 7M params   │ 7B params    │
│ 6ms         │ 2.5s         │
└──────┬──────┴──────┬───────┘
       │             │
       └──── Combine ────┘
              ↓
         Final Response
```

### Example Routing:

| Query Type | Route | Reasoning |
|-----------|-------|-----------|
| "What is 2+2?" | TRM | Simple logic |
| "Solve sudoku" | TRM | Reasoning task |
| "Explain quantum physics" | LLM | Knowledge retrieval |
| "Solve maze and explain solution" | TRM+LLM | Hybrid |

---

## Continuous Improvement Loop

```
1. Collect Feedback
   ├─ User ratings (thumbs up/down)
   ├─ Response quality scores
   └─ Error corrections

2. Store Training Data
   ├─ Successful TRM reasoning paths
   ├─ Failed attempts (for learning)
   └─ Ground truth labels

3. Periodic Retraining
   ├─ Weekly: Fine-tune on new data
   ├─ Monthly: Full retrain with accumulated data
   └─ A/B test: Old model vs new model

4. Auto-Deploy
   ├─ Evaluate new model on validation set
   ├─ If improvement > 5% → Canary deploy
   └─ Monitor → Auto-rollback if issues
```

---

## Docker Service Definition

```yaml
# Add to docker-compose.yml

services:
  trm-trainer:
    build:
      context: ./services/trm-trainer
      dockerfile: Dockerfile
    container_name: athena-trm-trainer
    restart: unless-stopped
    ports:
      - "127.0.0.1:8200:8200"
    environment:
      - PYTHONUNBUFFERED=1
      - CUDA_VISIBLE_DEVICES=0  # GPU access
    volumes:
      - ./services/trm-trainer:/app:ro
      - ./data/trm-models:/models:rw  # Model storage
      - ./data/trm-datasets:/datasets:rw  # Training data
    networks:
      - athena-network
    # Optional: GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  trm-inference:
    build:
      context: ./services/trm-inference
      dockerfile: Dockerfile
    container_name: athena-trm-inference
    restart: unless-stopped
    ports:
      - "127.0.0.1:8201:8201"
    environment:
      - PYTHONUNBUFFERED=1
      - MODEL_PATH=/models/current
    volumes:
      - ./data/trm-models:/models:ro
    networks:
      - athena-network
```

---

## Integration Points

### 1. Router Enhancement
```python
# services/router/app.py

providers = {
    "mlx": MLXProvider(),
    "ollama": OllamaProvider(),
    "uai": UAIProvider(),
    "trm": TRMProvider(),  # NEW: TRM reasoning
}

routing_logic = {
    "reasoning_task": "trm",
    "language_task": "uai",
    "hybrid_task": ["trm", "uai"],  # Use both
}
```

### 2. Knowledge Base Addition
```bash
# Add TRM training docs to knowledge base
echo "# TRM Training Guide
## How to Train TRM Models
- Dataset preparation
- Training configuration
- Evaluation metrics
- Deployment process
" > knowledge_base/trm_training_guide.md

# Re-embed
python3 embed_knowledge_base.py
```

### 3. Feedback Collection
```python
# Add to AI-Projects/universal-ai-tools/api/

@router.post("/feedback")
async def collect_feedback(
    query_id: str,
    rating: int,
    correction: str = None
):
    """Collect user feedback for model improvement"""
    # Store in database
    # Queue for next training cycle
    # Return acknowledgment
```

---

## Training Data Pipeline

```
User Interactions
    ↓
Feedback Collection API
    ↓
PostgreSQL Storage
    ↓
Data Processing (weekly)
    ↓
TRM Training Service
    ↓
Model Evaluation
    ↓
A/B Testing (Canary)
    ↓
Auto-Deploy (if better)
```

---

## Metrics to Track

### Model Performance:
- `trm_accuracy_by_task_type` - Success rate per category
- `trm_inference_latency` - Response time
- `trm_cycles_used` - Reasoning depth

### Training Progress:
- `trm_training_loss` - Model convergence
- `trm_eval_score` - Validation performance
- `trm_deployment_frequency` - How often models improve

### User Satisfaction:
- `user_feedback_rating` - Average thumbs up/down
- `correction_frequency` - How often users correct responses
- `trm_vs_llm_preference` - Which performs better

---

## Quick Start: Minimal TRM Integration

**Step 1: Add TRM inference endpoint**
```bash
# Create minimal TRM service that uses existing qwen2.5:7b
# but applies recursive reasoning pattern
```

**Step 2: Router integration**
```bash
# Detect reasoning tasks
# Route to TRM endpoint
# Fallback to LLM if needed
```

**Step 3: Feedback loop**
```bash
# Add thumbs up/down to UI
# Store feedback
# Periodic analysis
```

---

## Benefits

### Immediate:
- ✅ Reasoning tasks handled by specialized model
- ✅ Better performance on logic puzzles
- ✅ Lower latency for reasoning (6ms vs 2.5s)

### Long-term:
- ✅ Continuous model improvement
- ✅ Learned task routing (auto-optimization)
- ✅ Specialized models for specialized tasks
- ✅ Self-training system

---

## Next Steps

1. Create `services/trm-trainer/` skeleton
2. Implement inference endpoint first (quick win)
3. Add router integration
4. Implement feedback collection
5. Build training pipeline

