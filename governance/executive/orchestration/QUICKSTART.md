# FastVLM Quick Start

Get Apple's vision-language model running in 5 minutes.

## One-Liner Installation

```bash
cd /Users/christianmerrill/Documents/GitHub
make fastvlm-setup
```

This downloads ~2GB for the 1.5B model (recommended).

## Start Server

Terminal 1:
```bash
make fastvlm-server
```

Wait for: `✅ FastVLM Server on 127.0.0.1:8811`

## Test It

Terminal 2:
```bash
# Health check
make fastvlm-test

# Ask about an image (save a screenshot first)
make vision IMG=~/Desktop/screenshot.png PROMPT="What's in this image?"
```

## Your First Vision Call

### Command Line

```bash
python3 scripts/athena_vision.py image.png "Describe what you see"
```

### Python

```python
from fastvlm.fastvlm_client import call_fastvlm

result = call_fastvlm("screenshot.png", "What's shown here?")
print(result)
```

### With Routing (Auto-selects FastVLM for vision tasks)

```python
from src.core.routing.fastvlm_provider import get_provider

provider = get_provider()
text = provider.call("chart.png", "Extract the data from this chart")
print(text)
```

## Use Cases

### 📊 Chart Analysis
```bash
make vision IMG=revenue-chart.png PROMPT="Extract all data points and trends"
```

### 🖼️ Screenshot Understanding
```bash
make vision IMG=ui-screenshot.png PROMPT="Describe the UI elements and layout"
```

### 📝 OCR
```bash
make vision IMG=document.jpg PROMPT="Extract all text from this document"
```

### 🏗️ Diagram Analysis
```bash
make vision IMG=architecture.png PROMPT="Explain this system architecture"
```

## Observability

### Check Metrics
```bash
make fastvlm-metrics
```

### View in Prometheus
```bash
# Start monitoring stack if not running
make monitoring-up

# Open Prometheus
open http://localhost:9090/targets
```

Look for the `fastvlm` job - should show "UP" status.

### Query Metrics

```promql
# Request rate
rate(fastvlm_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(fastvlm_latency_ms_bucket[5m]))

# Success rate
rate(fastvlm_requests_total{status="success"}[5m])
/ rate(fastvlm_requests_total[5m])
```

## Model Variants

Switch to different model sizes:

### 0.5B (Fastest)
```bash
export FASTVLM_MODEL="checkpoints/fastvlm_0.5b_stage3"
make fastvlm-server
```

### 7B (Best Quality)
```bash
export FASTVLM_MODEL="checkpoints/fastvlm_7b_stage3"
make fastvlm-server
```

## Troubleshooting

### Server won't start

```bash
# Check if model was downloaded
ls -la fastvlm/ml-fastvlm/checkpoints/

# If empty, re-run setup
cd fastvlm/ml-fastvlm
bash get_models.sh
```

### Health check fails

```bash
# Check if server is running
ps aux | grep fastvlm_server

# Check port
lsof -i :8811

# Manual health check
curl http://127.0.0.1:8811/health
```

### Import errors

```bash
# Add to PYTHONPATH
export PYTHONPATH="/Users/christianmerrill/Documents/GitHub:$PYTHONPATH"
```

## Integration with Your Stack

### In Athena Reporter (Voice + Visual)

```bash
make vision IMG=chart.png PROMPT="Analyze this" --report
```

Opens a window with the analysis and reads it aloud (Samantha voice).

### In Routing System

FastVLM auto-registers and is selected when:
- Image/screenshot provided
- Capabilities include: vision, ocr, chart_reading
- Router prefers local models (no API cost)

### With RAG

```python
# 1. Extract from image
from fastvlm.fastvlm_client import call_fastvlm
chart_data = call_fastvlm("chart.png", "Extract all values")

# 2. Search relevant docs
from your_rag import search
docs = search(chart_data)

# 3. Generate insights
response = llm(f"Data: {chart_data}\n\nContext: {docs}")
```

## Next Steps

1. **Read full docs**: `fastvlm/README.md`
2. **Check routing integration**: `src/core/routing/fastvlm_provider.py`
3. **View metrics**: `make fastvlm-metrics`
4. **Try with your images**: `make vision IMG=... PROMPT=...`

## Performance Expectations

**1.5B model on M1/M2:**
- Small images: 200-500ms
- Medium images: 500-1500ms
- Large images: 1500-3000ms

**0.5B model on M1/M2:**
- Small images: 100-300ms
- Medium images: 300-800ms
- Large images: 800-1500ms

## Common Commands

```bash
# Setup (once)
make fastvlm-setup

# Daily usage
make fastvlm-server          # Start server
make fastvlm-test            # Health check
make vision IMG=x.png PROMPT="..." # Ask about image

# Operations
make fastvlm-health          # Detailed status
make fastvlm-metrics         # View metrics
make fastvlm-down            # Stop server

# Monitoring
make monitoring-up           # Start Prometheus + Grafana
open http://localhost:9090   # Prometheus
open http://localhost:3001   # Grafana
```

## Pro Tips

1. **Background server**: Add to cron or launchd for auto-start
2. **Batch processing**: Loop through images in a directory
3. **Custom prompts**: Tailor prompts for your use case
4. **Cache results**: Store in SQLite for offline access
5. **Chain with RAG**: Use vision output to query vector DB

## Resources

- 📚 [Full Documentation](README.md)
- 🍎 [Apple's FastVLM Repo](https://github.com/apple/ml-fastvlm)
- 📊 [Observability Guide](../OBSERVABILITY_COMPLETE.md)
- 🎯 [Routing System](../src/core/routing/README.md)

---

**Questions?** Check `fastvlm/README.md` or run `make help`

