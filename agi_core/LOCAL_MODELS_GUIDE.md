# Local Models Setup Guide for STOP Optimizer

## Overview

STOP optimizer now supports local LLM models, eliminating the need for cloud API keys and providing:
- ✅ **Privacy** - Code never leaves your machine
- ✅ **Cost** - No API fees
- ✅ **Speed** - Local inference (depending on hardware)
- ✅ **Offline** - Works without internet

## Supported Local Model Servers

### 1. Ollama (Recommended)
- **Best for**: Easy setup, wide model support
- **Models**: CodeLlama, Mistral, Llama 2, DeepSeek Coder
- **Website**: https://ollama.ai

### 2. LM Studio
- **Best for**: GUI-based management
- **Models**: Any GGUF format models
- **Website**: https://lmstudio.ai

### 3. vLLM
- **Best for**: Production deployments, high performance
- **Models**: Most HuggingFace models
- **Website**: https://github.com/vllm-project/vllm

### 4. text-generation-webui (oobabooga)
- **Best for**: Advanced users, extensive customization
- **Models**: Wide variety
- **Website**: https://github.com/oobabooga/text-generation-webui

## Quick Start: Ollama Setup

### Step 1: Install Ollama

```bash
# macOS
curl https://ollama.ai/install.sh | sh

# Linux
curl https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### Step 2: Pull a Code Model

```bash
# CodeLlama 7B (Recommended for coding)
ollama pull codellama:7b

# DeepSeek Coder 6.7B (Great for optimization)
ollama pull deepseek-coder:6.7b

# Mistral 7B (General purpose, good at following instructions)
ollama pull mistral:7b

# CodeLlama 13B (Better quality, slower)
ollama pull codellama:13b
```

### Step 3: Start Ollama Server

```bash
# Start server (usually starts automatically on macOS/Linux)
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Step 4: Use with STOP Optimizer

```python
from agi_core import STOPOptimizer
from agi_core.stop_optimizer import LLMInterface

# Create LLM interface for local model
llm = LLMInterface(
    model="codellama:7b",           # Model name
    use_local=True,                  # Use local model
    api_base="http://localhost:11434"  # Ollama default
)

# Create optimizer with local LLM
optimizer = STOPOptimizer(llm_interface=llm)

# Run optimization (will use local model!)
result = optimizer.optimize(
    target_code=your_code,
    utility_function=utility_func,
    utility_description="Optimize for performance",
    iterations=10
)
```

## Recommended Models for STOP

### For Code Optimization

| Model | Size | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **codellama:7b** | 4GB | Good | Fast | General optimization |
| **deepseek-coder:6.7b** | 4GB | Excellent | Fast | Algorithm optimization |
| **codellama:13b** | 8GB | Excellent | Medium | Complex optimizations |
| **codellama:34b** | 20GB | Best | Slow | Production-grade |

### For General Tasks

| Model | Size | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **mistral:7b** | 4GB | Good | Fast | Instructions, analysis |
| **llama2:13b** | 8GB | Good | Medium | Reasoning tasks |
| **mixtral:8x7b** | 26GB | Excellent | Slow | Complex reasoning |

## Complete Examples

### Example 1: Basic Local Optimization

```python
from agi_core import optimize_function
from agi_core.stop_optimizer import LLMInterface

# Setup local LLM
llm = LLMInterface(
    model="codellama:7b",
    use_local=True
)

# Your code to optimize
code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

# Utility function
def perf_utility(metrics):
    return metrics.get("success_rate", 0) * 0.8 + \
           (1.0 - metrics.get("execution_time_ms", 100) / 100.0) * 0.2

# Optimize with local model
result = optimize_function(
    code=code,
    utility_function=perf_utility,
    description="Optimize fibonacci calculation for performance",
    iterations=5
)

print(f"Improvement: {result.improvement_percent:.1f}%")
print(f"\nOptimized code:\n{result.best_candidate.code}")
```

### Example 2: Context Reduction with DeepSeek Coder

```python
from agi_core import STOPOptimizer
from agi_core.stop_optimizer import LLMInterface

# Use DeepSeek Coder (excellent for algorithms)
llm = LLMInterface(
    model="deepseek-coder:6.7b",
    use_local=True
)

optimizer = STOPOptimizer(llm_interface=llm)

context_code = """
def reduce_context(tokens, max_tokens):
    # Simple reduction strategy
    reduction_ratio = max_tokens / tokens
    return int(tokens * reduction_ratio)
"""

def context_utility(metrics):
    # Favor high efficiency
    return metrics.get("context_efficiency", 0.0)

result = optimizer.optimize(
    target_code=context_code,
    utility_function=context_utility,
    utility_description="Maximize token reduction efficiency while preserving information",
    iterations=10,
    beam_width=3
)

print(f"Optimized with {llm.model}")
print(f"Improvement: {result.improvement_percent:.1f}%")
```

### Example 3: Multi-Model Comparison

```python
from agi_core import OptimizationStrategy
from agi_core.stop_optimizer import LLMInterface, STOPOptimizer

# Test different local models
models = [
    "codellama:7b",
    "deepseek-coder:6.7b",
    "mistral:7b"
]

code = """
def process_items(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
    return results
"""

def utility_func(metrics):
    return metrics.get("success_rate", 0.0)

best_model = None
best_improvement = 0

for model_name in models:
    print(f"\nTesting {model_name}...")
    
    llm = LLMInterface(model=model_name, use_local=True)
    optimizer = STOPOptimizer(llm_interface=llm)
    
    result = optimizer.optimize(
        target_code=code,
        utility_function=utility_func,
        utility_description="Optimize for clarity and performance",
        iterations=5
    )
    
    print(f"  Improvement: {result.improvement_percent:.1f}%")
    print(f"  Confidence: {result.confidence_score:.3f}")
    
    if result.improvement_percent > best_improvement:
        best_model = model_name
        best_improvement = result.improvement_percent

print(f"\n🏆 Best model: {best_model} ({best_improvement:.1f}% improvement)")
```

## Environment Variables

```bash
# Set Ollama endpoint (if not default)
export OLLAMA_API_BASE="http://localhost:11434"

# For production deployment
export OLLAMA_API_BASE="http://your-server:11434"
```

## LM Studio Setup

### Step 1: Install LM Studio
Download from https://lmstudio.ai

### Step 2: Download a Model
- Open LM Studio
- Go to "Discover" tab
- Download CodeLlama or DeepSeek Coder

### Step 3: Start Server
- Go to "Local Server" tab
- Click "Start Server"
- Note the endpoint (usually http://localhost:1234)

### Step 4: Use with STOP

```python
from agi_core.stop_optimizer import LLMInterface

llm = LLMInterface(
    model="codellama-7b",  # Model you downloaded
    use_local=True,
    api_base="http://localhost:1234"  # LM Studio default
)
```

## Advanced: Custom Local Endpoint

If you're running a custom local model server:

```python
from agi_core.stop_optimizer import LLMInterface

# Custom endpoint
llm = LLMInterface(
    model="your-model-name",
    use_local=True,
    api_base="http://your-custom-endpoint:8080"
)

# The interface will send requests in Ollama-compatible format
# Make sure your server supports the format:
# POST /api/generate
# Body: {"model": "...", "prompt": "...", "stream": false}
```

## Performance Tips

### 1. Choose the Right Model Size

**System RAM Requirements:**
- 7B models: 8GB RAM minimum
- 13B models: 16GB RAM minimum
- 34B models: 32GB RAM minimum

```python
# For fast iteration
llm = LLMInterface(model="codellama:7b", use_local=True)

# For best quality
llm = LLMInterface(model="codellama:34b", use_local=True)
```

### 2. Adjust Generation Parameters

```python
# In stop_optimizer.py, modify _call_local_llm:
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.5,    # Lower = more focused (0.3-0.8)
        "top_p": 0.9,          # Nucleus sampling
        "num_predict": 2048,   # Max tokens to generate
        "repeat_penalty": 1.1  # Avoid repetition
    }
}
```

### 3. Use GPU Acceleration

```bash
# Ollama automatically uses GPU if available
# Check GPU usage
nvidia-smi  # For NVIDIA GPUs

# Force CPU mode (if needed)
OLLAMA_NUM_GPU=0 ollama serve
```

### 4. Batch Optimizations

```python
# Process multiple functions in one session
optimizer = STOPOptimizer(llm_interface=llm)

functions_to_optimize = [func1, func2, func3]

for func in functions_to_optimize:
    result = optimizer.optimize(
        target_code=func,
        utility_function=utility_func,
        iterations=5  # Fewer iterations per function
    )
    # Process result
```

## Troubleshooting

### Issue: "Connection refused"

```bash
# Make sure Ollama is running
ollama serve

# Or check if it's running
curl http://localhost:11434/api/tags
```

### Issue: Model not found

```bash
# List available models
ollama list

# Pull the model you need
ollama pull codellama:7b
```

### Issue: Slow generation

```python
# Use smaller model
llm = LLMInterface(model="codellama:7b", use_local=True)

# Reduce beam width
result = optimizer.optimize(..., beam_width=2)

# Reduce iterations
result = optimizer.optimize(..., iterations=5)
```

### Issue: Out of memory

```bash
# Use quantized models (smaller, faster)
ollama pull codellama:7b-q4  # 4-bit quantized

# Or use smaller model
ollama pull codellama:7b  # Instead of 13b
```

## Comparing Local vs Cloud

| Aspect | Local Models | Cloud APIs |
|--------|--------------|------------|
| **Privacy** | ✅ Complete | ❌ Code sent to cloud |
| **Cost** | ✅ Free (after hardware) | ❌ Per-token pricing |
| **Speed** | Depends on hardware | Usually fast |
| **Quality** | Good (7-34B models) | Excellent (GPT-4) |
| **Setup** | Moderate | Easy |
| **Offline** | ✅ Yes | ❌ No |

## Best Practices

### 1. Model Selection

```python
# For development/testing
llm = LLMInterface(model="codellama:7b", use_local=True)

# For production optimization
llm = LLMInterface(model="deepseek-coder:6.7b", use_local=True)

# For best quality (if you have the hardware)
llm = LLMInterface(model="codellama:34b", use_local=True)
```

### 2. Gradual Optimization

```python
# Start with few iterations
result = optimizer.optimize(..., iterations=5)

# If promising, increase
if result.improvement_percent > 5:
    result = optimizer.optimize(..., iterations=20)
```

### 3. Validate Results

```python
# Always validate optimized code
if result.confidence_score > 0.7:
    # Run tests
    test_result = run_tests(result.best_candidate.code)
    
    if test_result.passed:
        deploy_optimization(result.best_candidate.code)
```

### 4. Cache Successful Patterns

```python
# Keep track of successful optimizations
if result.improvement_percent > 10:
    save_optimization_pattern(
        original=code,
        optimized=result.best_candidate.code,
        strategy=result.strategy,
        model=llm.model
    )
```

## Production Deployment

### Docker Setup for Ollama

```dockerfile
FROM ollama/ollama

# Pull models at build time
RUN ollama pull codellama:7b
RUN ollama pull deepseek-coder:6.7b

EXPOSE 11434
CMD ["ollama", "serve"]
```

### Python Requirements

```txt
# Add to requirements.txt
requests>=2.31.0  # For local LLM calls
```

### Environment Configuration

```python
# config.py
import os

LLM_CONFIG = {
    "use_local": True,
    "model": os.getenv("LLM_MODEL", "codellama:7b"),
    "api_base": os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
}

# In your code
from agi_core.stop_optimizer import LLMInterface

llm = LLMInterface(**LLM_CONFIG)
```

## Next Steps

1. **Install Ollama**: `curl https://ollama.ai/install.sh | sh`
2. **Pull a model**: `ollama pull codellama:7b`
3. **Run example**: `python3 agi_core/examples_stop.py`
4. **Monitor performance**: Check `state/stop_optimizer/` for results
5. **Scale up**: Try larger models or more iterations

## Resources

- **Ollama**: https://ollama.ai
- **Model Library**: https://ollama.ai/library
- **LM Studio**: https://lmstudio.ai
- **STOP Paper**: https://arxiv.org/abs/2310.02304

---

**Your STOP optimizer is now ready for local, private code optimization!** 🚀

