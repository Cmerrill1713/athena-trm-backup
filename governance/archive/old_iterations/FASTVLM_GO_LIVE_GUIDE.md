# 🚀 FastVLM Go-Live Guide

**Quick path from zero to working vision queries in ~5 minutes**

---

## ✅ Step-by-Step (First Time)

### 1. Setup FastVLM (one-time, ~5 minutes)

This downloads Apple's FastVLM model (~2GB for 1.5B variant):

```bash
cd /Users/christianmerrill/Documents/GitHub
make fastvlm-setup
```

**What it does**:
- Clones https://github.com/apple/ml-fastvlm
- Creates Python venv
- Installs dependencies
- Downloads model checkpoint (~2GB)

**Expected output**:
```
✅ FastVLM repository cloned
✅ Virtual environment created
✅ FastVLM installed
✅ Models downloaded
✅ Model checkpoint found: checkpoints/fastvlm_1.5b_stage3
```

---

### 2. Start Monitoring Stack

```bash
make monitoring-up
```

Starts:
- Prometheus (port 9090) - metrics collection
- Grafana (port 3001) - dashboards

**Verify**:
```bash
curl -s http://localhost:9090/-/healthy  # Should return "Prometheus is Healthy"
```

---

### 3. Start FastVLM Server

**New terminal** (keep it open):

```bash
cd /Users/christianmerrill/Documents/GitHub
make fastvlm-server
```

**Expected startup**:
```
Starting FastVLM Server on 127.0.0.1:8811
Model: checkpoints/fastvlm_1.5b_stage3
Environment: dev
Metrics: enabled
Warming up model with test inference...
✅ Model warmed up: 512ms inference, 3.2s total
🚀 FastVLM Server ready on http://127.0.0.1:8811
INFO:     Uvicorn running on http://127.0.0.1:8811
```

**Warmup eliminates cold-start latency on first request!**

---

### 4. Run 90-Second Validation

Wait 30 seconds after server starts, then:

```bash
make fastvlm-validate
```

**Expected results**:
```
[1/6] ✓ Server is healthy and warmed up
[2/6] ✓ Recording rules active (p95: 487ms)
[3/6] ✓ Success rate: 100% (excellent)
[4/6] ✓ No fallbacks triggered (good!)
[5/6] ✓ Recording rules loaded: 10 rules
[6/6] ✓ Smoke test passed (6 tests)

✅ FastVLM Validation Complete
```

---

### 5. Try It Live!

Grab a screenshot first:
```bash
screencapture ~/Desktop/test.png
```

Then analyze it:
```bash
python3 scripts/athena_vision.py ~/Desktop/test.png \
  "Summarize this in 2 sentences" --report
```

**What happens**:
- ✅ FastVLM analyzes the image
- ✅ Markdown report opens in default app
- ✅ Samantha voice speaks 2-3 sentence summary
- ✅ Metrics recorded in Prometheus

---

## 🧪 Quick Sanity Checks (10 seconds each)

### Server Health
```bash
curl -s http://127.0.0.1:8811/health | jq
```

**Expected**:
```json
{
  "status": "healthy",
  "model": "checkpoints/fastvlm_1.5b_stage3",
  "fastvlm_root": "/Users/.../ml-fastvlm",
  "model_exists": true
}
```

### Pre-Aggregated Metrics (Fast!)
```bash
# p95 latency
curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:latency_p95_ms:5m' | jq

# Success rate (should be ~1.0)
curl -s 'http://localhost:9090/api/v1/query?query=fastvlm:success_rate:5m' | jq

# Fallback rate (should be 0)
curl -s 'http://localhost:9090/api/v1/query?query=rate(fastvlm_fallback_total[5m])' | jq
```

### Check Metrics Endpoint
```bash
curl -s http://127.0.0.1:8811/metrics | grep "^fastvlm_" | head -10
```

---

## 🎯 Task-Specific Helpers

Pre-configured prompts for common tasks:

```bash
# Extract text from document
make vision-ocr IMG=document.png

# Extract data from chart
make vision-chart IMG=sales-chart.png

# Analyze UI/screenshot
make vision-ui IMG=app-screenshot.png

# Explain technical diagram
make vision-diagram IMG=architecture.png
```

---

## 📊 Grafana Dashboard (Quick Add)

1. Open Grafana: http://localhost:3001
2. Edit your dashboard
3. Add panels with these **fast queries** (using recording rules):

```promql
# Requests per minute
fastvlm:requests_per_minute:5m{env="$env"}

# p95 Latency (ms)
fastvlm:latency_p95_ms:5m{env="$env"}

# Success Rate (%)
fastvlm:success_rate:5m{env="$env"} * 100

# Fallback Rate (should be near 0)
rate(fastvlm_fallback_total{env="$env"}[5m])

# p50 Latency
fastvlm:latency_p50_ms:5m{env="$env"}

# p99 Latency
fastvlm:latency_p99_ms:5m{env="$env"}

# Average image size
fastvlm:avg_image_size_bytes:5m{env="$env"}
```

**Why recording rules?** 10-100× faster dashboard load times!

---

## 🧰 Troubleshooting (Fast Triage)

### 1. Server Won't Start

**Symptom**: Error about model not found

**Fix**:
```bash
# Run setup (downloads model)
make fastvlm-setup

# Verify model exists
ls -la fastvlm/ml-fastvlm/checkpoints/

# Try again
make fastvlm-server
```

---

### 2. Port Already in Use

**Symptom**: `Address already in use`

**Check**:
```bash
lsof -i :8811
```

**Fix**:
```bash
# Kill existing process
pkill -f fastvlm_server

# Or use different port
FASTVLM_PORT=8812 make fastvlm-server
```

---

### 3. Prometheus Shows No Data

**Symptom**: Recording rules return empty results

**Check scrape config**:
```bash
# Should see fastvlm target
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job=="fastvlm")'
```

**Fix**:
```bash
# Verify prometheus.yml has fastvlm job
grep -A 5 "job_name: 'fastvlm'" prometheus/prometheus.yml

# Reload Prometheus
docker restart prometheus
# or
make monitoring-down && make monitoring-up
```

---

### 4. Reporter Opens But No Voice

**Symptom**: Markdown opens but silent

**Check**:
```bash
# Test TTS directly
say -v Samantha "Testing voice"
```

**Fix**:
- macOS: System Settings → Privacy & Security → Accessibility
- Add Terminal.app or your editor
- System Settings → Accessibility → Spoken Content
- Enable "Speak selection" or "Speak items under pointer"

**Workaround**:
```bash
# Use without voice
python3 scripts/athena_vision.py image.png "describe" --json
```

---

### 5. Validation Shows "Server Not Running"

**Symptom**: `make fastvlm-validate` fails step 1

**Fix**:
```bash
# Start server in background
make fastvlm-server &

# Wait for warmup (30 seconds)
sleep 30

# Run validation
make fastvlm-validate
```

---

### 6. Slow First Request

**Expected!** First inference after server start can be slow (~3-5s).

**Fix**: We already added warmup! Server warms up automatically on start.

**Verify warmup logs**:
```
Warming up model with test inference...
✅ Model warmed up: 512ms inference, 3.2s total
```

---

### 7. High Memory Usage (7B Model)

**Symptom**: OOM or slow performance

**Fix**: Use smaller model
```bash
export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3"
make fastvlm-server
```

Or even faster:
```bash
export FASTVLM_MODEL="checkpoints/fastvlm_0.5b_stage3"
make fastvlm-server
```

---

## 🔄 Daily Operations

### Start Everything
```bash
# Terminal 1: Monitoring
make monitoring-up

# Terminal 2: FastVLM
make fastvlm-server
```

### Check Health
```bash
make fastvlm-health
```

### View Metrics
```bash
make fastvlm-metrics
```

### Run Tests
```bash
make fastvlm-smoke
```

### Stop Everything
```bash
# Stop FastVLM
make fastvlm-down

# Stop monitoring
make monitoring-down
```

---

## 🎨 Advanced: RAG Integration

Vision → Knowledge Base → Grounded Answer

```bash
python3 scripts/athena_vision.py chart.png \
  "What insights can you extract?" \
  --rag --report
```

**Flow**:
1. 🔍 FastVLM extracts data from image
2. 🔎 RAG searches knowledge base for context
3. 💡 LLM generates answer with citations
4. 🔊 Samantha speaks summary

**Output includes**:
- Vision analysis
- Retrieved sources with relevance scores
- Grounded explanation with [Source N] citations

---

## 📈 Performance Expectations

### 1.5B Model on M1/M2

| Scenario | Expected Latency |
|----------|------------------|
| First request (with warmup) | 200-500ms |
| Subsequent small images | 200-500ms |
| Medium images (100KB-1MB) | 500-1500ms |
| Large images (>1MB) | 1500-3000ms |

### 0.5B Model on M1/M2

| Scenario | Expected Latency |
|----------|------------------|
| Small images | 100-300ms |
| Medium images | 300-800ms |
| Large images | 800-1500ms |

**Recording rules make dashboards 10-100× faster!**

---

## ✅ Success Checklist

After going live, verify:

- [ ] `make fastvlm-validate` shows all green ✓
- [ ] Prometheus scraping FastVLM (check /targets)
- [ ] Recording rules active (fast dashboard queries)
- [ ] Smoke test passes (6 image types)
- [ ] Real vision query works
- [ ] Voice output working (--report)
- [ ] Grafana panels showing data
- [ ] Fallback rate = 0
- [ ] p95 latency < 1500ms

---

## 🎯 Quick Reference

```bash
# Setup (once)
make fastvlm-setup

# Daily ops
make fastvlm-server          # Start server
make fastvlm-validate        # 90s validation
make fastvlm-health          # Check status
make fastvlm-metrics         # View metrics
make fastvlm-smoke           # Run tests

# Usage
make vision IMG=file.png PROMPT="describe"
make vision-chart IMG=chart.png
make vision-ocr IMG=doc.png

# With voice + visual
python3 scripts/athena_vision.py img.png "prompt" --report

# With RAG grounding
python3 scripts/athena_vision.py img.png "prompt" --rag --report

# Stop
make fastvlm-down
```

---

## 📚 Documentation

- **This Guide**: Quick start & troubleshooting
- **README.md**: `fastvlm/README.md` - Full reference
- **Quick Start**: `fastvlm/QUICKSTART.md` - 5-minute guide
- **Upgrades**: `FASTVLM_UPGRADES_COMPLETE.md` - What's new
- **Integration**: `FASTVLM_INTEGRATION_COMPLETE.md` - Technical details

---

## 🎉 You're Ready!

Run these commands in order:

```bash
# 1. Setup (if not done)
make fastvlm-setup

# 2. Start monitoring
make monitoring-up

# 3. Start FastVLM (new terminal)
make fastvlm-server

# 4. Wait 30 seconds, validate
sleep 30
make fastvlm-validate

# 5. Try it!
python3 scripts/athena_vision.py ~/Desktop/test.png \
  "What's in this image?" --report
```

**FastVLM is production-ready with full observability!** 🚀

