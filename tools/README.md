# Athena Platform Tools

Voice-driven orchestration tools for NeuroForge platform (RAG, Vision, Kokoro).

## 🚀 Quick Start

### 1. Register Tools with Athena

```bash
# Option A: Auto-register (API or file)
python3 register_with_athena.py

# Option B: Manual link
ln -s $(pwd) ~/.athena/tools/neuroforge
```

### 2. Test CLI

```bash
# Probe all services
./probe_services.sh

# Start full stack
./stack_full.sh

# Query RAG
./rag_query.sh "neuroforge"
```

### 3. Use with Voice

Say to Athena:
- **"Bring everything online"** → `stack_full.sh`
- **"Probe services"** → `probe_services.sh`
- **"What's running?"** → `whats_running.sh`
- **"Validate platform"** → `validate_platform.sh`
- **"Ship it"** → `ship_it.sh` (gated)

## 📦 Available Tools

| Tool | Intent | Purpose |
|------|--------|---------|
| `stack_full.sh` | "bring everything online" | Start all services |
| `stack_core.sh` | "bring core online" | Core services only |
| `stack_voice.sh` | "enable voice" | Start Kokoro TTS |
| `stack_rag.sh` | "enable rag" | Start RAG service |
| `stack_vision.sh` | "enable vision" | Start vision services |
| `probe_services.sh` | "probe services" | Quick health check |
| `whats_running.sh` | "what's running" | Service status |
| `validate_platform.sh` | "validate platform" | E2E validation |
| `ship_it.sh` | "ship it" | Gated deployment |
| `rag_query.sh` | "query rag about X" | Search knowledge |

## 📋 Manifest

`athena_tools.yaml` contains:
- 15 tool definitions
- Intent patterns
- Timeouts and gates
- Environment configuration
- Success criteria

## 🔧 Configuration

Edit `athena_tools.yaml` to:
- Add new tools
- Modify intent patterns
- Adjust timeouts
- Add gates/validation

## 🧪 Testing

```bash
# Test individual tool
./probe_services.sh

# Test with parameters
./rag_query.sh "swift ui app"

# Test gated ship
./ship_it.sh
```

## 📚 Documentation

- `ATHENA_INTEGRATION.md` - Full integration guide
- `athena_tools.yaml` - Tool manifest
- `register_with_athena.py` - Auto-registration

## 🎯 Success Criteria

Tools validate:
- ✅ All services respond
- ✅ Meta headers present
- ✅ No timeouts
- ✅ Confidence thresholds met (for ship)

## 📞 Support

```bash
# List tools
ls -l *.sh

# Check manifest
cat athena_tools.yaml

# Test tool manually
./probe_services.sh
```

---

**Status**: ✅ Ready for Athena integration  
**Services**: Bridge, Athena, UAT, Kokoro, RAG, Vision  
**Control**: Voice, CLI, API

