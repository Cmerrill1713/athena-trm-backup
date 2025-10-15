# Stack Management Guide

> **One-command stack control for UAT + Athena + Bridge**

This guide covers the new unified stack management system that allows you to boot, manage, and test the entire backend infrastructure with simple commands.

## Overview

The stack consists of three services running in real mode:

- **UAT (Universal AI Tools)** - Port 8181 - Orchestration & telemetry
- **Athena** - Port 8090 - Agent system with tool calls
- **Bridge** - Port 8014 - NeuroForge adapter

## Quick Start

### Start the entire stack
```bash
make stack-up
```

### Check status
```bash
make stack-status
```

### Run integration tests via Athena
```bash
make athena-tests
```

### Stop everything
```bash
make stack-down
```

## Detailed Commands

### `make stack-up`
Starts all three services in real mode (no mocks):
- Kills any processes on ports 8181, 8090, 8014
- Starts UAT on port 8181
- Starts Athena on port 8090
- Starts Bridge on port 8014 (real mode)
- Waits for services to initialize
- Performs health check

**Logs:**
- UAT: `logs/uat_8181.log`
- Athena: `logs/athena_8090.log`
- Bridge: `logs/bridge_8014.log`

**PIDs:**
- `.stack/uat.pid`
- `.stack/athena.pid`
- `.stack/bridge.pid`

### `make stack-down`
Gracefully stops all services:
- Kills processes using PID files
- Cleans up PID files
- Ensures ports are freed

### `make stack-status`
Shows current status:
- Running processes and PIDs
- Port assignments
- Bridge health check

### `make stack-restart`
Equivalent to:
```bash
make stack-down
make stack-up
```

### `make athena-tests`
Asks Athena to run the integration test suite:
- Executes pytest with markers: `smoke,e2e,backends,slo`
- Returns structured JSON results
- Shows test summary and failures

## Environment Variables

Override defaults as needed:

```bash
# Ports
UAT_PORT=8181       # UAT service port
ATH_PORT=8090       # Athena service port
BRIDGE_PORT=8014    # Bridge adapter port

# Authentication
UAT_TOKEN=supersecret    # UAT auth token
ATH_TOKEN=supersecret    # Athena auth token
BRIDGE_TOKEN=            # Bridge auth token (empty = no auth in dev)

# Environment
ENV=dev             # Environment (dev/staging/prod)
```

Example with custom ports:
```bash
UAT_PORT=9181 ATH_PORT=9090 BRIDGE_PORT=9014 make stack-up
```

## Athena Tool Calling

Athena now supports tool calls via the `/tool_call` endpoint:

### Available Tools

#### `run_command`
Execute safe shell commands:
```bash
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "run_command",
    "params": {"command": "pytest --version"}
  }'
```

Allowed commands: `pytest`, `ls`, `cat`, `grep`, `find`, `echo`, `pwd`

#### `read_file`
Read file contents:
```bash
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "read_file",
    "params": {"path": "README.md", "max_lines": 50}
  }'
```

#### `list_directory`
List directory contents:
```bash
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_directory",
    "params": {"path": "."}
  }'
```

## Test Execution via Athena

### Run specific test markers
```bash
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "suite": "integration",
    "markers": "smoke",
    "verbose": false,
    "maxfail": 1
  }'
```

### Request Parameters

- `suite`: Test suite name (default: "integration")
- `markers`: Pytest markers to filter tests (e.g., "smoke,e2e")
- `verbose`: Enable verbose output (default: false)
- `maxfail`: Stop after N failures (default: 1)

### Response Format

```json
{
  "ok": true,
  "cmd": "pytest tests/ -m smoke --maxfail=1 --disable-warnings -q",
  "cwd": "/Users/christianmerrill/Documents/GitHub",
  "summary": {
    "passed": 10,
    "failed": 0,
    "skipped": 2,
    "errors": 0
  },
  "stdout": "...test output...",
  "stderr": "",
  "report": { /* JSON report data */ },
  "timestamp": "2025-10-12T10:30:00.000Z"
}
```

## Full Development Flow

### 1. Start the stack
```bash
make stack-up
```

### 2. Verify health
```bash
# Check all services
make stack-status

# Bridge health (shows UAT + Athena status)
curl -s http://127.0.0.1:8014/health | jq .

# UAT direct
curl -s -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8181/health

# Athena direct
curl -s -H "Authorization: Bearer supersecret" \
  http://127.0.0.1:8090/health
```

### 3. Run tests
```bash
# Via Athena (recommended)
make athena-tests

# Or directly
pytest -m smoke tests/interop/
```

### 4. Launch the app
```bash
# In a new terminal
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

### 5. Stop everything
```bash
make stack-down
```

## Troubleshooting

### Ports already in use
```bash
# Kill all processes on stack ports
lsof -ti:8014,8181,8090 | xargs kill -9

# Then restart
make stack-up
```

### Bridge in mock mode
The stack always starts in real mode. If you see mock data:
```bash
# Verify environment
curl http://127.0.0.1:8014/ | jq .use_mock
# Should return: false

# If true, restart stack
make stack-restart
```

### Athena 401 errors
Token mismatch. Check environment:
```bash
# Should match on both sides
echo $ATH_TOKEN
# vs. what's in .stack logs

# Set explicitly
ATH_TOKEN=supersecret make stack-up
```

### Tests hang
Increase timeout in athena/api.py or run specific markers:
```bash
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers": "smoke"}'
```

### View logs
```bash
# All logs
tail -f logs/uat_8181.log
tail -f logs/athena_8090.log
tail -f logs/bridge_8014.log

# Or combined
tail -f logs/*.log
```

## Architecture

```
┌─────────────────┐
│  NeuroForge App │
│   (SwiftUI)     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Bridge :8014   │  ◄── Adapter layer
│  (FastAPI)      │
└────┬───────┬────┘
     │       │
     │       └──────────────┐
     ▼                      ▼
┌─────────────┐    ┌──────────────┐
│  UAT :8181  │    │ Athena :8090 │
│ Orchestrate │    │    Agents    │
│  Telemetry  │    │  Tool Calls  │
└─────────────┘    └──────────────┘
```

## Capabilities Matrix

| Service | Port | Role | Auth | Endpoints |
|---------|------|------|------|-----------|
| UAT | 8181 | Orchestration, traces | Bearer | /health, /traces, /capabilities |
| Athena | 8090 | Agents, chat, tools | Bearer | /chat, /agents, /tool_call, /run_tests |
| Bridge | 8014 | Adapter | Optional | /health, /chat, /traces |

## Security Notes

1. **Development mode** (`ENV=dev`):
   - Authentication optional
   - Bridge token not required
   - Verbose logging

2. **Production mode** (`ENV=prod`):
   - All tokens required
   - USE_MOCK must be 0
   - Stack refuses to start if USE_MOCK=1 in prod

3. **Token management**:
   - Use strong tokens in production
   - Rotate regularly
   - Never commit tokens to git

## Next Steps

- [Integration Tests Guide](./tests/interop/README.md)
- [Bridge Adapter Spec](./bridge/README.md)
- [Athena Agent System](./AI-Projects/universal-ai-tools/athena/README.md)

---

**Questions?** Run `make help` for full command reference.
