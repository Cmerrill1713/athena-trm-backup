# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.9.6] - 2025-10-12

### Added
- **Operations Window** - Multi-tab dashboard (Traces/Health/Meta/Metrics)
  - Auto-open on low confidence (configurable threshold)
  - Service registry for all 10 services
  - One-click log viewer with live tail
  - Keyboard shortcut (Cmd+Option+O)
  - Settings UI for auto-open behavior

- **Log Security** - Production-grade log access
  - Bridge log proxy endpoint (`/ops/logs`)
  - Secret redaction (8+ patterns: Bearer, API keys, emails, etc.)
  - Max-tail guard (2000 lines enforced)
  - Service allowlist (prevents arbitrary file reads)
  - Timeout protection (5s max)
  - 12 unit tests for redaction
  - Security validation script
  - 5 Prometheus alerts

- **Platform Validation** - E2E smoke test
  - `VALIDATE_PLATFORM.sh` - Tests all services
  - CI matrix strategy (core/voice/rag profiles)
  - GitHub Actions workflow
  - Prevents silent service rot

- **Service Registry** - LEGO-simple integration
  - 10 services registered
  - Auto-discovery in ops window
  - Health monitoring with latency
  - Grouped by tier (core/voice/rag/vision/monitoring)

### Changed
- **Weaviate Port** - Moved from 8090 to 8095 (fixed conflict with Athena)
- **Tiered Stack** - Added optional layer targets
  - `make stack-voice` - Add Kokoro TTS
  - `make stack-rag` - Add RAG service
  - `make stack-vision` - Add FastVLM + Vision RAG
  - `make stack-full` - Start everything
- **CI Matrix** - Now tests multiple stack profiles
- **Root Directory** - Organized 160+ docs into `docs/` structure

### Fixed
- Port conflict between Weaviate and Athena
- Integration gaps (all services now have make targets)
- Secret leakage in log viewer
- Resource exhaustion (max tail limit)

### Security
- Secret redaction in all log responses
- Service allowlist prevents arbitrary file reads
- Timeout protection prevents hanging requests
- Prometheus alerts for security events
- 12 unit tests validate redaction patterns

---

## [v0.9.4-complete] - 2025-10-12

### Added
- **Tiered Stack** - 5 modular profiles
  - Core: Bridge + Athena + UAT (2s)
  - Voice: +Kokoro TTS
  - RAG: +RAG service  
  - Vision: +FastVLM + Vision RAG
  - Full: Everything (6s)

- **Meta UX** - Transparent AI
  - Confidence tracking (0-100%)
  - Sparkline visualization
  - Plan steps visible
  - Tool usage display
  - Debug overlay (Cmd+Shift+P)

- **Voice Control** - Complete system
  - CLI voice (50+ commands)
  - SwiftUI voice (Apple Speech + Kokoro TTS)
  - Natural voice responses
  - Voice meta-summary

- **Self-Improving Prompts** - Backend adaptation
  - Auto-rewrites on low confidence
  - RAG injection when needed
  - Reflection on vague prompts
  - Context chaining

### Changed
- Organized 160+ documentation files into `docs/` structure
- Root directory cleaned (3 essential docs only)
- Scripts organized (90+ in `scripts/`)
- Tests centralized (in `tests/`)

### Security
- `.env.template` created
- `.gitignore` updated (blocks .env files)
- Pre-commit hooks scan for secrets

---

## [v0.9.3-tier3-4] - 2025-10-11

### Added
- **Self-Healing Watchdog** - Autonomous recovery (8-23s MTTR)
- **Tier 4 Observability** - OpenTelemetry, rate limiting, graceful shutdown
- **Pre-Push Quality Gate** - Athena validates before push
- **Forensic Debugging** - `make truth` for reality checks
- **Voice Control** - athena_voice.sh with 50+ commands

---

## [Earlier Versions]

See `docs/changelog/` for complete version history.

---

**Current Version:** v0.9.6  
**Latest Tag:** v0.9.6  
**Status:** Production-Ready

