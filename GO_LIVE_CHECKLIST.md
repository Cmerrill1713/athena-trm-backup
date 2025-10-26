# 🚀 Go-Live Checklist — Production Deployment

**Complete pre-launch validation and cutover procedures.**

---

## 🎯 Final Validation (Run This First)

### One-Command Green-Light

```bash
# Run complete validation
bash scripts/go_live_drill.sh
```

**Expected output:**

```
🚀 GO-LIVE DRILL — Final Validation
================================================

🔴 CRITICAL GATES (Must Pass)

[1] Adapter /healthz returns 200 with diagnostics
✅ PASS

[2] /v1/models lists athena-rag, athena-chat, athena-hybrid
✅ PASS

[3] Non-stream /v1/chat/completions returns valid OpenAI format
✅ PASS

[4] Stream /v1/chat/completions returns SSE format with [DONE]
✅ PASS

[5] All 3 models route and return non-empty content
✅ PASS

📋 CONTRACT VALIDATION

[6] OpenAI contract: response has id, model, choices, usage
✅ PASS

[7] OpenAI contract: message.content is non-empty string
✅ PASS

[8] Invalid model returns 400 error
✅ PASS

🎯 RAG QUALITY GATES

[9] RAG evaluation: hit@5 ≥ 0.97, support@3 ≥ 0.95
✅ PASS

[10] Delta report: semantic ≥ BM25
✅ PASS

🏗️  INFRASTRUCTURE VALIDATION

[11] Weaviate schema contains classes
✅ PASS

[12] Metrics endpoint exposes Prometheus format
✅ PASS

[13] Open WebUI reachable
✅ PASS

⚡ PERFORMANCE BASELINE

p95 latency: 650ms
✅ Latency acceptable (<1500ms)

================================================
GO-LIVE DRILL SUMMARY

  Passed: 14
  Failed: 0

✅ ALL GATES PASSED — READY FOR PRODUCTION
```

---

## 📋 Pre-Production Checklist

### Infrastructure (MUST DO)

- [ ] **Restore Weaviate corpus** (5.8GB from external drive)

  ```bash
  cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
    ./volumes/weaviate_data/
  ```

- [ ] **Run go-live drill** — All gates must pass

  ```bash
  bash scripts/go_live_drill.sh
  ```

- [ ] **Configure TLS/SSL** — Add certificates to nginx.conf

  ```nginx
  ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
  ```

- [ ] **Enable authentication** — Set API_KEY env var

  ```env
  API_KEY=your-secret-key-here
  ```

- [ ] **Restrict CORS** — Set allowed origins

  ```env
  CORS_ORIGIN=https://your-ui-domain.com
  ```

- [ ] **Configure rate limiting** — Update nginx.conf
  ```nginx
  limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
  ```

### Monitoring (MUST DO)

- [ ] **Import Grafana dashboard**

  ```bash
  # Import grafana-dashboard.json via UI
  # Or: curl -X POST http://grafana:3000/api/dashboards/db \
  #   -H "Content-Type: application/json" \
  #   --data @grafana-dashboard.json
  ```

- [ ] **Load Prometheus alert rules**

  ```yaml
  # prometheus.yml
  rule_files:
    - "prometheus-alerts.yml"
  ```

- [ ] **Configure Alertmanager** — Add Slack/PagerDuty webhook

  ```yaml
  # alertmanager.yml
  receivers:
    - name: "slack"
      slack_configs:
        - api_url: "YOUR_WEBHOOK_URL"
          channel: "#alerts-rag"
  ```

- [ ] **Verify metrics scraping**
  ```bash
  curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "openai-compat")'
  ```

### Testing (MUST DO)

- [ ] **E2E test passes**

  ```bash
  make e2e  # Must show: ✅ E2E TEST PASSED
  ```

- [ ] **Load test passes**

  ```bash
  k6 run k6-rag.js  # p95 <1.5s, errors <0.3%
  ```

- [ ] **Smoke test passes**
  ```bash
  cd services/openai-compat && ./smoke-test.sh
  ```

### Security (MUST DO)

- [ ] **Secrets in env/vault** — No tokens in git
- [ ] **Resource limits set** — CPU, memory caps in docker-compose
- [ ] **HSTS enabled** — Force HTTPS

  ```nginx
  add_header Strict-Transport-Security "max-age=31536000" always;
  ```

- [ ] **Request validation** — Already implemented ✅
- [ ] **Error sanitization** — No sensitive data in logs ✅

### Operations (SHOULD DO)

- [ ] **Runbook reviewed** — Team trained
- [ ] **Rollback procedure tested**

  ```bash
  docker service update --rollback openai-compat
  ```

- [ ] **Backup procedure tested**

  ```bash
  tar -czf weaviate-backup-$(date +%Y%m%d).tar.gz \
    ./volumes/weaviate_data/
  ```

- [ ] **On-call rotation defined**
- [ ] **Incident response trained**

---

## 🔄 Canary Deployment Procedure

### Step 1: Deploy Canary (5% traffic)

```yaml
# docker-compose.canary.yml
services:
  openai-compat-canary:
    image: openai-compat:v2.0 # New version
    ports:
      - "3001:3000"
    environment:
      # Same config as main
```

**Nginx routing:**

```nginx
upstream openai_backend {
    server openai-compat:3000 weight=95;      # Stable
    server openai-compat-canary:3001 weight=5; # Canary (5%)
}
```

### Step 2: Monitor for 30 minutes

**Watch these metrics:**

```bash
# p95 latency delta
watch -n 10 'curl -s http://localhost:3000/metrics | grep http_request_duration'

# Error rate comparison
watch -n 10 'curl -s http://localhost:3000/metrics | grep http_requests_total | grep "code=\"5"'
```

**Gates for promotion:**

- ✅ p95 latency ≤ +10% vs baseline
- ✅ 5xx delta ≤ +0.3%
- ✅ Stream error rate ≤ +1%
- ✅ No OOM kills or crashes

### Step 3: Promote to 25% → 50% → 100%

**If gates pass after 30min:**

```nginx
# Update weights
upstream openai_backend {
    server openai-compat:3000 weight=75;
    server openai-compat-canary:3001 weight=25;  # 25%
}
```

**Wait 30min, check gates again, then:**

```nginx
# 50%
weight=50 each

# Wait 30min, then 100%
upstream openai_backend {
    server openai-compat-canary:3001;  # 100% canary
}

# Finally, swap tags
openai-compat:
  image: openai-compat:v2.0  # Promote canary to main
```

### Step 4: Rollback (if needed)

```bash
# Fast rollback (<2 minutes)
docker service update --rollback openai-compat

# Or: nginx weight back to 0
upstream openai_backend {
    server openai-compat:3000 weight=100;
    server openai-compat-canary:3001 weight=0;  # 0% canary
}
nginx -s reload
```

---

## 🎯 Production Toggles (Flip These)

### Before Exposing to Users

```env
# services/openai-compat/.env

# 🔴 SECURITY (Required)
API_KEY=your-secure-random-key-here
CORS_ORIGIN=https://your-ui-domain.com
ENABLE_AUTH=true

# ⚡ PERFORMANCE (Recommended)
TIMEOUT_MS=30000
DEFAULT_MODE=nearText
DEFAULT_TOP_K=5

# 📊 OBSERVABILITY (Required)
ENABLE_METRICS=true
LOG_LEVEL=info
MASK_SECRETS=true

# 🚫 SAFETY (Required)
ENABLE_SIGNUP=false              # Open WebUI
RATE_LIMIT_ENABLED=true          # Nginx
ATHENA_NO_CLOUD=1                # Hard block cloud
ATHENA_FAIL_CLOSED=1             # Fail if no local models
```

### Nginx Production Config

```nginx
# nginx.conf
events { worker_connections 1024; }

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';

    # Streaming settings
    proxy_buffering off;
    proxy_read_timeout 3600s;
    chunked_transfer_encoding on;

    server {
        listen 80;
        return 301 https://$server_name$request_uri;  # Force HTTPS
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        # HSTS
        add_header Strict-Transport-Transport "max-age=31536000" always;

        location /v1/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://openai-compat:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

## 👀 Eyes-On Dashboards

### What to Monitor (First 24 Hours)

**Every 10 minutes:**

- Adapter p95 latency (should be <1s)
- 5xx error rate (should be <0.3%)
- Active requests (watch for spikes)

**Every hour:**

- Stream error rate (should be <2%)
- Empty response rate (should be <5%)
- Memory usage (should be stable, no leaks)

**Daily:**

- RAG evaluation gates (run nightly)
- Delta trend (semantic vs BM25 over time)
- Backup completion status

### Grafana Panels to Watch

1. **Request Rate** — Should match expected traffic
2. **Error Rate** — Should stay below 0.3%
3. **p95 Latency** — Should stay below 1.5s
4. **Model Usage** — Verify distribution makes sense
5. **Backend Latency** — Identify slow backends
6. **Memory Usage** — Watch for leaks (should be flat)

---

## 🚨 Known Gotchas (Kill Them Now)

### 1. "Invalid model" in UI

**Symptom:** UI shows "Model not found" error

**Fix:** Ensure `/v1/models` lists exact model strings

```bash
curl http://localhost:3000/v1/models | jq '.data[].id'
# Must include: athena-rag, athena-chat, athena-hybrid
```

### 2. Streaming stalls

**Symptom:** Responses freeze mid-stream

**Fix:** Nginx buffering

```nginx
location /v1/ {
    proxy_buffering off;              # Critical!
    proxy_read_timeout 3600s;         # Long timeout for streams
    proxy_http_version 1.1;
    proxy_set_header Connection '';
}
```

### 3. RAG eval misses gates

**Symptom:** `make rag-eval` fails with low hit@k

**Fix:** Check seed IDs match Weaviate

```bash
# Check what doc IDs exist in Weaviate
curl -s http://localhost:8080/v1/objects?class=DocsV2&limit=5 | \
  jq '.objects[].properties.doc_id'

# Compare with seeds/eval_seed.jsonl expected_ids
```

### 4. Empty RAG responses

**Symptom:** "I couldn't find relevant information" on valid queries

**Fix:** Verify Weaviate has data

```bash
# Check object count
curl -s http://localhost:8080/v1/objects?class=KnowledgeDocumentBge | \
  jq '.objects | length'

# If 0, restore from external drive
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  ./volumes/weaviate_data/
```

### 5. CORS errors in browser

**Symptom:** "CORS policy" errors in browser console

**Fix:** Set proper CORS origin

```env
# services/openai-compat/.env
CORS_ORIGIN=https://your-ui-domain.com
```

**Nginx CORS headers:**

```nginx
add_header Access-Control-Allow-Origin https://your-ui-domain.com always;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
```

### 6. High latency spikes

**Symptom:** p95 >2s intermittently

**Root causes:**

- Weaviate HNSW query slow (increase `ef` parameter)
- Ollama model cold start (keep warm with health checks)
- Resource contention (check `docker stats`)

**Fix:**

```yaml
# Increase resources
deploy:
  resources:
    limits: { cpus: "4", memory: 8G }
```

### 7. Vector dimension mismatch

**Symptom:** "vector dimension mismatch" errors from Weaviate

**Fix:** Ensure embeddings are 384-dim (BGE model)

```bash
# Check vector dimension
curl -s http://localhost:8080/v1/objects/{UUID}?include=vector | \
  jq '.vector | length'
# Should be: 384
```

---

## 🔒 Security Final Checks

### Pre-Launch Security Audit

```bash
# 1. No secrets in logs
docker logs openai-compat | grep -i "token\|password\|secret" || echo "✅ Clean"

# 2. Auth enforced
curl -s http://localhost:3000/v1/chat/completions | jq .error
# Should require auth

# 3. Rate limiting works
for i in {1..35}; do
  curl -s http://localhost:3000/v1/models >/dev/null
done
# Should get 429 after 30 requests

# 4. CORS restricted
curl -H "Origin: https://evil.com" http://localhost:3000/v1/models -I
# Should be blocked if CORS_ORIGIN set

# 5. TLS enforced
curl http://your-domain.com
# Should redirect to https://
```

---

## 📊 Canary Cutover SLA

### Timeline

| Phase      | Traffic % | Duration | Gates                   |
| ---------- | --------- | -------- | ----------------------- |
| **Deploy** | 0%        | 5 min    | Deploy + health check   |
| **Canary** | 5%        | 30 min   | p95 ≤ +10%, 5xx ≤ +0.3% |
| **Ramp 1** | 25%       | 30 min   | Same gates              |
| **Ramp 2** | 50%       | 30 min   | Same gates              |
| **Ramp 3** | 100%      | 30 min   | Same gates              |
| **Stable** | 100%      | Ongoing  | Normal monitoring       |

**Total cutover time:** ~2.5 hours (conservative)

### Gate Monitoring

```bash
# Watch p95 latency
watch -n 10 'curl -s http://localhost:3000/metrics | \
  grep http_request_duration_seconds | grep "0.95"'

# Watch error rate
watch -n 10 'curl -s http://localhost:3000/metrics | \
  grep "http_requests_total" | grep "code=\"5"'

# Watch active requests (detect hangs)
watch -n 5 'curl -s http://localhost:3000/metrics | grep active_requests'
```

### Rollback Triggers

**Immediate rollback if:**

- p95 latency >+20% for 5 minutes
- 5xx rate >1% for 2 minutes
- Stream error rate >5% for 5 minutes
- Memory usage >2GB (leak detected)
- Any service crashes

**Rollback command:**

```bash
# Weight back to stable
docker-compose -f docker-compose.full-stack.yml up -d \
  --scale openai-compat-canary=0

# Or nginx:
# Set canary weight=0 in nginx.conf
nginx -s reload
```

---

## 🎯 Trust But Verify (Quick Checks)

### Contract Validation

```bash
# Verify OpenAI shape (critical for UI compatibility)
jq -e '.id and .choices[0].message.content and .model and .usage' \
  <<< "$(curl -s http://localhost:3000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"athena-rag","messages":[{"role":"user","content":"ping"}]}')"
```

**Must print:** `true` ✅

### Vector Sanity

```bash
# Ensure 384-dim BGE embeddings
OBJECT_ID=$(curl -s http://localhost:8080/v1/objects?class=KnowledgeDocumentBge&limit=1 | jq -r '.objects[0].id')
curl -s "http://localhost:8080/v1/objects/$OBJECT_ID?include=vector" | \
  jq '.vector | length'
```

**Must print:** `384` ✅

### Backend Connectivity

```bash
# Adapter can reach backends (from inside container)
docker exec openai-compat sh -c 'curl -sf http://rag-gateway:8090/health && echo " ✅ RAG reachable"'
docker exec openai-compat sh -c 'curl -sf http://smart-chat:8088/health && echo " ✅ Chat reachable"'
```

**Both must show:** ✅

---

## 📞 Day-0 Support Plan

### First 24 Hours

**Monitor:**

- Dashboard every 30 minutes
- Check alerts in Slack/PagerDuty
- Review error logs hourly

**Alert Response:**

- P0/P1: Acknowledge within 5 minutes
- Follow runbook procedures
- Document all incidents

**Scheduled Checks:**

```bash
# Every 4 hours: run quick smoke
cd services/openai-compat && ./smoke-test.sh

# Every 12 hours: backup Weaviate
tar -czf weaviate-backup-$(date +%Y%m%d-%H%M).tar.gz \
  ./volumes/weaviate_data/
```

### First Week

- Run nightly RAG evaluations
- Review metrics trends daily
- Tune alert thresholds
- Document any custom procedures
- Schedule post-launch retrospective

---

## 🎉 Final Go-Live Command

```bash
# 1. Run final validation
bash scripts/go_live_drill.sh

# 2. If all gates pass, deploy to production
docker-compose -f docker-compose.full-stack.yml \
  -f docker-compose.prod.yml \
  up -d

# 3. Monitor for first 30 minutes
watch -n 30 'curl -s http://localhost:3000/healthz | jq .'

# 4. Open UI and test manually
open https://your-domain.com

# 5. Celebrate! 🎉
```

---

## ✅ Sign-Off Checklist

### Engineering Lead

- [ ] All go-live drill gates passed
- [ ] Load test passed (p95 <1.5s)
- [ ] E2E test passed (all 10 gates)
- [ ] Code reviewed and approved
- [ ] Documentation complete

### DevOps/SRE

- [ ] TLS configured and tested
- [ ] Monitoring stack operational
- [ ] Alert rules loaded
- [ ] Backup procedure tested
- [ ] Rollback procedure tested

### Security

- [ ] Authentication enforced
- [ ] Rate limiting configured
- [ ] CORS restricted
- [ ] Secrets in vault
- [ ] Logs sanitized

### Product/PM

- [ ] User acceptance tested
- [ ] Performance acceptable
- [ ] Error handling verified
- [ ] Rollback plan documented
- [ ] Success metrics defined

---

## 🚀 GO LIVE!

**Once all checklists complete:**

```bash
bash scripts/go_live_drill.sh && \
docker-compose -f docker-compose.full-stack.yml up -d && \
echo "🎉 PRODUCTION DEPLOYED!"
```

**Monitor for first 24 hours, then celebrate!** 🎊

---

**Last Updated:** October 18, 2025  
**Status:** ✅ Ready for production deployment
