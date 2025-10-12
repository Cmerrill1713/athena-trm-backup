# 🚀 NeuroForge - Voice-Controlled Autonomous AI Infrastructure

> **Production-grade AI stack with self-healing, observability, and voice control**

---

## ⚡ Quick Start (5 Minutes)

```bash
# Start the complete stack
make stack-up

# Verify health
make truth

# Run tests via Athena
make athena-tests

# Enable self-healing autopilot
make watchdog-start
```

**That's it!** Your autonomous infrastructure is running.

---

## 🎯 What You Have

### Complete AI Stack
- **Athena AI** - Autonomous agent with tool calls (port 8090)
- **UAT** - Universal AI Tools orchestrator (port 8181)  
- **Bridge** - FastAPI adapter with Tier 4 observability (port 8014)
- **Kokoro TTS** - Natural voice synthesis (port 8020)
- **NeuroForgeApp** - SwiftUI macOS chat interface

### Production Features
- 🗣️ **Voice Control** - CLI and SwiftUI voice interfaces
- 🧠 **Meta-Awareness** - See AI confidence and thinking
- 📊 **Full Observability** - OpenTelemetry, Prometheus, Grafana
- 🤖 **Self-Healing** - Watchdog autopilot (8-23s MTTR)
- 🛡️ **Quality Gates** - Pre-push validation
- 🔍 **Forensic Debugging** - Truth checks, PID tracking

---

## 📚 Documentation

**See:** [`START_HERE.md`](START_HERE.md) for quick start  
**See:** [`docs/INDEX.md`](docs/INDEX.md) for full navigation

### Quick Links
- 🚀 [Launch Procedures](docs/launch/) - Deployment guides
- 🔧 [Operations](docs/operations/) - Day 2 ops, monitoring
- 📖 [Guides](docs/guides/) - How-to guides
- ⚡ [Reference](docs/reference/) - Quick command cards
- 🧠 [Athena Docs](docs/athena/) - AI system documentation

---

## 🎙️ Voice Control

### CLI Voice (Backend Ops)
```bash
./athena_voice.sh

# Say:
"bring everything online"   → Starts stack
"run smoke tests"           → Runs tests
"ghost check"               → Forensic scan
"enable watchdog"           → Self-healing on
"ship it"                   → Deploy canary
```

**50+ commands** - See [`athena_voice_map.json`](athena_voice_map.json)

### SwiftUI Voice (Chat Interface)
- Click mic in NeuroForgeApp
- Speak naturally to Athena
- Hear responses with Kokoro TTS
- See confidence and thinking process

---

## 🚀 Common Commands

### Stack Management
```bash
make stack-up           # Start everything
make stack-down         # Stop everything
make stack-restart      # Restart cleanly
make stack-status       # Health check
make truth              # Reality check (PIDs, ports)
```

### Testing
```bash
make athena-tests       # Run all tests
make athena-tests-smoke # Smoke tests only
make tier4-proof        # Full observability proof
```

### Self-Healing
```bash
make watchdog-start     # Enable autopilot
make watchdog-status    # Check status
make auto-heal-test     # Test recovery
```

### Debugging
```bash
make nuke-ports         # Kill ghosts
make stack-validate     # Full validation
```

**Full reference:** [`docs/reference/`](docs/reference/)

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  NeuroForgeApp (SwiftUI)        │
│  • Voice chat interface         │
│  • Meta-awareness UI            │
│  • Confidence tracking          │
└──────────┬──────────────────────┘
           │ :8014
┌──────────┴──────────────────────┐
│  Bridge (FastAPI)               │
│  • Tier 4 observability         │
│  • Rate limiting                │
│  • Graceful shutdown            │
│  • Self-identification          │
└──────┬────────┬─────────────────┘
       │        │
       ▼        ▼
    ┌────┐  ┌────────┐
    │UAT │  │ Athena │
    │8181│  │  8090  │
    └────┘  └────────┘
       │        │
       └────┬───┘
            ▼
    ┌───────────────┐
    │  Kokoro TTS   │
    │     8020      │
    └───────────────┘
```

---

## 🔧 Development

### Work on Backend
```bash
cd AI-Projects/universal-ai-tools
make test
make lint
```

### Work on Frontend
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

### Deploy Changes
```bash
git commit -am "feature"
git push
# Pre-push gate validates automatically
```

---

## 🧠 Key Features

### 1. Transparent AI
- See Athena's confidence level (0-100%)
- View her thinking process (plan steps)
- Watch tools being used
- Understand reasoning (RAG, Reflection, Chaining)

### 2. Self-Healing
- Watchdog monitors health 24/7
- Auto-detects issues (ghosts, crashes)
- Recovers automatically (8-23s MTTR)
- Sends notifications (Slack/Telegram)

### 3. Voice Control
- CLI commands for operations
- Natural language in SwiftUI app
- Kokoro TTS for responses
- Speech recognition for input

### 4. Production Observability
- OpenTelemetry tracing
- Prometheus metrics
- Grafana dashboards
- Health endpoints (/live, /ready)
- Rate limiting and guardrails

---

## 📊 Stats

- **Services:** 5 (Bridge, Athena, UAT, Kokoro, Frontend)
- **Startup Time:** ~2 seconds
- **MTTR:** 8-23 seconds (self-healing)
- **Test Coverage:** Full e2e validation
- **Documentation:** 160+ guides
- **Scripts:** 90+ automation tools
- **Voice Commands:** 50+

---

## 🛠️ Troubleshooting

### Quick Fixes
```bash
# Ghosts (multiple PIDs)
make nuke-ports && make stack-up

# No voice
python3 scripts/kokoro_server.py

# Meta panels missing
export META_PROMPTING=1 && make stack-restart

# Full reset
make stack-down && make nuke-ports && make stack-up
```

**See:** [`docs/guides/`](docs/guides/) for detailed troubleshooting

---

## 📝 Recent Updates

**October 12, 2025:**
- ✅ Meta UX integrated (confidence tracking, sparklines)
- ✅ Voice control for frontend and backend
- ✅ Kokoro TTS integration
- ✅ Prompt engineering visibility
- ✅ Root directory cleanup (100+ files organized)
- ✅ Complete documentation structure

**See:** [`docs/changelog/`](docs/changelog/) for version history

---

## 🚀 Next Steps

### First Time
1. Read [`START_HERE.md`](START_HERE.md)
2. Run `make stack-up`
3. Try voice: `./athena_voice.sh`
4. Launch app: `cd NeuroForgeApp && swift run`

### Operations
- See [`docs/operations/`](docs/operations/)
- Enable watchdog: `make watchdog-start`
- Monitor: [`docs/tier4/`](docs/tier4/)

### Development
- See [`docs/guides/`](docs/guides/)
- Check [`docs/reference/`](docs/reference/)

---

## 🏆 What This Is

**An autonomous, voice-controlled AI infrastructure** that:
- Learns from every conversation
- Heals itself automatically  
- Shows its thinking process
- Speaks with confidence
- Gates itself with quality checks
- Provides complete visibility

**Built for production. Ready to scale.**

---

**Version:** v0.9.4-meta-ux  
**Status:** ✅ Production-Ready  
**Updated:** October 12, 2025  
**Maintained By:** Christian Merrill

🎙️ **Talk to your infrastructure. It listens.** 🚀
