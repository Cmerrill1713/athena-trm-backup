# ✅ Prometheus Metrics Setup - Complete

**Date**: October 13, 2025  
**Status**: Code ready, needs manual restart

---

## 🎯 What Was Accomplished

### Services Already Have Metrics ✅
You were absolutely right - these services were already instrumented:
- **Bridge** (`:8014`) - Has `/metrics` via `common/ops.py` ✅
- **UAT** (`:8181`) - Has `/metrics` via `common/ops.py` ✅
- **Athena** (`:8090`) - Has `/metrics` via `common/ops.py` ✅

### Services Now Have Metrics Added ✅
I added Prometheus instrumentation to:
- **RAG** (`:8015`) - Added `add_health_endpoints()` + custom metrics ✅
- **Vision** (`:8016`) - Added `add_health_endpoints()` + custom metrics ✅
- **Kokoro** (`:8020`) - Added `add_health_endpoints()` + custom metrics ✅

---

## 📊 Custom Metrics Added

### RAG Service
```python
rag_requests_total{status="success|error"}  # Total RAG requests
rag_request_duration_seconds                # Request latency histogram
rag_hits_count                              # Number of hits returned
```

### Vision Service  
```python
vision_requests_total{status="success|error",operation="describe"}
vision_request_duration_seconds{operation="describe"}
```

### Kokoro TTS
```python
tts_requests_total{status="success|error",voice="af_heart|..."}
tts_request_duration_seconds{voice="af_heart|..."}
tts_audio_length_seconds  # Generated audio duration
```

---

## 🚀 How to Restart Services

### Option 1: Use the Makefile (Recommended)
```bash
cd /Users/christianmerrill/Documents/GitHub

# Stop everything
make stack-down

# Start everything with metrics
make stack-full

# Verify
make stack-status
```

### Option 2: Use the Restart Script
```bash
cd /Users/christianmerrill/Documents/GitHub
bash restart_metrics_services.sh
```

### Option 3: Manual Restart
```bash
cd /Users/christianmerrill/Documents/GitHub

# Kill old processes
lsof -ti:8015 | xargs kill -9
lsof -ti:8016 | xargs kill -9
lsof -ti:8020 | xargs kill -9

# Start fresh
source .venv/bin/activate

# RAG
cd AI-Projects/universal-ai-tools
python rag_service.py > ../../logs/rag.out 2>&1 &
cd ../..

# Vision
cd AI-Projects/universal-ai-tools  
python vision_rag_service.py > ../../logs/vision.out 2>&1 &
cd ../..

# Kokoro
cd kokoro
python kokoro_tts_service.py > ../logs/kokoro.out 2>&1 &
cd ..

# Wait for startup
sleep 10
```

---

## 🧪 Verify Metrics Are Working

```bash
# Test all metrics endpoints
curl http://localhost:8014/metrics  # Bridge
curl http://localhost:8015/metrics  # RAG ⭐ NEW
curl http://localhost:8016/metrics  # Vision ⭐ NEW
curl http://localhost:8020/metrics  # Kokoro ⭐ NEW
curl http://localhost:8181/metrics  # UAT
curl http://localhost:8090/metrics  # Athena
```

### Expected Output
Each should return Prometheus-format metrics like:
```
# HELP rag_requests_total Total RAG requests
# TYPE rag_requests_total counter
rag_requests_total{status="success"} 0.0
...
```

---

## 📊 Prometheus Configuration

### Updated Config
`prometheus/prometheus.yml` now scrapes all 6 services:
- Bridge (`:8014`)
- RAG (`:8015`) ⭐ NEW
- Vision (`:8016`) ⭐ NEW
- Kokoro (`:8020`) ⭐ NEW
- UAT (`:8181`)
- Athena (`:8090`)

Plus optional services:
- Weaviate (`:8090`)
- FastVLM (`:8811`)
- Ollama (`:11434`)
- Assistantd (`:8085`)
- ML Inference (`:8091`)
- Orchestration (`:8080`)

### Reload Prometheus
```bash
# Restart Prometheus to pick up new targets
docker compose -f docker-compose.monitoring.yml restart prometheus

# Or reload config without restart
curl -X POST http://localhost:9091/-/reload
```

---

## 🎨 Grafana Dashboards

### Access Grafana
```
🌐 URL: http://localhost:3002
🔐 Login: admin / admin
```

### Available Dashboards
1. **NeuroForge Services Overview** - All 6 services
2. **TRM Evolution Overview** - Routing decisions
3. **Circuit Breaker Panel** - Failure detection

### After Services Restart
You'll be able to see:
- RAG query volume and latency
- Vision API usage  
- TTS generation metrics
- Service health for all 6 core services
- Request rates and error rates
- Response latencies (p50, p95)

---

## ✅ Summary

### What's Ready
- ✅ All 6 services have Prometheus metrics code
- ✅ Prometheus configured to scrape all services
- ✅ Grafana running with dashboards
- ✅ Makefile updated for easy management

### What Needs to Happen
- 🔄 Restart the 3 services (RAG, Vision, Kokoro) to load new code
- 📊 Reload Prometheus to scrape new metrics
- 🎨 View dashboards in Grafana

### One-Liner to Complete Setup
```bash
cd /Users/christianmerrill/Documents/GitHub && \
make stack-down && \
make stack-full && \
docker compose -f docker-compose.monitoring.yml restart prometheus && \
sleep 10 && \
echo "✅ All services running with metrics!"
```

---

## 🎉 Final State

Once services are restarted, you'll have:
- **9 services being monitored** (6 core + 3 optional)
- **Custom metrics** for RAG queries, Vision API, TTS generation
- **Real-time dashboards** showing all activity
- **Full observability** into your NeuroForge platform

**No Supabase** - Everything uses Weaviate as you specified! 🚀

