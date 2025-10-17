# MLX Model Setup for Athena Router

## Overview

MLX is Apple's machine learning framework optimized for Apple Silicon (M1/M2/M3). This guide shows how to set up MLX models for use with the Athena Router's local-first routing.

## Prerequisites

- **Apple Silicon Mac** (M1/M2/M3/M4)
- **macOS 13.0+** (Ventura or later)
- **Python 3.9+**
- **16GB+ RAM** recommended (32GB for larger models)

## Quick Start

```bash
# Install MLX
pip install mlx mlx-lm

# Download and run a model
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080
```

## Detailed Setup

### 1. Install MLX and MLX-LM

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install MLX packages
pip install mlx mlx-lm
```

### 2. Download Models

MLX models are hosted on Hugging Face under the `mlx-community` organization.

**Recommended models for Athena Router:**

```bash
# Code generation (7B - fast, good quality)
mlx_lm.convert --hf-path qwen/Qwen2.5-Coder-7B-Instruct \
               --mlx-path ~/.cache/mlx/qwen2.5-coder-7b

# General purpose (3B - very fast)
mlx_lm.convert --hf-path meta-llama/Llama-3.2-3B-Instruct \
               --mlx-path ~/.cache/mlx/llama-3.2-3b

# Reasoning (14B - slower, higher quality)
mlx_lm.convert --hf-path qwen/Qwen2.5-Coder-14B-Instruct \
               --mlx-path ~/.cache/mlx/qwen2.5-coder-14b
```

Or download pre-converted models:

```bash
# Using mlx_lm.server will auto-download
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080
```

### 3. Start MLX Server

**Option A: Using mlx_lm.server (recommended)**

```bash
mlx_lm.server \
  --model mlx-community/qwen2.5-coder-7b \
  --port 8080 \
  --host 127.0.0.1
```

**Option B: Custom Python server**

Create `mlx_server.py`:

```python
#!/usr/bin/env python3
from mlx_lm import load, generate
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load model at startup
model, tokenizer = load("mlx-community/qwen2.5-coder-7b")

@app.route('/generate', methods=['POST'])
def generate_text():
    data = request.json
    prompt = data['prompt']
    max_tokens = data.get('max_tokens', 1024)
    temperature = data.get('temperature', 0.7)
    
    response = generate(
        model, 
        tokenizer, 
        prompt=prompt,
        max_tokens=max_tokens,
        temp=temperature
    )
    
    return jsonify({'text': response})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
```

Run it:

```bash
python mlx_server.py
```

### 4. Verify MLX is Working

```bash
# Health check
curl http://127.0.0.1:8080/health

# Test generation
curl -s http://127.0.0.1:8080/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Write a Python function to reverse a string:",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

### 5. Configure Athena Router

Set environment variables:

```bash
export MLX_ENDPOINT=http://127.0.0.1:8080
export MLX_MODEL=qwen2.5-coder-7b
```

Or update `services/router/policies/local_first.yaml`:

```yaml
order:
  - mlx
  - ollama
  - mcp_browser
  - cloud

timeouts_ms:
  mlx: 1500
  ollama: 2000
```

### 6. Start Router with MLX

```bash
cd /Users/christianmerrill/Documents/GitHub
python services/router/app.py
```

Test routing:

```bash
curl -s http://127.0.0.1:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Write a Swift function to sort an array"}' | jq
```

Expected response:

```json
{
  "route": "mlx",
  "text": "...",
  "latency_ms": 450,
  "cached": false,
  "provider_health": {
    "mlx": {
      "available": true,
      "p95_latency_ms": 480
    }
  }
}
```

## Model Selection Guide

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| llama-3.2-3b | 3B | ⚡⚡⚡ | ⭐⭐ | Quick responses, chat |
| qwen2.5-coder-7b | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Code generation (recommended) |
| qwen2.5-coder-14b | 14B | ⚡ | ⭐⭐⭐⭐⭐ | Complex code, reasoning |
| deepseek-coder-6.7b | 6.7B | ⚡⚡ | ⭐⭐⭐⭐ | Code completion |

## Performance Tuning

### Pre-warming (Recommended)

The router pre-warms MLX on startup to avoid cold-start latency:

```python
# In app.py startup()
await providers['mlx'].generate("test", max_tokens=5)
```

This loads the model into memory before the first real request.

### Memory Management

```bash
# Check model memory usage
ps aux | grep mlx

# For large models (14B+), increase swap
sudo sysctl vm.swapusage
```

### Concurrent Requests

MLX handles 1 request at a time efficiently. The router rate-limits to 4 concurrent MLX requests by default:

```yaml
# In local_first.yaml
rate_limits:
  max_concurrent_mlx: 4
```

## Troubleshooting

### Model Not Found

```bash
# List available models
ls ~/.cache/mlx/

# Re-download
mlx_lm.server --model mlx-community/qwen2.5-coder-7b
```

### Out of Memory

```bash
# Use smaller model
mlx_lm.server --model mlx-community/llama-3.2-3b --port 8080
```

### Slow Performance

- **First request is slow**: Normal - model loads into memory
- **All requests slow**: Check Activity Monitor for CPU/memory pressure
- **Reduce max_tokens**: Set `max_tokens: 512` for faster responses

### Connection Refused

```bash
# Check if MLX server is running
lsof -i :8080

# Check logs
tail -f logs/mlx_server.log
```

## Integration with Bridge Service

The bridge service should route to the router on port 9113:

```python
# In bridge_service.py
ROUTER_URL = "http://127.0.0.1:9113/route"

response = requests.post(ROUTER_URL, json={
    "prompt": user_message,
    "max_tokens": 1024
})

route_result = response.json()
# route_result['route'] will be 'mlx' if MLX is healthy
```

## Running as LaunchDaemon (Optional)

Create `/Library/LaunchDaemons/com.athena.mlx.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.mlx</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/mlx_lm.server</string>
        <string>--model</string>
        <string>mlx-community/qwen2.5-coder-7b</string>
        <string>--port</string>
        <string>8080</string>
        <string>--host</string>
        <string>127.0.0.1</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/mlx.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/mlx.error.log</string>
</dict>
</plist>
```

Load it:

```bash
sudo launchctl load /Library/LaunchDaemons/com.athena.mlx.plist
```

## Next Steps

1. ✅ MLX running on port 8080
2. ✅ Router running on port 9113
3. Test failover: Stop MLX, verify router fails over to Ollama
4. Monitor metrics: Open Grafana dashboard at http://localhost:3000
5. Review decisions: `tail -f state/router_decisions.jsonl`

## Resources

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [MLX-LM GitHub](https://github.com/ml-explore/mlx-examples/tree/main/llms)
- [MLX Community Models](https://huggingface.co/mlx-community)
- [Athena Router README](../../services/router/README.md)


