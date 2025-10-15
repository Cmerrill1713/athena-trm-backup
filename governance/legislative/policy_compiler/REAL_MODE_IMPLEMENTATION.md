# Real Mode Implementation Plan

## Status: In Progress

### P0 — Make "real mode" actually real

- [ ] **1. UAT Service (8080)**
  - [ ] Create `/traces` endpoint (170+ transcripts)
  - [ ] Create `/trace/{id}` endpoint
  - [ ] Create `/health`, `/stats`, `/capabilities`
  - [ ] Add Bearer auth middleware
  - [ ] Seed 170 transcripts
  - [ ] Target: p95 < 250ms

- [ ] **2. Athena Service (8090)**
  - [ ] Create `/chat` endpoint (stream + non-stream)
  - [ ] Create `/agents` endpoint
  - [ ] Create `/health` endpoint
  - [ ] Add Bearer auth middleware
  - [ ] Target: Valid replies with route labels

- [ ] **3. Lock down auth**
  - [ ] Bearer validation on UAT
  - [ ] Bearer validation on Athena
  - [ ] Bridge forwards tokens
  - [ ] Target: 401 without token, 200 with token

- [ ] **4. Flip bridge to real**
  - [ ] Start with USE_MOCK=0
  - [ ] Configure UAT_BASE, ATHENA_BASE
  - [ ] Target: Real data primary, mock on failure

### P1 — Hardening & observability

- [ ] **5. Contract test pack**
  - [ ] pytest suite for bridge, UAT, Athena
  - [ ] CI job "interop"
  
- [ ] **6. Circuit-breaker metrics**
  - [ ] Counters for breaker states
  - [ ] Structured logging
  - [ ] Grafana panel

- [ ] **7. Data shape parity**
  - [ ] UAT trace schema matches TraceDTO
  - [ ] No client-side decode errors

### P2 — UX + ops polish

- [ ] **8. Provider transparency**
  - [ ] Show API_BASE in footer
  - [ ] Show token status
  - [ ] Show last route

- [ ] **9. Make targets**
  - [ ] `make uat-up`
  - [ ] `make athena-up`
  - [ ] `make all-real`

- [ ] **10. Chaos check**
  - [ ] Kill UAT → verify fallback
  - [ ] Restart UAT → verify recovery
  - [ ] Zero hard-errors

## Quick Start

```bash
# Start real backends
make uat-up
make athena-up

# Start bridge in real mode
USE_MOCK=0 UAT_BASE=http://127.0.0.1:8080 ATHENA_BASE=http://127.0.0.1:8090 \
UAT_TOKEN=supersecret ATH_TOKEN=supersecret make bridge-up

# Test
curl -H 'Authorization: Bearer supersecret' http://127.0.0.1:8014/health
curl -H 'Authorization: Bearer supersecret' http://127.0.0.1:8014/traces | jq '.[0]'
```


