# 🎚️ Stack Profiles - Choose Your Layer

> **Modular startup: Pick what you need**

---

## 🎯 Stack Profiles

### Profile 1: Core (Minimal - 2 seconds)
```bash
make stack-up
```

**Starts:**
- ✅ UAT :8181
- ✅ Athena :8090
- ✅ Bridge :8014

**Use when:**
- Quick development
- Testing chat without voice/vision
- Minimal resource usage

---

### Profile 2: Core + Voice (3 seconds)
```bash
make stack-up
make stack-voice
```

**Adds:**
- ✅ Kokoro TTS :8020

**Use when:**
- Testing voice chat
- Need natural TTS
- Want voice feedback

---

### Profile 3: Core + RAG (4 seconds)
```bash
make stack-up
make stack-rag
```

**Adds:**
- ✅ RAG Service :8015 (knowledge search)

**Use when:**
- Testing knowledge grounding
- Need context retrieval
- Want cited responses

---

### Profile 4: Core + Vision (5 seconds)
```bash
make stack-up
make stack-vision
```

**Adds:**
- ✅ FastVLM :8811
- ✅ Vision RAG :8016

**Use when:**
- Testing image analysis
- Need OCR/chart extraction
- Want vision capabilities

---

### Profile 5: Full Stack (6 seconds)
```bash
make stack-full
```

**Starts everything:**
- ✅ UAT, Athena, Bridge (core)
- ✅ Kokoro TTS (voice)
- ✅ RAG Service (knowledge)
- ✅ FastVLM (vision)
- ✅ Vision RAG (image + knowledge)

**Use when:**
- Full feature testing
- Demo/showcase
- Production-like environment

---

## 🔧 Port Map

| Service | Port | Started By | Optional |
|---------|------|------------|----------|
| **Bridge** | 8014 | `stack-up` | Core |
| **Athena** | 8090 | `stack-up` | Core |
| **UAT** | 8181 | `stack-up` | Core |
| **Kokoro TTS** | 8020 | `stack-voice` | Optional |
| **RAG** | 8015 | `stack-rag` | Optional |
| **FastVLM** | 8811 | `stack-vision` | Optional |
| **Vision RAG** | 8016 | `stack-vision` | Optional |
| **Weaviate** | 8095 | Manual | Optional |
| **OTLP** | 4318 | `otel-up` | Optional |
| **Prometheus** | 9090 | `monitoring-up` | Optional |
| **Grafana** | 3001 | `monitoring-up` | Optional |

---

## 🎯 Common Workflows

### Chat Only (Fast Development)
```bash
make stack-up
cd NeuroForgeApp
swift run
```

### Voice Chat (Most Common)
```bash
make stack-up
make stack-voice
cd NeuroForgeApp
swift run
```

### Vision + RAG (Full Features)
```bash
make stack-full
cd NeuroForgeApp
swift run
```

### With Monitoring (Production-Like)
```bash
make stack-full
make otel-up
make monitoring-up
# Grafana: http://localhost:3001
```

---

## 🛑 Stopping Services

### Stop Core Only
```bash
make stack-down
```

### Stop Everything
```bash
make stack-full-down
```

### Stop Individual Layers
```bash
make stack-voice-down
make stack-rag-down
make stack-vision-down
```

---

## 📊 Service Dependencies

```
Bridge (8014)
  ├─→ Athena (8090) - required
  ├─→ UAT (8181) - required
  ├─→ RAG (8015) - optional (graceful degradation)
  └─→ Vision (8811) - optional (graceful degradation)

NeuroForgeApp
  ├─→ Bridge (8014) - required
  └─→ Kokoro (8020) - optional (falls back to system voice)

Vision RAG (8016)
  ├─→ FastVLM (8811) OR Ollama - required
  ├─→ RAG (8015) - optional
  └─→ Weaviate (8095) - optional

RAG (8015)
  └─→ Weaviate (8095) - optional (can work standalone)
```

---

## 🧪 Testing Each Profile

### Core Stack
```bash
make stack-up
curl http://127.0.0.1:8014/ready
# Should return: {"status":"ready"}
```

### + Voice
```bash
make stack-voice
curl http://127.0.0.1:8020/health
# Should return: {"status":"ok","model":"Kokoro-82M"}
```

### + RAG
```bash
make stack-rag
curl http://127.0.0.1:8015/ready
# Should return: {"status":"ready"}
```

### + Vision
```bash
make stack-vision
curl http://127.0.0.1:8811/health
curl http://127.0.0.1:8016/ready
```

### Full Status
```bash
make stack-status-full
# Shows ✅/❌ for all services
```

---

## 🎯 Recommendations

### For Development
**Use:** Core + Voice
```bash
make stack-up && make stack-voice
```
**Why:** Fast startup, voice feedback, minimal resources

### For Testing
**Use:** Full stack
```bash
make stack-full
```
**Why:** Test all integrations, catch edge cases

### For Demos
**Use:** Full stack + monitoring
```bash
make stack-full
make monitoring-up
```
**Why:** Show all capabilities, live dashboards

### For CI/CD
**Use:** Core only
```bash
make stack-up
```
**Why:** Fast, deterministic, minimal dependencies

---

## ⚙️ Configuration

### Enable RAG in Backend
```bash
export ENABLE_RAG=1
export RAG_URL=http://127.0.0.1:8015
make stack-restart
```

### Enable Vision in Backend
```bash
export ENABLE_VISION=1
export FASTVLM_URL=http://127.0.0.1:8811
make stack-restart
```

### Quick Setup
```bash
# Source service URLs
source config/services.env

# Start what you need
make stack-full
```

---

## 🏆 Benefits

### Modular
- ✅ Start only what you need
- ✅ No bloat in core boot
- ✅ Layer on features as needed

### Fast
- ✅ Core: 2 seconds
- ✅ + Voice: 3 seconds total
- ✅ + RAG: 4 seconds total
- ✅ Full: 6 seconds total

### Flexible
- ✅ Development: Core only
- ✅ Testing: Core + Voice
- ✅ Demo: Full stack
- ✅ Production: Full + monitoring

---

## 🚨 Port Conflict Fix

**Weaviate port changed:**
- ❌ Old: 8090 (conflicted with Athena)
- ✅ New: 8095 (no conflicts)

**Update docker-compose.weaviate.yml if you have one:**
```yaml
ports:
  - "8095:8080"  # External 8095 → internal 8080
```

**Update all code referencing Weaviate:**
```python
# Old
weaviate_url = "http://127.0.0.1:8090"

# New
weaviate_url = os.getenv("WEAVIATE_URL", "http://127.0.0.1:8095")
```

---

**Status:** ✅ TIERED STACK COMPLETE
**Profiles:** 5 (core, voice, RAG, vision, full)
**Conflicts:** Fixed (Weaviate → 8095)

🎚️ **Choose your layer. Scale as needed.** 🚀
