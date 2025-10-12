# 🎓 Fine-Tuning Guide - MLX + GGUF Pipeline

**The right way to fine-tune and deploy on Apple Silicon**

---

## 🎯 The Correct Pipeline

### **✅ DO THIS**:
```
PyTorch/HF Model
      ↓
  LoRA Fine-Tune
      ↓
   ┌──────┴──────┐
   ↓             ↓
MLX Export    GGUF Export
   ↓             ↓
Apple Silicon  Ollama
(Metal GPU)    (CPU/Any)
```

### **❌ DON'T DO THIS**:
```
GGUF → MLX  (Won't work - one-way street)
MLX → GGUF  (Lossy, defeats purpose)
Random download → Fine-tune  (Start from HF weights!)
```

---

## 🚀 Quick Start

### **One-Command Pipeline**
```bash
bash scripts/model_pipeline.sh \
  --base hf://meta-llama/Llama-3-8B-Instruct \
  --data data/vision_tasks.jsonl \
  --name llama3-8b-vision-tuned
```

**What it does**:
1. Trains LoRA adapter
2. Exports to MLX (Apple Silicon optimized)
3. Exports to GGUF (Ollama compatible)
4. Creates Ollama model
5. Updates routing registry
6. Runs A/B smoke test

**Time**: 10-30 minutes (depends on dataset size)

---

## 📋 Step-by-Step (Manual Control)

### **1. Fine-Tune LoRA**

```bash
python3 scripts/ft/train_lora.py \
  --base hf://meta-llama/Llama-3-8B-Instruct \
  --data data/my_task.jsonl \
  --epochs 2 \
  --lr 2e-4 \
  --lora_r 16 \
  --lora_alpha 32 \
  --save_dir artifacts/lora-run
```

**Output**: `artifacts/lora-run/` with adapter weights

---

### **2. Export to MLX** (Apple Silicon)

```bash
python3 scripts/ft/export_to_mlx.py \
  --base hf://meta-llama/Llama-3-8B-Instruct \
  --lora artifacts/lora-run \
  --out models/mlx/llama3-8b-tuned-mlx
```

**Output**: MLX-optimized model using Metal GPU

**Performance**: ~2-5× faster than PyTorch on M1/M2/M3

---

### **3. Export to GGUF** (Ollama)

```bash
python3 scripts/ft/export_to_gguf.py \
  --base hf://meta-llama/Llama-3-8B-Instruct \
  --lora artifacts/lora-run \
  --out models/gguf/llama3-8b-tuned.Q4_K_M.gguf
```

**Output**: Quantized GGUF file

---

### **4. Create Ollama Model**

```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM models/gguf/llama3-8b-tuned.Q4_K_M.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
TEMPLATE """{{ .System }}

{{ .Prompt }}"""
EOF

# Create model
ollama create llama3-8b-tuned -f Modelfile
```

**Test**:
```bash
ollama run llama3-8b-tuned "Hello, test"
```

---

### **5. Register in Router**

Add to `config/routing_policy.json`:

```json
{
  "providers": {
    "llama3_mlx": {
      "endpoint": "http://localhost:8014/api/chat",
      "model": "mlx:llama3-8b-tuned",
      "tier": "accurate"
    },
    "llama3_ollama": {
      "endpoint": "http://localhost:11434/api/chat",
      "model": "llama3-8b-tuned",
      "tier": "fast"
    }
  }
}
```

**Router will pick**:
- MLX for accuracy-critical tasks
- Ollama for speed-critical tasks

---

## 🧠 Model Family Support

### **Well-Supported** (MLX + GGUF)
- ✅ LLaMA/LLaMA-2/LLaMA-3
- ✅ Mistral/Mixtral
- ✅ Qwen/Qwen2
- ✅ Phi-2/Phi-3
- ✅ Gemma

### **Partial Support**
- ⚠️ Newer architectures (check `mlx-lm` compatibility)
- ⚠️ Multi-modal models (vision may need special handling)

### **Not Supported**
- ❌ Proprietary architectures (OpenAI, Anthropic)
- ❌ Some newer research models

**Check before training**: https://github.com/ml-explore/mlx-examples

---

## ⚙️ Format Characteristics

| Format | Best For | Speed | Memory | Quality |
|--------|----------|-------|--------|---------|
| **MLX** | Apple Silicon tasks | Fast | Medium | High |
| **GGUF Q4** | Fast inference | Very Fast | Low | Good |
| **GGUF Q8** | Balanced | Medium | Medium | Very Good |
| **PyTorch** | Training only | Slow | High | Best |

---

## 🎯 Router Integration

### **Model-Agnostic Routing** (Your Current Setup)

Frontend sends **task**, not model:
```swift
let meta = [
    "task": "chat.reasoning",  // Router picks best model
    "latency_budget_ms": 5000,
    "requires_tools": false
]
```

Backend routes via `config/routing_policy.json`:
```json
{
  "tasks": {
    "chat.reasoning": {
      "provider": "trm_router",  // TRM picks MLX or Ollama
      "depth": "auto"
    }
  }
}
```

**Result**: TRM/LLM picks MLX for complex reasoning, Ollama for simple queries!

---

## 🧪 Testing Pipeline

### **After Training**

```bash
# 1. Test MLX export
python3 -c "import mlx.core as mx; print('MLX:', mx.metal.is_available())"

# 2. Test GGUF
ollama list | grep your-model

# 3. Test routing
curl -X POST http://localhost:8014/api/chat \
  -d '{"input": "test", "meta": {"task": "chat.coding"}}'

# 4. Deploy as canary
make canary-10 CANARY_MODEL=your-model
source /tmp/canary.env

# 5. Monitor
make canary-eval
```

---

## 📊 What Gets Created

After running `model_pipeline.sh`:

```
artifacts/model-pipeline/llama3-8b-tuned-TIMESTAMP/
├── lora/                      # LoRA adapter weights
│   ├── adapter_config.json
│   └── adapter_model.bin
├── mlx/                       # MLX export (Apple Silicon)
│   ├── config.json
│   ├── weights.npz
│   └── tokenizer.model
├── gguf/                      # GGUF export (Ollama)
│   └── llama3-8b-tuned.Q4_K_M.gguf
├── registry_entry.json        # Router registration
├── train.log                  # Training logs
├── export_mlx.log            # MLX export logs
└── export_gguf.log           # GGUF export logs
```

---

## 🚨 Common Gotchas

### **1. "Model not compatible with MLX"**

**Cause**: Model architecture not in `mlx-lm`
**Fix**: Use GGUF/Ollama only, or wait for MLX support

---

### **2. "GGUF export failed"**

**Cause**: Model not compatible with llama.cpp
**Fix**: Use MLX only, or check llama.cpp compatibility

---

### **3. "Can't convert GGUF to MLX"**

**Cause**: One-way conversion (wrong direction)
**Fix**: Always start from original HF weights

---

### **4. "Quantized model is worse"**

**Cause**: Over-quantization (Q2/Q3 too aggressive)
**Fix**: Use Q4_K_M or Q8 for better quality

---

### **5. "XCUITests fail"**

**Cause**: macOS Automation permissions
**Fix**:
- System Settings → Privacy → Accessibility → Allow Xcode/Terminal
- System Settings → Privacy → Automation → Allow Xcode → System Events
- Run once in Xcode (⌘U)

---

## 🎯 Supported Workflows

### **Workflow 1: MLX Only** (Fastest on M-series)
```bash
# Train
python3 scripts/ft/train_lora.py --base ... --data ... --save_dir lora/

# Export MLX
python3 scripts/ft/export_to_mlx.py --lora lora/ --out mlx/

# Use
# Router automatically picks MLX for Apple Silicon
```

---

### **Workflow 2: Ollama Only** (Most Compatible)
```bash
# Train
python3 scripts/ft/train_lora.py ...

# Export GGUF
python3 scripts/ft/export_to_gguf.py ...

# Create Ollama model
ollama create my-model -f Modelfile

# Use
curl http://localhost:11434/api/chat -d '{"model": "my-model", ...}'
```

---

### **Workflow 3: Both** (Recommended - Router Picks Best)
```bash
# Use model_pipeline.sh (does both)
bash scripts/model_pipeline.sh --base ... --data ... --name ...

# Router picks:
# - MLX for accuracy/complex tasks
# - Ollama for speed/simple tasks
```

---

## 📚 Resources

- **MLX Examples**: https://github.com/ml-explore/mlx-examples
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **Ollama**: https://github.com/ollama/ollama
- **Your Router**: `config/routing_policy.json`

---

## ✅ Quick Reference

```bash
# Complete pipeline
bash scripts/model_pipeline.sh \
  --base hf://MODEL \
  --data data.jsonl \
  --name output-name

# Test routing
curl -X POST http://localhost:8014/api/chat \
  -d '{"input": "test", "meta": {"task": "chat.coding"}}'

# Deploy as canary
make canary-10 CANARY_MODEL=output-name
```

---

**Fine-tuning is now part of your autonomous evolution loop!** 🎓✨
