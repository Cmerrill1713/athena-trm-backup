# Debug Summary: Service Startup Issues

## Problem
Services kept dying/exiting with various errors:
- Bridge: killed
- Athena: "done" (exited normally - shouldn't happen for server)
- UAT: "exit 1" (failed) or "killed"

## Root Causes Found

### 1. Missing Authentication Tokens
**Symptom**: Services would start but couldn't communicate
**Cause**: UAT and Athena require auth tokens
**Fix**:
```bash
ATH_TOKEN=supersecret
UAT_TOKEN=supersecret
```

### 2. Wrong Port Configuration
**Symptom**: Bridge reported UAT as "HTTP 401" even with tokens
**Cause**: Bridge defaulted to wrong port for UAT
```python
# bridge/adapter.py line 54
UAT_BASE = os.environ.get("UAT_BASE", "http://127.0.0.1:8080")  # WRONG!
```
**Actual**: UAT runs on port 8181
**Fix**:
```bash
UAT_BASE=http://127.0.0.1:8181
ATHENA_BASE=http://127.0.0.1:8090
```

### 3. Incorrect File Paths
**Symptom**: "can't open file" errors in logs
**Cause**: Services moved to AI-Projects/universal-ai-tools/
**Wrong paths**:
- `athena/server.py` (doesn't exist)
- `orchestrator/main.py` (doesn't exist)

**Correct paths**:
- `AI-Projects/universal-ai-tools/athena/api.py` ✅
- `AI-Projects/universal-ai-tools/uat/api.py` ✅

## Final Working Configuration

### Athena
```bash
cd /Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools
source ../../.venv/bin/activate
ATH_TOKEN=supersecret \
  python -m uvicorn athena.api:app --host 127.0.0.1 --port 8090
```

### UAT
```bash
cd /Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools
source ../../.venv/bin/activate
UAT_TOKEN=supersecret UAT_AUTO_SEED=1 \
  python -m uvicorn uat.api:app --host 127.0.0.1 --port 8181
```

### Bridge
```bash
cd /Users/christianmerrill/Documents/GitHub/bridge
source ../.venv/bin/activate
UAT_TOKEN=supersecret \
ATH_TOKEN=supersecret \
UAT_BASE=http://127.0.0.1:8181 \
ATHENA_BASE=http://127.0.0.1:8090 \
PYTHONPATH=.. \
  uvicorn adapter:app --host 0.0.0.0 --port 8014
```

### Kokoro (was already working)
```bash
# No changes needed
```

## Makefile Fix

Updated `stack-up` target in Makefile to:
1. Start Athena first (with ATH_TOKEN)
2. Start UAT second (with UAT_TOKEN, UAT_AUTO_SEED=1)
3. Start Bridge last (with all tokens and correct BASE URLs)

This ensures services are available when Bridge tries to connect.

## Verification

After fixes, Bridge `/health` endpoint shows:
```json
{
    "status": "healthy",
    "adapter": "neuroforge-adapter-v1.0.0",
    "uat": { "status": "healthy", "traces_loaded": 170 },
    "athena": { "status": "healthy", "agents_available": 3 }
}
```

## Key Learnings

1. **Service Discovery**: Document actual ports and require explicit env vars
2. **Auth First**: Start services with auth tokens from the beginning
3. **Start Order**: Dependent services (Bridge) should start AFTER dependencies (Athena, UAT)
4. **Validation**: Always check `/health` endpoints show "healthy", not just 200 OK

## Quick Start Command

```bash
make stack-up
# Wait 5 seconds
make stack-status
```

Should show:
```
OK All services up: 4/4
```

---

**Date**: October 13, 2025
**Status**: ✅ RESOLVED
**Services**: All 4/4 operational
