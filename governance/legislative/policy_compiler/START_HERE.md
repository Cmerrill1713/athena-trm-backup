# 🚀 Start Here - NeuroForge Stack

> **Your voice-controlled, self-healing, autonomous AI infrastructure**

---

## ⚡ Quick Start (5 minutes)

```bash
# 1. Start the stack
make stack-up

# 2. Verify
make truth

# 3. Run tests
make athena-tests
```

**That's it!** Your autonomous infrastructure is running.

---

## 📚 Documentation

**All docs organized in:** [`docs/`](docs/)

### I want to:
- 🚀 **Deploy the system** → [docs/launch/](docs/launch/)
- 🔧 **Operate the system** → [docs/operations/](docs/operations/)
- 🧠 **Understand Athena** → [docs/athena/](docs/athena/)
- 📊 **Monitor the system** → [docs/tier4/](docs/tier4/)
- 🛠️ **Troubleshoot** → [docs/guides/](docs/guides/)
- ⚡ **Quick commands** → [docs/reference/](docs/reference/)

**Full index:** [docs/INDEX.md](docs/INDEX.md)

---

## 🎯 What You Have

### Complete System
- **Backend:** UAT + Athena + Bridge (ports 8181, 8090, 8014)
- **Voice:** CLI ops control + SwiftUI chat interface
- **TTS:** Kokoro natural voice (port 8020)
- **Observability:** OpenTelemetry, Prometheus, Grafana
- **Self-Healing:** Watchdog autopilot (8-23s MTTR)
- **Quality Gates:** Pre-push validation

### Key Features
- 🗣️ Voice-controlled operations
- 🧠 Transparent AI (see confidence & thinking)
- 📊 Real-time confidence tracking
- 🔍 Prompt engineering visibility
- 🤖 Autonomous recovery
- 🛡️ Production-grade guardrails

---

## 🚀 Common Commands

```bash
# Stack management
make stack-up           # Start everything
make stack-down         # Stop everything
make stack-restart      # Restart cleanly
make stack-status       # Health check
make truth              # Reality check (PIDs, ports)

# Testing
make athena-tests       # Run all tests
make athena-tests-smoke # Smoke tests only
make tier4-proof        # Full observability proof

# Self-healing
make watchdog-start     # Enable autopilot
make watchdog-status    # Check watchdog
make auto-heal-test     # Test recovery

# Voice control
./athena_voice.sh       # CLI voice interface
athena "run tests"      # Natural language commands

# Debugging
make nuke-ports         # Kill ghosts
make stack-validate     # Full validation
```

---

## 🎙️ Voice Commands

```bash
# CLI voice (backend ops)
athena "bring everything online"
athena "run smoke tests"
athena "ghost check"
athena "enable watchdog"
athena "ship it"

# SwiftUI voice (chat interface)
# Click mic in app → speak naturally
```

---

## 📖 Documentation Structure

```
docs/
├── INDEX.md           # Full navigation
├── launch/            # Deployment & launch
├── operations/        # Day 2 operations
├── guides/            # How-to guides
├── reference/         # Quick references
├── athena/            # Athena AI docs
├── fastvlm/           # FastVLM integration
├── tier4/             # Observability
├── complete/          # Status tracking
└── archive/           # Legacy docs
```

---

## 🛠️ Troubleshooting

**Quick fixes:**
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

**See:** [docs/guides/](docs/guides/) for detailed troubleshooting

---

## 🎯 Next Steps

### First Time Setup
1. Run `make stack-up`
2. Run `make truth` to verify
3. Try voice: `./athena_voice.sh`
4. Enable watchdog: `make watchdog-start`

### For Development
- See [docs/guides/](docs/guides/)
- Check [docs/reference/](docs/reference/)

### For Operations
- See [docs/operations/](docs/operations/)
- Monitor: [docs/tier4/](docs/tier4/)

### For Deployment
- See [docs/launch/](docs/launch/)

---

## 🏆 What This Is

**An autonomous, voice-controlled AI infrastructure** that:
- Learns from every conversation
- Heals itself automatically
- Shows its thinking process
- Speaks with confidence
- Gates itself with quality checks
- Provides complete visibility

**Built with:**
- SwiftUI (frontend)
- FastAPI (backend)
- Kokoro TTS (voice)
- OpenTelemetry (observability)
- Self-healing watchdog
- Complete automation

---

## 📞 Need Help?

1. Check [docs/INDEX.md](docs/INDEX.md)
2. Look in [docs/guides/](docs/guides/)
3. Try [docs/reference/](docs/reference/)
4. See [docs/operations/](docs/operations/)

---

**Status:** ✅ Production-Ready  
**Version:** v0.9.4-meta-ux  
**Quality:** ⭐⭐⭐⭐⭐

🚀 **Let's go!**
