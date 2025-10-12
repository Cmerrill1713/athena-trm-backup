# FastVLM Integration for Athena

Apple's FastVLM vision-language model integrated into the Athena routing system with full observability.

## Features

✅ **Fast local vision inference** - 0.5B, 1.5B, 7B models  
✅ **FastAPI server** - REST API with `/v1/vision` endpoint  
✅ **Full observability** - Prometheus metrics + Sentry tracing  
✅ **Routing integration** - Auto-registered in model selector  
✅ **CLI convenience** - `athena vision <image> "<prompt>"`  
✅ **Athena Reporter** - Voice + visual output support  

## Quick Start

### 1. Setup (one-time)

```bash
# From workspace root
make fastvlm-setup
```

This will:
- Clone Apple's ml-fastvlm repository
- Create virtual environment
- Install dependencies
- Download model checkpoints (~2GB for 1.5B)

### 2. Start the server

```bash
make fastvlm-server
```

Server will start on `http://127.0.0.1:8811`

### 3. Test it

```bash
# Health check
make fastvlm-test

# Or via CLI
python3 scripts/athena_vision.py --health

# Try with an image
python3 scripts/athena_vision.py screenshot.png "What's in this image?"
```

## Usage

### CLI - Direct

```bash
# Basic
python3 scripts/athena_vision.py image.png "Describe this"

# JSON output
python3 scripts/athena_vision.py image.png "What's shown?" --json

# With Athena Reporter (voice + visual)
python3 scripts/athena_vision.py chart.png "Extract data" --report
```

### CLI - Makefile shortcut

```bash
make vision IMG=screenshot.png PROMPT="What's in this screenshot?"
```

### Python API

```python
from fastvlm.fastvlm_client import FastVLMClient

client = FastVLMClient("http://127.0.0.1:8811")

# Simple call
result = client.vision("image.png", "Describe this image")
print(result["text"])
print(f"Latency: {result['latency_ms']}ms")

# Check health
if client.is_healthy():
    print("Server is ready")
```

### Routing Integration

FastVLM automatically registers with the model selector:

```python
from src.core.routing.fastvlm_provider import get_provider

# Get provider
provider = get_provider()

# Check capabilities
caps = provider.get_capabilities()
# {'vision': 0.85, 'ocr': 0.82, 'chart_reading': 0.78, ...}

# Call with tracing & metrics
result = provider.call(
    image_path="screenshot.png",
    prompt="What's in this screenshot?",
    context={"user_id": "123", "session": "abc"}
)
```

## Observability

### Metrics

FastVLM exposes Prometheus metrics on `/metrics`:

```promql
# Request count by status
fastvlm_requests_total{status="success"}

# Latency percentiles
fastvlm_latency_ms{quantile="0.95"}

# Active requests
fastvlm_active_requests

# Image sizes
fastvlm_image_size_bytes
```

View live metrics:
```bash
make fastvlm-metrics
```

### Prometheus Scraping

FastVLM is automatically scraped by Prometheus (see `prometheus/prometheus.yml`):

```yaml
- job_name: 'fastvlm'
  static_configs:
    - targets: ['127.0.0.1:8811']
  metrics_path: /metrics
  scrape_interval: 10s
```

### Sentry Tracing

All vision operations are traced with Sentry spans:

```python
# Automatically creates span:
# op: "vision.inference"
# name: "FastVLM: screenshot.png"
# attributes: model, endpoint, image, prompt_length, context.*

result = provider.call(image_path, prompt, context)
```

Follows user's Sentry instrumentation rules (see `.cursorrules`).

## Configuration

### Environment Variables

```bash
# FastVLM root directory (where ml-fastvlm is cloned)
export FASTVLM_ROOT="/path/to/ml-fastvlm"

# Model variant
export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3"

# Server settings
export FASTVLM_HOST="127.0.0.1"
export FASTVLM_PORT="8811"

# Observability
export ENV="prod"
export BUILD_SHA="abc123"

# Client endpoint (for routing)
export FASTVLM_ENDPOINT="http://127.0.0.1:8811"
```

### Model Variants

Three model sizes available:

| Model | Size | Use Case | Quality | Speed |
|-------|------|----------|---------|-------|
| 0.5B  | ~1GB | Fast prototyping | Good | Very fast |
| 1.5B  | ~3GB | **Recommended** | Excellent | Fast |
| 7B    | ~14GB | Highest quality | Best | Moderate |

Change variant:
```bash
export FASTVLM_MODEL="checkpoints/fastvlm_7b_stage3"
make fastvlm-server
```

## API Reference

### POST /v1/vision

**Request:**
```bash
curl -X POST http://127.0.0.1:8811/v1/vision \
  -F "image=@screenshot.png" \
  -F "prompt=What's in this image?"
```

**Response:**
```json
{
  "text": "This image shows a system architecture diagram...",
  "latency_ms": 487.3,
  "model": "checkpoints/fastvlm_1.5b_stage3",
  "image_size": 125834
}
```

### GET /health

**Response:**
```json
{
  "status": "healthy",
  "model": "checkpoints/fastvlm_1.5b_stage3",
  "fastvlm_root": "/Users/.../ml-fastvlm",
  "model_exists": true
}
```

### GET /metrics

Prometheus metrics in text format.

## Routing Policy

FastVLM is automatically selected when:
- User provides an image/screenshot/chart
- Request has `vision`, `ocr`, or `screenshot_analysis` capability requirement
- Router prefers local models (cost-free, low latency)

Registry entry:
```python
{
    "name": "fastvlm-1.5b",
    "provider": "fastvlm",
    "caps": {"vision", "ocr", "chart_reading", "screenshot_analysis"},
    "quality": 0.85,  # Updated by online learner
    "context": 4096,
    "latency_ms": 500,
    "cost_tier": "free",
    "local": True
}
```

## Makefile Targets

```bash
# Setup
make fastvlm-setup        # One-time setup

# Server management
make fastvlm-server       # Start server (foreground)
make fastvlm-up           # Start in background
make fastvlm-down         # Stop server

# Testing
make fastvlm-test         # Health check
make fastvlm-health       # Detailed status
make fastvlm-metrics      # View metrics
make fastvlm-demo         # Run demo

# Usage
make vision IMG=file.png PROMPT="describe this"
```

## Troubleshooting

### Server won't start

```bash
# Check setup
ls -la fastvlm/ml-fastvlm/

# Verify model exists
ls -la fastvlm/ml-fastvlm/checkpoints/

# Check environment
echo $FASTVLM_ROOT
echo $FASTVLM_MODEL
```

### Health check fails

```bash
# Manual test
curl http://127.0.0.1:8811/health

# Check logs
tail -f fastvlm/fastvlm_server.log
```

### Import errors in routing

```bash
# Add to PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# Or use absolute imports
```

## Performance

Expected latency (1.5B model on M1/M2):
- Small images (<100KB): 200-500ms
- Medium images (100KB-1MB): 500-1500ms
- Large images (>1MB): 1500-3000ms

TTFT (time to first token) is very fast thanks to FastViTHD encoder.

## Apple Silicon Optimization

For maximum performance, use Apple's Core ML exports:

```bash
cd fastvlm/ml-fastvlm
# Follow "Inference on Apple Silicon" instructions
# This will use Metal GPU acceleration
```

## Integration Examples

### With RAG

```python
# 1. Extract text from chart with FastVLM
chart_data = provider.call("chart.png", "Extract all data points")

# 2. Ground with RAG
from rag_system import search_docs
context = search_docs(chart_data)

# 3. Generate response
response = llm_call(f"Based on this chart: {chart_data}\n\nContext: {context}")
```

### With Athena Reporter

```python
from fastvlm.fastvlm_client import call_fastvlm
from AthenaReporter import show_report

result = call_fastvlm("diagram.png", "Explain this architecture")

markdown = f"""# Architecture Analysis

{result}

*Analyzed with FastVLM 1.5B*
"""

show_report(markdown, speak=True)  # Visual + voice
```

## References

- [Apple FastVLM GitHub](https://github.com/apple/ml-fastvlm)
- [FastVLM Paper](https://arxiv.org/abs/...) (when available)
- [Athena Routing System](../src/core/routing/README.md)
- [Observability Guide](../OBSERVABILITY_COMPLETE.md)

## License

FastVLM: Apple's license (see ml-fastvlm/LICENSE)  
Integration code: Your workspace license

