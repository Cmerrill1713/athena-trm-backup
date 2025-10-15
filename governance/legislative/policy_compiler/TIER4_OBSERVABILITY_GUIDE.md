# 📊 Tier 4: Observability & Guardrails - Integration Guide

> **Prove reliability with metrics, not vibes**

---

## ✅ Status: Foundation Ready

**Created:**
- ✅ `common/ops.py` - Production tooling library
- ✅ `common/secrets.py` - Secure secrets management
- ✅ `otel/collector.yaml` - OTLP collector config
- ✅ `requirements.txt` - All dependencies
- ✅ Makefile targets for verification

**Next:** Wire into services (Bridge, Athena, UAT)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
make install-tier4-deps
```

Installs:
- OpenTelemetry SDK + exporters
- FastAPI instrumentation
- Rate limiting (slowapi)
- Secrets management (keyring)

### 2. Start OTLP Collector (Optional)
```bash
make otel-up
```

Runs OpenTelemetry Collector in Docker:
- HTTP endpoint: `:4318`
- gRPC endpoint: `:4317`
- Exports to console (logging exporter)

### 3. Configure Environment
```bash
# Add to .env.stack
echo "OTLP_ENDPOINT=http://localhost:4318/v1/traces" >> .env.stack
echo "RATE_LIMIT=100/minute" >> .env.stack
echo "MAX_BODY_MB=5" >> .env.stack
echo "REQ_TIMEOUT_S=30" >> .env.stack
echo "DRAIN_S=5" >> .env.stack
```

---

## 🔧 Service Integration

### Bridge (Example)

**File:** `bridge/adapter.py`

Add at the top:
```python
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ops import (
    wire_tracing,
    attach_guardrails,
    install_graceful_shutdown,
    add_health_endpoints
)
```

After `app = FastAPI(...)`:
```python
# Health & readiness endpoints (/live, /ready)
add_health_endpoints(app)

# OpenTelemetry tracing
wire_tracing(app, service_name="neuroforge-bridge")

# Guardrails (rate limiting, payload limits, timeouts)
attach_guardrails(
    app,
    per_ip_rate=os.getenv("RATE_LIMIT", "100/minute"),
    max_body_mb=int(os.getenv("MAX_BODY_MB", "5")),
    request_timeout_s=int(os.getenv("REQ_TIMEOUT_S", "30"))
)

# Graceful shutdown with 5s drain
install_graceful_shutdown(app, drain_seconds=int(os.getenv("DRAIN_S", "5")))
```

**Repeat for:**
- `AI-Projects/universal-ai-tools/athena/api.py` (service_name="athena")
- `AI-Projects/universal-ai-tools/uat/api.py` (service_name="uat")

---

## 🧪 Verification Steps

### A) Test Tracing

```bash
# 1. Start collector
make otel-up

# 2. Set endpoint and restart stack
export OTLP_ENDPOINT=http://localhost:4318/v1/traces
make stack-restart

# 3. Generate some traffic
curl -s http://127.0.0.1:8014/health > /dev/null
curl -s http://127.0.0.1:8014/traces > /dev/null

# 4. Check collector logs for spans
docker logs otel-collector

# Expected: Should see trace spans with service.name=neuroforge-bridge
```

### B) Test Rate Limiting

```bash
# Start stack
make stack-up

# Burst 105 requests (limit is 100/min)
make guardrails-smoke

# Expected output:
#   1 200
#   1 200
#   ...
#   5 429  ← Rate limit exceeded!
```

### C) Test Request Timeout

Create a test endpoint temporarily:
```python
# In any service
@app.get("/slow")
async def slow():
    import asyncio
    await asyncio.sleep(40)  # Exceeds 30s timeout
    return {"ok": True}
```

```bash
# Should return 504 after ~30s
time curl -i http://127.0.0.1:8014/slow
```

### D) Test Graceful Shutdown

```bash
# Terminal 1: Watch logs
tail -f logs/bridge_8014.log

# Terminal 2: Send SIGTERM
make shutdown-drain-test

# Expected in logs:
# [Shutdown] Draining for 5s ...
# [Shutdown] Done.
```

---

## 🔒 Secrets Management

### macOS Keychain (Recommended)

```bash
# Store secrets in keychain (one-time)
security add-generic-password -a stack -s "uat_token" -w "supersecret"
security add-generic-password -a stack -s "ath_token" -w "supersecret"
```

### Update Services
```python
from common.secrets import load_secret

# Instead of:
UAT_TOKEN = os.getenv("UAT_TOKEN", "")

# Use:
UAT_TOKEN = load_secret("uat_token", "UAT_TOKEN", "")
```

**Benefits:**
- ✅ Tokens not in environment
- ✅ Keychain is encrypted
- ✅ Falls back to env vars
- ✅ Production migration path

---

## 📊 What You Get

### Tracing
- ✅ Distributed traces across all services
- ✅ Request correlation IDs
- ✅ Timing for each span
- ✅ OTLP export (Tempo/Jaeger-ready)

### Guardrails
- ✅ Per-IP rate limiting (100/min default)
- ✅ Payload size limits (5MB default)
- ✅ Global request timeout (30s default)
- ✅ Automatic 429/413/504 responses

### Graceful Shutdown
- ✅ 5-second drain period
- ✅ In-flight requests complete
- ✅ Clean SIGTERM/SIGINT handling
- ✅ Zero dropped requests

### Health Checks
- ✅ `/live` - Liveness probe (process alive?)
- ✅ `/ready` - Readiness probe (ready for traffic?)
- ✅ `/health` - Existing comprehensive check

---

## 🎯 Environment Variables

```bash
# Tracing
OTLP_ENDPOINT=http://localhost:4318/v1/traces

# Guardrails
RATE_LIMIT=100/minute     # Per-IP rate limit
MAX_BODY_MB=5             # Max request body size
REQ_TIMEOUT_S=30          # Global request timeout
DRAIN_S=5                 # Shutdown drain period

# Environment
ENV=dev                   # Used in trace resource attributes
```

---

## 🐳 Docker Compose Integration

**File:** `docker-compose.observability.yml`

```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./otel/collector.yaml:/etc/otelcol/config.yaml
    ports:
      - "4318:4318"  # OTLP HTTP
      - "4317:4317"  # OTLP gRPC
    environment:
      - ENV=${ENV:-dev}
    restart: unless-stopped

  bridge:
    build: ./bridge
    ports:
      - "8014:8014"
    environment:
      - OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
      - RATE_LIMIT=100/minute
      - MAX_BODY_MB=5
      - REQ_TIMEOUT_S=30
      - DRAIN_S=5
      - UAT_BASE=http://uat:8181
      - ATHENA_BASE=http://athena:8090
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8014/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Similar for athena and uat...
```

---

## 📈 Next Steps

### Immediate
1. **Install deps:** `make install-tier4-deps`
2. **Wire Bridge:** Add common/ops imports + setup
3. **Wire Athena:** Add common/ops imports + setup
4. **Wire UAT:** Add common/ops imports + setup
5. **Test:** Run verification steps

### Week 1
- Start OTLP collector
- Generate traffic
- Verify traces flowing
- Test all guardrails
- Validate graceful shutdown

### Week 2
- Add Grafana dashboards
- Define SLOs
- Create alert rules
- Run chaos drills
- Document metrics

---

## 🎯 Success Criteria

- [ ] All services export OTLP traces
- [ ] Rate limiting returns 429 after threshold
- [ ] Payload limits return 413 for large bodies
- [ ] Request timeout returns 504 after 30s
- [ ] Graceful shutdown drains for 5s
- [ ] /live and /ready endpoints work
- [ ] Secrets loaded from keychain (optional)

---

## 📚 Documentation

- **TIER4_OBSERVABILITY_GUIDE.md** - This guide
- **common/ops.py** - Implementation
- **otel/collector.yaml** - Collector config
- **requirements.txt** - Dependencies

---

## 🚀 Quick Commands

```bash
# Install
make install-tier4-deps

# Start collector
make otel-up

# Test tracing
make trace-local

# Test rate limits
make guardrails-smoke

# Test shutdown
make shutdown-drain-test

# Stop collector
make otel-down
```

---

**Status:** ✅ Foundation ready for Tier 4
**Next:** Wire services and verify
**Timeline:** This week for complete Tier 4

🎯 **Ready to integrate into services!**
