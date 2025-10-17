# Athena Router - Local-First Model Routing

**Port:** 9113  
**Policy:** MLX → Ollama → MCP-Browser → Cloud (governed)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start MLX server (in another terminal)
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080

# Start Ollama (in another terminal)
ollama serve

# Start router
python app.py
```

## Features

- ✅ **Local-first routing**: MLX and Ollama prioritized
- ✅ **Health monitoring**: Heartbeats every 5s with exponential backoff
- ✅ **Explainability**: Every decision logged to `state/router_decisions.jsonl`
- ✅ **Governance integration**: Cloud access blocked by default, only enabled via governance API
- ✅ **Prometheus metrics**: Latency, failovers, route share, cache hit rate
- ✅ **Prompt caching**: Short-lived cache for duplicate requests
- ✅ **Pre-warming**: MLX model loaded on startup

## Architecture

```
┌──────────────┐
│  Swift App   │
└──────┬───────┘
       │
       ▼
┌──────────────┐       ┌─────────────┐
│ Bridge/Chat  │──────>│   Router    │ :9113
│  Service     │       │   (app.py)  │
└──────────────┘       └──────┬──────┘
                              │
                    ┌─────────┼─────────┬─────────┐
                    ▼         ▼         ▼         ▼
                ┌─────┐  ┌────────┐ ┌─────┐  ┌──────┐
                │ MLX │  │ Ollama │ │ MCP │  │Cloud │
                │:8080│  │ :11434 │ │:8095│  │ ❌   │
                └─────┘  └────────┘ └─────┘  └──────┘
                  ✅         ✅        🔧      🚫
```

## API Endpoints

### `GET /health`

Returns router health and provider status.

```bash
curl http://127.0.0.1:9113/health
```

Response:

```json
{
  "status": "healthy",
  "providers": {
    "mlx": {
      "available": true,
      "p95_latency_ms": 480,
      "error_rate": 0.01,
      "consecutive_failures": 0
    },
    "ollama": {
      "available": true,
      "p95_latency_ms": 620
    }
  },
  "policy": {
    "order": ["mlx", "ollama", "mcp_browser", "cloud"],
    "allow_cloud": false
  }
}
```

### `POST /route`

Route a prompt to the best available provider.

```bash
curl -X POST http://127.0.0.1:9113/route \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Write a Swift function to reverse a string",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

Response:

```json
{
  "route": "mlx",
  "text": "Here's a Swift function...",
  "latency_ms": 450,
  "tokens_generated": 128,
  "cached": false,
  "provider_health": {
    "mlx": {"available": true},
    "ollama": {"available": true}
  },
  "decision_reasoning": "Routed to mlx (primary available)"
}
```

### `GET /metrics`

Prometheus metrics endpoint.

```bash
curl http://127.0.0.1:9113/metrics
```

### `POST /reload-policy`

Reload routing policy from disk.

```bash
curl -X POST http://127.0.0.1:9113/reload-policy
```

## Configuration

**File:** `services/router/policies/local_first.yaml`

```yaml
order:
  - mlx
  - ollama
  - mcp_browser
  - cloud

timeouts_ms:
  mlx: 1500
  ollama: 2000
  mcp_browser: 4000
  cloud: 5000

max_tokens: 1024
allow_cloud: false

failure_backoff_s:
  - 1
  - 2
  - 5
  - 15
  - 60
```

## Environment Variables

```bash
# MLX
export MLX_ENDPOINT=http://127.0.0.1:8080
export MLX_MODEL=qwen2.5-coder-7b

# Ollama
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5-coder:7b

# MCP Browser
export MCP_BROWSER_ENDPOINT=http://127.0.0.1:8095
export MCP_BROWSER_ENABLE=true

# Cloud (blocked by default)
export ATHENA_NO_CLOUD=1  # Hard block
unset OPENAI_API_KEY
unset ANTHROPIC_API_KEY

# Router
export ROUTER_PORT=9113
export ROUTER_HOST=127.0.0.1
export ROUTER_POLICY_PATH=services/router/policies/local_first.yaml
```

## Metrics

### Counters

- `athena_router_requests_total{route,status}` - Total requests
- `athena_router_decisions_count{route}` - Routing decisions
- `athena_router_failovers_count{from_provider,to_provider,reason}` - Failovers
- `athena_router_cloud_attempts_total{blocked}` - Cloud attempts (should be 0)
- `athena_router_cache_hits_total` - Cache hits
- `athena_router_cache_misses_total` - Cache misses

### Histograms

- `athena_router_latency_seconds{route}` - End-to-end latency

### Gauges

- `athena_router_allow_cloud` - Cloud enabled (0=disabled, 1=enabled)

## Decision Logging

All routing decisions are logged to `state/router_decisions.jsonl`:

```json
{
  "timestamp": "2025-10-17T15:30:45.123Z",
  "prompt_hash": "a3b2c1d4e5f6",
  "route": "mlx",
  "latency_ms": 450,
  "provider_health": {
    "mlx": {"available": true, "p95_latency_ms": 480}
  },
  "cached": false
}
```

## Governance Integration

Cloud access is **disabled by default** and can only be enabled via the Governance Executive API:

```bash
# Enable cloud for 2 hours
curl -X POST http://127.0.0.1:9110/verdict \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "ALLOW_CLOUD",
    "reason": "emergency_fallback",
    "ttl_minutes": 120
  }'
```

The router watches `state/router_policy_overrides.json` and automatically enables/disables cloud access based on TTL.

## Failover Behavior

1. **MLX fails** → Router tries Ollama
2. **Ollama fails** → Router tries MCP-Browser (if enabled)
3. **All local fail** → Router returns 503 (cloud blocked)

Failovers are tracked in metrics:

```
athena_router_failovers_count{from_provider="mlx",to_provider="ollama",reason="provider_failure"} 5
```

## Health Monitoring

- **Heartbeat interval**: 5 seconds
- **Consecutive failures trigger backoff**: 3 failures → unavailable
- **Exponential backoff**: 1s, 2s, 5s, 15s, 60s
- **Auto-recovery**: Provider marked available on next successful heartbeat

## Performance Targets

- **p95 latency**: ≤ 1.2s on M2 Ultra
- **Local-first share**: ≥ 85% served by MLX/Ollama
- **Failover correctness**: 100% (no dropped requests)
- **Cache hit rate**: ≥ 20% for typical usage

## Testing

### Test basic routing

```bash
curl -s http://127.0.0.1:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello"}' | jq '.route'
# Expected: "mlx"
```

### Test failover

```bash
# Stop MLX server, then:
curl -s http://127.0.0.1:9113/route \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Hello"}' | jq '.route'
# Expected: "ollama"
```

### Test cache

```bash
# Send same prompt twice
for i in {1..2}; do
  curl -s http://127.0.0.1:9113/route \
    -d '{"prompt":"test"}' \
    -H 'Content-Type: application/json' | jq '.cached'
done
# First: false, Second: true
```

### Test governance

```bash
# Cloud should be blocked
curl -s http://127.0.0.1:9113/metrics | grep athena_router_allow_cloud
# Expected: athena_router_allow_cloud 0

# Enable via governance
curl -X POST http://127.0.0.1:9110/verdict \
  -d '{"action":"ALLOW_CLOUD","ttl_minutes":5}' \
  -H 'Content-Type: application/json'

# Wait 30s for router to detect, then check
curl -s http://127.0.0.1:9113/metrics | grep athena_router_allow_cloud
# Expected: athena_router_allow_cloud 1
```

## Troubleshooting

### Router won't start

```bash
# Check port availability
lsof -i :9113

# Check logs
python app.py
```

### MLX not detected

```bash
# Verify MLX is running
curl http://127.0.0.1:8080/health

# Check router logs for "Provider mlx failure"
```

### High latency

```bash
# Check p95 latency in metrics
curl -s http://127.0.0.1:9113/metrics | grep p95

# Check provider health
curl http://127.0.0.1:9113/health | jq '.providers'
```

### Cloud attempts not blocked

```bash
# Verify hard block
echo $ATHENA_NO_CLOUD  # Should be "1"

# Check metrics
curl -s http://127.0.0.1:9113/metrics | grep cloud_attempts_total
# Should show only blocked="true" entries
```

## Development

### Add a new provider

1. Create `services/router/providers/my_provider.py`:

```python
from .base_provider import BaseProvider

class MyProvider(BaseProvider):
    async def generate(self, prompt, max_tokens, temperature):
        # Implementation
        pass
    
    async def health_check(self):
        # Implementation
        pass
```

2. Register in `app.py`:

```python
providers['my_provider'] = MyProvider(
    endpoint=os.getenv("MY_PROVIDER_ENDPOINT"),
    timeout_ms=config.timeouts_ms.get('my_provider', 2000)
)
```

3. Add to `local_first.yaml`:

```yaml
order:
  - mlx
  - my_provider
  - ollama
```

## See Also

- [MLX Setup Guide](../../docs/setup/MLX_SETUP.md)
- [Governance Executive API](../../governance/executive/api.py)
- [Grafana Dashboard](../../infra/grafana/dashboards/router.json)
- [Prometheus Rules](../../infra/prometheus/router.rules.yml)


