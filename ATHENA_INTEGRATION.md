# 🧠 Athena Integration - Voice-Driven Platform Orchestration

**Status**: ✅ Ready to integrate  
**Services**: RAG, Vision, Kokoro wired into Athena  
**Control**: Voice, CLI, or API

---

## 🎯 What This Does

Integrates RAG, Vision, and Kokoro services into your Athena orchestration system so you can control the entire platform by voice or natural language.

**Examples**:
- 🗣️ **"Bring everything online"** → Starts full stack
- 🗣️ **"Validate platform"** → Runs end-to-end tests
- 🗣️ **"What's running?"** → Shows service status
- 🗣️ **"Query RAG about NeuroForge"** → Searches knowledge base
- 🗣️ **"Ship it"** → Deploys (gated by validation)

---

## 📦 What Was Created

### 1. Tool Manifest (`tools/athena_tools.yaml`)
- 15 tools mapped to intents
- Environment configuration
- Success criteria per tool
- Gates for critical operations

### 2. Bash Wrappers (`tools/*.sh`)
```
tools/
├── stack_full.sh          # Start complete stack
├── stack_core.sh          # Core services only
├── stack_voice.sh         # Enable Kokoro
├── stack_rag.sh           # Enable RAG
├── stack_vision.sh        # Enable Vision
├── probe_services.sh      # Quick health check
├── whats_running.sh       # Service status
├── validate_platform.sh   # E2E validation
├── ship_it.sh             # Gated deployment
└── rag_query.sh           # Direct RAG query
```

### 3. Integration Layer
- Intent patterns for each tool
- Timeouts and gates
- Confirmation for destructive ops
- Meta-prompt awareness

---

## 🔌 Integration Methods

### Method 1: Direct Registration (Recommended)

If your Athena reads from a tools directory:

```bash
# Link tools into Athena's tool directory
ln -s /Users/christianmerrill/Documents/GitHub/tools ~/.athena/tools/neuroforge

# Or copy the manifest
cp tools/athena_tools.yaml ~/.athena/config/tools/neuroforge.yaml
```

Then restart Athena:
```bash
cd athena && python restart.py
```

### Method 2: Python Integration

Add to your Athena tool loader (`athena/tools/loader.py` or similar):

```python
import yaml
from pathlib import Path

def load_neuroforge_tools():
    manifest_path = Path("/Users/christianmerrill/Documents/GitHub/tools/athena_tools.yaml")
    with open(manifest_path) as f:
        tools = yaml.safe_load(f)
    
    for tool in tools['tools']:
        register_tool(
            name=tool['name'],
            cmd=tool['cmd'],
            intents=tool['intent_patterns'],
            working_dir=tool.get('working_dir', '.'),
            timeout=tool.get('timeout', 30)
        )
    
    return tools['tools']
```

### Method 3: API Registration

POST to Athena's tool registration endpoint:

```bash
curl -X POST http://127.0.0.1:8090/api/tools/register \
  -H 'Content-Type: application/json' \
  -d @tools/athena_tools.yaml
```

---

## 🗣️ Voice Commands → Actions

| Say This | Athena Runs | Result |
|----------|-------------|--------|
| "Bring everything online" | `make stack-full && make truth` | Full stack up |
| "Bring core online" | `make stack-up && make truth` | Core services only |
| "Enable voice" | `make stack-voice && make truth` | Kokoro TTS ready |
| "Enable RAG" | `make stack-rag && make truth` | RAG service started |
| "Enable vision" | `make stack-vision && make truth` | Vision services started |
| "Validate platform" | `./VALIDATE_PLATFORM.sh` | E2E validation |
| "Probe services" | `./NeuroForgeApp/scripts/validate_services.sh` | Quick health check |
| "What's running?" | `make stack-status-full` | Service status |
| "Query RAG about X" | `./tools/rag_query.sh "X"` | Search knowledge base |
| "Ship it" | `./tools/ship_it.sh` | Deploy (gated) |

---

## 🧪 Test Integration

### 1. Test Individual Tools (CLI)

```bash
cd /Users/christianmerrill/Documents/GitHub

# Test stack full
./tools/stack_full.sh

# Test validation
./tools/validate_platform.sh

# Test RAG query
./tools/rag_query.sh "neuroforge swift app"

# Test service probe
./tools/probe_services.sh
```

### 2. Test Via Athena API

```bash
# Assuming Athena exposes a /execute endpoint
curl -X POST http://127.0.0.1:8090/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "bring everything online",
    "context": {}
  }'
```

### 3. Test Via Voice

In your app with voice enabled:
1. Hold Space
2. Say: "Athena, bring everything online"
3. Release
4. Athena should execute `make stack-full && make truth`

---

## 🔐 Environment Variables

Tools automatically inherit these (set in manifest):

```bash
API_BASE=http://127.0.0.1:8014
META_PROMPTING=1
META_REFLECTION=1
META_RAG=1
META_SELFCRITIQUE=1
FEATURE_RAG=1
FEATURE_VISION=1
FEATURE_VOICE=1
FEATURE_HEALTH_PROBE=1
META_CONFIDENCE_FLOOR=0.75
```

---

## 🎛️ Tool Details

### Stack Management

#### `stack_full`
**Intent**: "bring everything online"  
**Does**: Starts Bridge, Athena, UAT, Kokoro, RAG, Vision  
**Timeout**: 60s  
**Validates**: All services respond

#### `stack_core`
**Intent**: "bring core online"  
**Does**: Starts Bridge, Athena, UAT only  
**Timeout**: 30s

#### `stack_voice` / `stack_rag` / `stack_vision`
**Intent**: "enable {service}"  
**Does**: Starts specific service layer  
**Timeout**: 15-20s

### Validation & Testing

#### `validate_platform`
**Intent**: "validate platform"  
**Does**: End-to-end health + smoke tests  
**Timeout**: 45s  
**Gates**: None (but used to gate ship)

#### `probe_services`
**Intent**: "probe services" / "health check"  
**Does**: Quick HEAD requests to all services  
**Timeout**: 10s  
**Output**: ✅/⚠️ per service

### Deployment

#### `ship_it`
**Intent**: "ship it" / "deploy"  
**Does**: Validates then deploys  
**Timeout**: 90s  
**Gates**:
1. Platform validation must pass
2. Optional confidence threshold

**Confidence Gate**:
```bash
# If META_CONFIDENCE_FLOOR=0.75 is set
# Athena checks last meta response confidence
# Blocks ship if confidence < 0.75
```

---

## 🧠 Meta-Prompt Awareness

Athena already returns meta headers. Tools leverage this:

### Confidence-Based Decisions

```yaml
# In ship_it tool
gates:
  - cmd: "./VALIDATE_PLATFORM.sh"
    must_pass: true
  - cmd: "test $META_CONFIDENCE_FLOOR && echo 'OK'"
    must_pass: false  # Optional
```

When Athena processes "ship it":
1. Runs validation
2. Checks confidence from last response
3. If confidence < floor, suggests improvements
4. Returns plan in meta headers

### Example Meta Response

```json
{
  "message": "Ship blocked - confidence too low",
  "meta": {
    "confidence": 0.65,
    "plan": [
      "Run additional validation",
      "Check RAG service health",
      "Retry with higher confidence"
    ],
    "tools": ["validate_platform", "probe_services"],
    "reflection": true
  }
}
```

---

## 🔄 Workflow Examples

### Full System Bring-Up

```
User: "Bring everything online"
  ↓
Athena: Executes stack_full.sh
  ↓
  make stack-full && make truth
  ↓
Services start: Bridge :8014, Athena :8090, UAT :8181,
                Kokoro :8020, RAG :8015, Vision :8016
  ↓
Athena: "✅ All services operational. 6/6 up."
```

### Gated Ship

```
User: "Ship it"
  ↓
Athena: Executes ship_it.sh
  ↓
Gate 1: ./VALIDATE_PLATFORM.sh
  ↓
  (validation passes)
  ↓
Gate 2: Check confidence
  ↓
  (confidence = 0.82 > 0.75)
  ↓
  ./GO_LIVE_NOW.sh
  ↓
Athena: "✅ Ship complete. Version v0.9.5 deployed."
```

### Query with Context

```
User: "Query RAG about Swift UI integration"
  ↓
Athena: Executes rag_query.sh "Swift UI integration"
  ↓
  curl POST 127.0.0.1:8015/api/rag/query
  ↓
  Returns 5 hits from 170 transcripts
  ↓
Athena: "Found 5 results about Swift UI:
         1. Building Swift UI Apps with...
         2. SwiftUI State Management..."
```

---

## 🚧 Advanced: Custom Intent Processing

If you want Athena to extract parameters from natural language:

```python
# In your Athena intent processor

def process_rag_query(intent_text):
    # Extract query from "query rag about X"
    match = re.search(r'query rag about (.+)', intent_text, re.I)
    if match:
        query = match.group(1)
        return execute_tool('rag_query', params={'QUERY': query})
```

---

## 📊 Success Criteria (Automated)

From manifest, Athena validates:

### `stack_full` success:
- Bridge responds on 8014 ✅
- Athena responds on 8090 ✅
- UAT responds on 8181 ✅
- Kokoro responds on 8020 ✅
- RAG responds on 8015 ✅
- Vision responds on 8016 ✅

### `validate_platform` success:
- All health checks pass
- Meta headers present
- No timeouts

### `ship_it` success:
- Validation passes
- Confidence >= 0.75
- No critical errors

---

## 🧯 Troubleshooting

### Tools Not Showing Up

```bash
# Check tool registration
cat ~/.athena/config/tools/neuroforge.yaml

# Or query Athena
curl http://127.0.0.1:8090/api/tools | jq '.tools[] | select(.name | contains("stack"))'
```

### Intent Not Matching

Check intent patterns in manifest:
```yaml
intent_patterns:
  - "bring everything online"  # ← Exact match
  - "start full stack"         # ← Alternative
```

Test pattern matching:
```bash
# Send intent directly
curl -X POST http://127.0.0.1:8090/api/intent \
  -d '{"text": "bring everything online"}'
```

### Tool Timeout

Increase timeout in manifest:
```yaml
- name: stack_full
  timeout: 60  # ← Increase if needed
```

---

## 🎯 Quick Start Checklist

- [ ] Tools created in `/tools/`
- [ ] Scripts are executable (`chmod +x tools/*.sh`)
- [ ] Manifest exists: `tools/athena_tools.yaml`
- [ ] Register tools with Athena (pick method above)
- [ ] Restart Athena
- [ ] Test: `./tools/stack_full.sh` (CLI)
- [ ] Test: "Bring everything online" (Voice)
- [ ] Verify: Tools show in Athena's tool list

---

## 🚀 Next Steps

1. **Register tools** with Athena (pick integration method)
2. **Test CLI**: Run `./tools/stack_full.sh`
3. **Test voice**: Say "bring everything online"
4. **Validate**: Run `./tools/validate_platform.sh`
5. **Ship**: Say "ship it" (gated by validation)

---

## 📞 Support Commands

```bash
# List available tools
ls -l tools/*.sh

# Test a tool manually
./tools/stack_full.sh

# Check Athena tool registry
curl http://127.0.0.1:8090/api/tools

# Reload Athena tools
cd athena && python restart.py
```

---

**✅ Integration Complete. Voice-driven platform orchestration ready!** 🎤🚀

