# 🎯 Athena Quick Reference Card

**ONE-PAGE CHEAT SHEET FOR DAILY OPS**

---

## 🚀 Quick Start

```bash
athena                    # Interactive menu
make green                # Health check (2s)
make fastvlm-go-live      # Start full stack
```

---

## 📊 Service Endpoints

| Service | URL | Status Check |
|---------|-----|--------------|
| **Broker** | http://127.0.0.1:8080 | `curl http://127.0.0.1:8080/v1/health` |
| **Ollama** | http://localhost:11434 | `curl http://localhost:11434/api/tags` |
| **FastVLM** | http://127.0.0.1:8811 | `curl http://127.0.0.1:8811/health` |
| **Chat API** | http://localhost:8014 | `curl http://localhost:8014/health` |
| **Weaviate** | http://localhost:8090 | `curl http://localhost:8090/v1/.well-known/ready` |
| **Prometheus** | http://localhost:9090 | Open in browser |
| **Grafana** | http://localhost:3001 | admin/admin |

---

## 🎮 Common Commands

### **Vision:**
```bash
# Test FastVLM
curl -X POST http://127.0.0.1:8811/v1/vision \
  -F "image=@image.png" \
  -F 'prompt=Describe this.'

# Via helper script
python3 scripts/athena_vision.py image.png "What's this?" --report
```

### **Chat:**
```bash
# Quick Ollama test
curl http://localhost:11434/api/generate \
  -d '{"model":"mistral:7b","prompt":"Hello"}'
```

### **Provider Routing:**
```bash
# Test routing logic
python3 scripts/pick_provider.py

# Check health cache
python3 -c "
from scripts.pick_provider import HealthCache
cache = HealthCache()
print(cache.cache)
"
```

---

## 🔧 Service Control

### **Start/Stop:**
```bash
# Start all
make fastvlm-go-live

# Stop all
make down

# Restart FastVLM
launchctl kickstart gui/$(id -u)/com.athena.fastvlm

# Restart Broker
launchctl kickstart gui/$(id -u)/com.neuroforge.assistant-broker
```

### **View Logs:**
```bash
# FastVLM
tail -f /tmp/fastvlm_server.log

# Broker
tail -f ~/Library/Logs/AssistantBroker.out.log

# All services
make fastvlm-logs
```

---

## 🩹 Quick Fixes

### **Service Down:**
```bash
# Check what's running
make green

# Restart specific service
launchctl list | grep athena
launchctl kickstart gui/$(id -u)/com.athena.fastvlm
```

### **Vision Slow:**
```bash
# Warmup model
bash scripts/warmup_fastvlm.sh

# Check memory
top -l 1 | grep PhysMem
```

### **Port Conflict:**
```bash
# Find what's using port
lsof -i :8811

# Kill process
kill -9 <PID>
```

---

## 📂 Key Files

```
config/
  routing_policy.json       # Main routing config
  vision_providers.json     # Vision-specific config

scripts/
  pick_provider.py          # Provider selection logic
  persist_vision_to_weaviate.py  # Store vision results
  warmup_fastvlm.sh         # Boot-time warmup
  athena_vision.py          # Vision helper
  athena_menu.sh            # Interactive menu

~/Library/LaunchAgents/
  com.neuroforge.assistant-broker.plist  # Broker auto-start
  com.athena.fastvlm.plist              # FastVLM auto-start

~/.venvs/
  fastvlm311/               # Python 3.11 for FastVLM
```

---

## 🎯 Frontend Integration

### **Task Pattern (Swift):**
```swift
enum ChatTaskKind: String {
    case text
    case visionDescribe
    case reasoning
}

struct ChatTask: Encodable {
    let kind: ChatTaskKind
    let text: String?
    let imageBase64: String?
}

// Send to /api/chat - backend routes to correct provider
```

### **Response Handling:**
```swift
struct ChatResponse: Decodable {
    let text: String
    let latency_ms: Double
    let provider: String  // For debugging only
}
```

---

## 🔒 Circuit Breaker

- **Threshold:** 5 failures
- **Open Duration:** 30s
- **Half-Open:** Allow 1 test after 30s
- **Success to Close:** 2 consecutive successes

**Status:** `python3 scripts/pick_provider.py` shows circuit breaker state

---

## 📈 Performance Targets

| Metric | Target | Check |
|--------|--------|-------|
| Vision latency | <3s | `curl timing http://127.0.0.1:8811` |
| Chat latency | <200ms | Prometheus dashboard |
| Health check | <800ms | Provider picker output |
| Memory | <8GB | `top -l 1` |

---

## 🎊 Daily Workflow

```bash
# Morning: Check health
make green

# Use system
athena  # Interactive menu

# Evening: View stats
make daily-ops

# Tag stable
make validate-green && make tag-green
```

---

## 🆘 Emergency Commands

```bash
# PANIC - Stop everything
make down
# OR
bash ~/Desktop/"Panic Athena.command"

# Restart clean
make fastvlm-go-live
```

---

## 📞 Support

**Logs:**
- Broker: `~/Library/Logs/AssistantBroker.*.log`
- FastVLM: `/tmp/fastvlm_server.log`
- LaunchAgent: `/tmp/fastvlm.launchd.*`

**Docs:**
- `ATHENA_PRODUCTION_READY.md` - Full setup guide
- `COMPLETE_PRODUCTION_SETUP.md` - This session summary
- `README.md` - Workspace overview

---

**Quick Help:** Type `athena` → Option 1 for status
