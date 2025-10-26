# 🚀 **GO MIGRATION PLAN - Surgical, Not Wholesale**

## 🎯 **Strategy: Strangler Fig Pattern**

**Don't rewrite. Extract hot paths behind stable RPC interfaces.**

---

## 📊 **Language Decision Matrix:**

### **Keep in Python:**

✅ RAG & orchestration glue (FastAPI, Weaviate, embeddings)  
✅ Governance/policy engine (YAML/JSON, rule authoring)  
✅ Evaluation & experimentation (A/B tests, quality gates)  
✅ Agent logic & tooling (rapid iteration, rich libs)  
✅ Dev daemon (athena-devd) - already working great!

### **Move to Go:**

✅ Router (A2) request path - **FIRST CANDIDATE**  
✅ OpenAI-compat gateway - **FIRST CANDIDATE**  
✅ Event bus producers/consumers (NATS/Kafka)  
✅ Model lifecycle manager (heartbeats, capacity)  
✅ Telemetry gateways (OTEL, Prometheus)

### **Move to Rust (Later):**

⏳ Token streaming/SSE fan-out (ultra-low overhead)  
⏳ Security-sensitive components (policy sandbox)  
⏳ CPU-bound kernels (custom re-rankers)  
⏳ Latency-critical filters (circuit breakers)

---

## 🔧 **Service Boundaries (RPC-first):**

### **Current (Python):**

```
Python UAI (8080)          → Python Router (9113)      → Ollama/MLX
Python Governance (9110)   → Python Judicial (8096)
Python Learning (8098)     → Python AGI Core (8100)
```

### **Target (Hybrid):**

```
Go Gateway (8081)          → Go Router (9115)          → Ollama/MLX
  ↓ (gRPC)                   ↓ (gRPC)
Python Governance (9110)   Python Judicial (8096)

Python UAI (8080) - KEEP FOR NOW (shadowed by Go)
Python Learning (8098) - KEEP (experimentation)
Python AGI Core (8100) - KEEP (agent logic)
Python Dev Daemon (8765) - KEEP (working great!)
```

---

## 🎯 **Phase 1: Shadow & Validate (0-30 days)**

### **Goals:**

- Go router mirrors Python router
- Measure parity & performance
- Zero production impact

### **Steps:**

#### **1. Create Protobuf Contracts** ✅

**File:** `proto/athena.proto`

Services defined:

- Router.Decide (routing decisions)
- Governance.Authorize (authorization gate)
- RAG.Search (context retrieval)
- Health checks

#### **2. Implement Go Router** ⏳

**File:** `services/go-router/main.go`

Features:

- gRPC server on port 9115
- Calls Python governance via gRPC
- Emits NATS events
- Full OTEL tracing
- Health checks

#### **3. Implement Go Gateway** ⏳

**File:** `services/go-gateway/main.go`

Features:

- HTTP server on port 8081
- OpenAI-compatible `/v1/chat/completions`
- SSE streaming with backpressure
- Calls Go router via gRPC
- Rate limiting

#### **4. Add to Docker Compose** ⏳

```yaml
services:
  go-router:
    build: ./services/go-router
    ports:
      - "127.0.0.1:9115:9115" # gRPC (shadow mode)
    environment:
      - GOVERNANCE_URL=governance-orchestrator:9110
      - NATS_URL=nats://athena-nats:4222
    labels:
      - "athena.mode=shadow"
      - "athena.replaces=python-router"

  go-gateway:
    build: ./services/go-gateway
    ports:
      - "127.0.0.1:8081:8081" # HTTP (shadow mode)
    environment:
      - ROUTER_URL=go-router:9115
    labels:
      - "athena.mode=shadow"
      - "athena.replaces=python-uai"
```

#### **5. Shadow Traffic**

```bash
# Use existing test suite to hit both:
# - Python: localhost:8080, localhost:9113
# - Go: localhost:8081, localhost:9115

# Compare metrics:
make test-python-stack > python_metrics.json
make test-go-stack > go_metrics.json
make compare-stacks
```

#### **6. Measure Parity**

**Exit Criteria:**

- ✅ Decision parity ≥ 99%
- ✅ p95 latency improves ≥ 20%
- ✅ Error rate ≤ 0.3%
- ✅ No quality gate regressions

---

## 🎯 **Phase 2: Cut Over Hot Path (31-60 days)**

### **Goals:**

- Go handles production traffic
- Python becomes fallback
- Full observability maintained

### **Steps:**

#### **1. Feature Flag Setup**

```yaml
# feature_flags.yml
go_router_enabled:
  percentage: 0 # Start at 0%
  users: [] # Allowlist for testing

go_gateway_enabled:
  percentage: 0
  users: []
```

#### **2. Progressive Rollout**

```bash
# Week 1: 5%
make set-go-traffic --percentage 5
make canary-watch

# Week 2: 20%
make set-go-traffic --percentage 20
make canary-watch

# Week 3: 50%
make set-go-traffic --percentage 50
make canary-watch

# Week 4: 100%
make set-go-traffic --percentage 100
make metrics-snapshot  # New baseline!
```

#### **3. Rollback Safety**

```bash
# Instant rollback if gates fail:
make rollback-to-python
```

#### **4. Retirement**

```bash
# After 30 days at 100% with no issues:
make retire-python-router
make retire-python-gateway
# (Archive, don't delete - keep for 90 days)
```

---

## 🎯 **Phase 3: Optimize & Expand (61-90 days)**

### **Optional Rust SSE Streamer:**

If p99 still high under load:

```rust
// services/rust-streamer/src/main.rs
// Ultra-low-latency SSE fan-out with tokio
// Zero-copy where possible
// Predictable tail latency
```

### **Model Lifecycle Manager → Go:**

```go
// services/go-lifecycle/main.go
// Heartbeats, capacity checks, rate limiting
// Calls Python governance for policy
```

---

## 📊 **Measurement Tools:**

### **Before Touching Code:**

```bash
# 1. Baseline Python performance
k6 run --vus 50 --duration 5m test_chat_completions.js > baseline_python.json

# 2. Profile hot paths
py-spy record -o python_flamegraph.svg -- python services/router/app.py

# 3. Check p95/p99
curl http://localhost:9090/api/v1/query?query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
```

### **During Shadow:**

```bash
# Compare side-by-side
make shadow-test --iterations 1000
# Output: parity_percentage, latency_delta, error_delta
```

### **After Cutover:**

```bash
# Continuous monitoring
make monitor-go-services
# Grafana dashboard: "Go vs Python Performance"
```

---

## 🛡️ **Risk Mitigation:**

### **1. Team Context Switch:**

- Restrict Go work to 2 services (router, gateway)
- Keep everything else Python
- Document RPC contracts clearly

### **2. FFI Pain:**

- **Never embed** - always RPC (gRPC/HTTP)
- Keep Python governance untouched
- Call it via gRPC from Go

### **3. Duplicated Logic:**

- Centralize schemas in `proto/`
- Share feature flags via Redis/etcd
- One OTEL setup for all languages

### **4. Observability Split:**

- W3C traceparent across all services
- Single Grafana dashboard
- Language-agnostic metrics labels

---

## 🎯 **Decision Rules:**

### **Move to Go if:**

- ✅ On hot path (every user request)
- ✅ I/O-bound with concurrency needs
- ✅ Stable interface (not changing weekly)
- ✅ p95 latency > 500ms in Python

### **Keep in Python if:**

- ✅ Changes weekly (policies, prompts)
- ✅ Needs rich ML libraries
- ✅ Not on critical path
- ✅ Already fast enough

### **Move to Rust if:**

- ✅ CPU-tight (custom kernels)
- ✅ Needs constant-time behavior
- ✅ Security-sensitive (sandboxing)
- ✅ p99 tail matters

---

## 📦 **Files to Create:**

```
proto/
  └── athena.proto               # RPC contracts

services/go-router/
  ├── main.go                    # Router implementation
  ├── Dockerfile                 # Build container
  ├── go.mod                     # Dependencies
  └── go.sum

services/go-gateway/
  ├── main.go                    # OpenAI-compat gateway
  ├── Dockerfile
  ├── go.mod
  └── go.sum

scripts/
  ├── shadow_test.sh             # Shadow traffic testing
  ├── compare_stacks.sh          # Parity measurement
  └── progressive_rollout.sh     # Feature flag automation

docker-compose.shadow.yml        # Shadow services overlay
```

---

## 💙 **Bottom Line:**

**Don't rewrite Athena.**

**Do:**

1. ✅ Extract Go router (gRPC, NATS, OTEL)
2. ✅ Extract Go gateway (SSE, backpressure)
3. ✅ Keep Python governance (policy, rules)
4. ✅ Keep Python learning (experimentation)
5. ✅ Keep Python devd (already great!)

**Result:**

- 🚀 Lower tail latency where it counts
- 🔄 Fast iteration where you need it
- 📊 Clear rollback path
- 📈 Ready to scale 20 → 200+ concurrent users

---

**Surgical. Measured. Safe. Fast. 🚀💙**
