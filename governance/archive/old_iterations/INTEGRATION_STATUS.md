# 🔍 Integration Status - All Systems

> **What's wired vs what's optional**

---

## ✅ CORE STACK (Auto-Started with `make stack-up`)

### These Start Automatically:
1. **UAT** - port 8181 ✅ Wired
   - Universal AI Tools orchestrator
   - Started: `make stack-up`

2. **Athena** - port 8090 ✅ Wired
   - AI agent with tool calls
   - Started: `make stack-up`

3. **Bridge** - port 8014 ✅ Wired
   - FastAPI adapter with Tier 4
   - Started: `make stack-up`

4. **Watchdog** ✅ Wired (optional enable)
   - Self-healing autopilot
   - Started: `make watchdog-start`

---

## 🔧 TIER 4 OBSERVABILITY (Optional)

### These Need Manual Start:
1. **OpenTelemetry Collector** - port 4318 ⚠️ Optional
   - Trace collection
   - Start: `make otel-up`
   - Stop: `make otel-down`

2. **Prometheus** - port 9090 ⚠️ Optional
   - Metrics collection
   - Start: `make monitoring-up`
   - Access: http://localhost:9090

3. **Grafana** - port 3001 ⚠️ Optional
   - Metrics dashboards
   - Started with: `make monitoring-up`
   - Access: http://localhost:3001

---

## 🎤 VOICE SYSTEMS (Ready)

### These Are Ready:
1. **Kokoro TTS** - port 8020 ⚠️ Manual/LaunchAgent
   - Natural voice synthesis
   - Start: `python3 scripts/kokoro_server.py`
   - Or: Auto-start with LaunchAgent
   - Status: ✅ **Wired in VoiceManager.swift**

2. **CLI Voice Control** ✅ Ready
   - Backend ops commands
   - Start: `./athena_voice.sh`
   - Commands: 50+ in `athena_voice_map.json`

3. **SwiftUI Voice** ✅ Ready
   - Chat interface voice
   - Built into NeuroForgeApp
   - Uses: Apple Speech + Kokoro

---

## 👁️ VISION SYSTEMS (Optional Services)

### These Need Manual Start:
1. **FastVLM** - port 8811 ⚠️ Not in stack-up
   - Vision-language model
   - Setup: `make fastvlm-setup` (one-time)
   - Start: `make fastvlm-server`
   - Or: `make fastvlm-autostart` (watchdog)
   - Status: **Standalone service**

2. **Vision RAG** - port 8016 ⚠️ Not in stack-up
   - Image analysis + citations
   - Start: Manual python script
   - Depends on: FastVLM OR Ollama
   - Status: **Standalone service**

3. **RAG Service** - port 8015 ⚠️ Not in stack-up
   - Knowledge base search
   - Start: Manual python script
   - Depends on: Weaviate
   - Status: **Standalone service**

4. **Weaviate** - port 8090 ⚠️ Conflict!
   - Vector database
   - Start: `make weaviate-up` (Docker)
   - **ISSUE:** Port 8090 conflicts with Athena!
   - Status: **Port conflict - needs different port**

---

## 🤖 OTHER SYSTEMS (Standalone)

### Not Integrated into Main Stack:
1. **agents/** - Agent system ⚠️ Standalone
   - Multi-agent orchestration
   - Status: Separate Python package
   - **Could integrate** if needed

2. **AthenaReporter** - Swift app ⚠️ Standalone
   - Voice + visual reports
   - Status: Separate macOS app
   - **Independent** - opens via athena:// URL scheme

3. **assistant-broker** - port 8080 ⚠️ Standalone
   - macOS app control API
   - Start: `make broker`
   - Status: Optional utility service

4. **TinyRecursiveModels** ⚠️ Standalone
   - TRM training pipeline
   - Status: Training/eval only
   - **Not a service** - runs on demand

5. **pydantic-ai** ⚠️ Library
   - Framework dependency
   - Status: Library, not a service

---

## ⚠️ ISSUES FOUND

### 1. Port Conflict: Weaviate vs Athena
```
Athena:   port 8090  ✅ Core stack
Weaviate: port 8090  ❌ CONFLICT!
```

**Fix needed:**
- Either change Weaviate port (recommended: 8095)
- Or wire Weaviate into stack properly

### 2. Vision Services Not in Core Stack
```
FastVLM:      port 8811  ⚠️ Manual start required
Vision RAG:   port 8016  ⚠️ Manual start required
RAG Service:  port 8015  ⚠️ Manual start required
```

**Options:**
a) Add to `stack-up` for all-in-one
b) Keep separate (optional services)
c) Create `make stack-full` with all services

### 3. Monitoring Optional
```
Prometheus: port 9090  ⚠️ Separate make target
Grafana:    port 3001  ⚠️ Separate make target
```

**Status:** Working as designed (optional)

---

## 🎯 RECOMMENDATIONS

### Option A: Keep Current (Minimal Core)
```bash
make stack-up         # UAT + Athena + Bridge only
make otel-up          # Add observability if needed
make monitoring-up    # Add dashboards if needed
make fastvlm-server   # Add vision if needed
```

**Pros:** Fast startup, minimal resources
**Cons:** Manual steps for full features

### Option B: Create Extended Stack
```bash
make stack-full       # All services including vision + RAG
```

Would start:
- ✅ UAT, Athena, Bridge (core)
- ✅ Kokoro TTS
- ✅ FastVLM
- ✅ RAG Service
- ✅ Vision RAG
- ✅ Weaviate (different port)
- ✅ OpenTelemetry
- ⚠️ Optional: Prometheus + Grafana

**Pros:** One command for everything
**Cons:** Slower startup, more resources

### Option C: Tiered Start
```bash
make stack-up         # Core: UAT + Athena + Bridge
make stack-voice      # Add: Kokoro TTS
make stack-vision     # Add: FastVLM + Vision RAG
make stack-monitor    # Add: OTLP + Prometheus + Grafana
```

**Pros:** Modular, choose what you need
**Cons:** Multiple commands

---

## 🛠️ QUICK FIXES

### Fix Weaviate Port Conflict
```bash
# In docker-compose or Weaviate config, change port to 8095
# Then can run alongside Athena
```

### Add Kokoro to Stack
```bash
# Could add to stack-up:
@python3 scripts/kokoro_server.py > logs/kokoro_8020.log 2>&1 & echo $$! > .stack/kokoro.pid
```

### Add Vision to Stack
```bash
# Could add to stack-up:
@make fastvlm-server > logs/fastvlm_8811.log 2>&1 &
```

---

## 📋 WHAT'S MISSING FROM INTEGRATION

### Services with Make Targets But Not in Stack:
1. ❌ FastVLM (vision) - has targets, not auto-started
2. ❌ RAG Service - has code, not auto-started
3. ❌ Vision RAG - has code, not auto-started
4. ❌ Weaviate - **PORT CONFLICT with Athena**
5. ❌ Prometheus/Grafana - intentionally separate
6. ❌ Kokoro TTS - manual or LaunchAgent only

### Services Without Integration:
1. ❓ agents/ - standalone Python package
2. ❓ assistant-broker - standalone utility
3. ❓ TinyRecursiveModels - training only, not a service

---

## 🎯 YOUR DECISION

**Which do you want?**

1. **Keep minimal** - Current stack-up is fine (UAT + Athena + Bridge)
2. **Create stack-full** - Add all services to one command
3. **Create tiered** - stack-up, stack-voice, stack-vision, stack-monitor
4. **Fix Weaviate** - Change port so it doesn't conflict with Athena

**Or tell me what you want wired up and I'll do it!**

---

**Current Status:**
- ✅ Core stack works (3 services)
- ✅ Voice works (Kokoro optional)
- ⚠️ Vision requires manual start
- ⚠️ RAG requires manual start
- ⚠️ Weaviate has port conflict
- ⚠️ Monitoring separate (by design)

**Question:** Should we wire more into the main stack?
