# 🔍 Platform Validation Guide

> **10-minute E2E smoke test for all systems**

---

## ✅ What It Tests

### Core Services
- Bridge :8014
- Athena :8090
- UAT :8181

### Meta Features
- Meta headers present
- Confidence scores returned
- Prompt style indicators

### Voice System
- Kokoro TTS health
- Audio generation
- WAV output quality

### RAG Layer
- RAG service :8015
- Knowledge search
- Health endpoints

### Vision Layer
- FastVLM :8811
- Vision RAG :8016
- Health checks

### Infrastructure
- Weaviate :8095 (port fix verified!)
- Prometheus :9090
- Grafana :3001

### Meta Behavior
- Low confidence prompts ("logs?")
- Medium confidence prompts ("backend errors")
- High confidence prompts ("run smoke tests")

---

## 🚀 Quick Start

```bash
cd /Users/christianmerrill/Documents/GitHub
chmod +x VALIDATE_PLATFORM.sh
./VALIDATE_PLATFORM.sh
```

**Expected time:** 1-2 minutes

---

## 📊 What "Good" Looks Like

### All Core Services Pass
```
✅ Bridge ready (http://127.0.0.1:8014/ready)
✅ Athena ready (http://127.0.0.1:8090/ready)
✅ UAT ready (http://127.0.0.1:8181/ready)
```

### Chat Works with Meta
```
✅ Chat response has content (245 chars)
✅ Meta headers present (confidence: 0.85)
```

### Optional Services Show Status
```
✅ Kokoro TTS produced audio (342044 bytes)
⚠️  RAG service not up at :8015 (start: make stack-rag)
⚠️  FastVLM not up at :8811 (start: make stack-vision)
```

### Weaviate on Correct Port
```
✅ Weaviate ready on :8095 (port conflict fixed!)
```

### Meta Confidence Evolution
```
• logs?                                      conf=0.18   style=direct
• backend errors last 5 minutes              conf=0.76   style=reasoned
• run smoke tests and summarize failures     conf=0.92   style=reasoned
```

---

## 🎯 Usage Patterns

### Daily Development
```bash
# Start core + voice
make stack-up && make stack-voice

# Validate
./VALIDATE_PLATFORM.sh

# Expect: Core ✅, Voice ✅, Others ⚠️ (not started)
```

### Full Feature Testing
```bash
# Start everything
make stack-full

# Validate
./VALIDATE_PLATFORM.sh

# Expect: All ✅
```

### CI/CD
```bash
# Minimal stack
make stack-up

# Validate core only
./VALIDATE_PLATFORM.sh

# Expect: Core ✅, Others ⚠️ (OK in CI)
```

---

## 🛠️ Troubleshooting

### Core Service Fails
```bash
# Check what's running
make truth

# Nuke ghosts and restart
make nuke-ports
make stack-up
```

### Meta Headers Missing
```bash
# Ensure meta enabled
export META_PROMPTING=1
export META_REFLECTION=1
export META_RAG=1
make stack-restart
```

### Voice Service Fails
```bash
# Check Kokoro
curl http://127.0.0.1:8020/health

# Start if needed
make stack-voice

# Or manually
python3 scripts/kokoro_server.py
```

### Weaviate on Wrong Port
```bash
# Verify not on 8090 (conflict!)
lsof -ti:8090

# Should only show Athena PID
# If Weaviate there, stop it and restart on 8095
```

---

## 📋 Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All critical checks passed | ✅ Good to go |
| 1 | Core service failed | Fix core stack |
| Non-zero | Validation error | Check output |

**Warnings (⚠️) don't fail the script** - they indicate optional services not running.

---

## 🧪 Adding to CI

### GitHub Actions Example
```yaml
# .github/workflows/smoke.yml
name: Platform Validation
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl
      
      - name: Start core stack
        run: |
          export META_PROMPTING=1
          make stack-up
          sleep 5
      
      - name: Validate platform
        run: |
          chmod +x VALIDATE_PLATFORM.sh
          ./VALIDATE_PLATFORM.sh
```

---

## 📊 Validation Matrix

| Test | Required | Optional | Skip |
|------|----------|----------|------|
| Core services | ✅ | | |
| Chat endpoint | ✅ | | |
| Meta headers | | ✅ | If META_PROMPTING=0 |
| Kokoro TTS | | ✅ | If voice not needed |
| RAG service | | ✅ | If RAG not started |
| Vision services | | ✅ | If vision not started |
| Weaviate | | ✅ | If not using vectors |
| Monitoring | | ✅ | If not monitoring |

---

## 🔍 What Gets Checked

### Health Endpoints
- `/ready` on all core services
- `/health` on Bridge, Athena, UAT
- `/health` on optional services

### Functional Tests
- Chat produces valid JSON
- Content is non-empty
- Meta headers surfaced (if enabled)
- TTS produces audio bytes
- Confidence varies by prompt complexity

### Port Conflicts
- Weaviate NOT on 8090 (Athena's port)
- Weaviate IS on 8095 (fixed port)
- No duplicate processes per port

### Integration Points
- Bridge can reach Athena
- Bridge can reach UAT
- Frontend can reach Bridge
- Services return expected JSON

---

## 🎯 Post-Validation

### All Pass
```
✅ Ship it!
✅ Tests will pass
✅ Pre-push gate will allow push
```

### Core Pass, Optional Warn
```
✅ Core functional
⚠️  Optional features available if needed
✅ Ready for development
```

### Core Fail
```
❌ Fix core stack first
→ make nuke-ports && make stack-up
→ make truth
```

---

## 📚 Related Docs

- `docs/STACK_PROFILES.md` - Stack startup profiles
- `docs/operations/` - Operations guides
- `START_HERE.md` - Quick start
- `docs/launch/` - Deployment procedures

---

**Script:** `/Users/christianmerrill/Documents/GitHub/VALIDATE_PLATFORM.sh`  
**Runtime:** 1-2 minutes  
**Dependencies:** curl, jq, awk, grep, sed

🔍 **One command to validate everything!** ✅

