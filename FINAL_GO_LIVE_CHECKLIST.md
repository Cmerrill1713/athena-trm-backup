# ✅ FINAL GO-LIVE CHECKLIST

**Run these steps in order before shipping to production.**

---

## 🚀 Pre-Flight (5 minutes)

### **1. Bring up stack (offline default)**

```bash
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate \
  ollama \
  rag-gateway \
  smart-chat \
  openai-compat
```

### **2. Restore KB if needed**

```bash
test -d volumes/weaviate_data || echo "⚠️  restore corpus before shipping"

# If corpus missing:
# - Restore from backup: cp -r /path/to/backup/weaviate_data volumes/
# - OR re-seed: make seed-corpus
```

### **3. One-command acceptance (hard fail if not ship-ready)**

```bash
make ship-check
```

**Green (exit 0)** → Proceed to canary  
**Red (exit 1)** → Fix the failing gate shown by `ship_check.sh`

**Note:** `make canary-rollback` isn't needed yet; fix issues locally first.

---

## 🕯️ Canary Rollout (Guarded)

### **Start at 5%**

```bash
make canary-start
```

Captures baseline: p95, error rate, hit@5

### **Monitor live**

```bash
make canary-watch
```

Watch for:

- p95 ≤ baseline + 10%
- 5xx < 1%
- hit@5 ≥ 0.97

**Ctrl+C to stop monitoring**

### **Promote (only if green ≥10-15 min)**

```bash
# After 10-15 min of green metrics:
make canary-promote  # 5% → 25%

# Wait 10-15 min, watch metrics
make canary-promote  # 25% → 50%

# Wait 10-15 min, watch metrics
make canary-promote  # 50% → 100%
```

### **Instant safety valve**

```bash
make canary-rollback
```

Reverts to baseline instantly if any gate fails.

---

## 📊 Pin the Baseline (So Regressions Are Obvious)

After a clean run, freeze metrics for future comparisons:

```bash
make metrics-snapshot > artifacts/baseline_$(date +%Y%m%d).json
```

Captures:

- Route mix
- p95 latency
- Quality gates
- Service versions

**Store in artifacts/** for regression detection.

---

## 🔒 CI Wiring (Block Merges Unless Ship-Ready)

Add to `.github/workflows/ship-gate.yml`:

```yaml
name: Ship Gate
on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  ship-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: |
          docker-compose -f docker-compose.full-stack.yml up -d
          sleep 10

      - name: Run ship check
        run: make ship-check
        # Fails build if any of the 8 gates trip:
        # - health
        # - bridge latency
        # - router decisions
        # - metrics
        # - rag-eval
        # - delta
        # - integration smoke
        # - DocsV2 presence

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: ship-check-artifacts
          path: |
            artifacts/*.json
            artifacts/*.md
            /tmp/ship_check_smoke.log
```

**Build fails if exit code 1** → Blocks merge until fixed.

---

## 🛡️ Two Tiny Hardening Tweaks (High ROI)

### **1. Secrets Management**

**Never commit tokens/keys.** Move to env/Compose secrets:

```bash
# Create .env (gitignored)
cat > .env <<EOF
WEAVIATE_API_KEY=your-key-here
OLLAMA_TOKEN=your-token-here
GRAFANA_PASSWORD=your-password-here
EOF

# Update docker-compose to use secrets
```

**In docker-compose.full-stack.yml:**

```yaml
services:
  rag-gateway:
    environment:
      - WEAVIATE_API_KEY=${WEAVIATE_API_KEY}
    env_file:
      - .env
```

**Add to .gitignore:**

```
.env
*.key
*.pem
secrets/
```

### **2. Artifacts Retention**

**Keep artifacts/** from every `ship-check` to prove why a version shipped:

```bash
# After ship-check passes
mkdir -p artifacts/shipped/$(date +%Y%m%d_%H%M%S)
cp artifacts/*.json artifacts/*.md artifacts/shipped/$(date +%Y%m%d_%H%M%S)/

# Add git tag
git tag -a v1.0.0-$(date +%Y%m%d) -m "Shipped: all gates passed"
git push --tags
```

**Benefits:**

- Audit trail for compliance
- Regression investigation
- Rollback decision making

---

## 📱 iPhone + Controlled Egress Reminders

### **PWA over HTTPS**

```bash
# For local dev: use mkcert
brew install mkcert
mkcert -install
mkcert localhost 127.0.0.1 ::1

# For production: use real cert (Let's Encrypt)
certbot certonly --standalone -d your-domain.com
```

**Update nginx.conf:**

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /v1 {
        proxy_pass http://openai-compat:3000;
    }
}
```

**Set adapter CORS:**

```yaml
# In docker-compose
services:
  openai-compat:
    environment:
      - CORS_ORIGIN=https://your-domain.com
```

### **Controlled Egress for Research**

```bash
# Enable internet for paper ingestion
make online

# Fetch approved papers
make papers-search
make papers-queue
make papers-fetch
make papers-embed

# Disable internet (back to air-gapped)
make offline
```

**Your gates already protect quality drift** — RAG eval runs after ingest.

---

## 🚨 If a Gate Fails (Fast Fixes)

### **KB hits = 0 / slow search**

```bash
# Confirm DocsV2 has 384-dim vectors
curl 'localhost:8090/v1/objects?class=DocsV2&limit=1' | jq '.objects[0].vector | length'

# Should return: 384

# If wrong: re-seed with correct dimensions
make seed-corpus

# Warm cache with a few queries
for i in {1..5}; do
  curl -s localhost:8088/kb/search -d '{"query":"test","topK":5}' > /dev/null
done
```

### **Router misroutes**

```bash
# Adjust threshold
export RAG_PROBE_THRESHOLD=0.60  # Lower = more RAG

# Re-run probe
python3 scripts/router_probe.py --q "What is X?"
python3 scripts/router_probe.py --q "Brainstorm Y"
python3 scripts/router_probe.py --q "Compare A vs B"

# If good: persist in docker-compose
```

### **Delta regression**

```bash
# Check which mode regressed
cat artifacts/delta_report.md

# If semantic < BM25:
#   → Bump HNSW ef in Weaviate
#   → Check embeddings quality
#   → Re-run: make rag-delta

# If hybrid < both:
#   → Tune alpha (0.7 default)
#   → Increase top_k
```

### **Stream errors**

```bash
# Check nginx config
grep proxy_buffering nginx.conf

# Should be: proxy_buffering off;

# Check timeout
grep proxy_read_timeout nginx.conf

# Should be: proxy_read_timeout 300s;

# Restart nginx
docker-compose restart nginx
```

---

## ✅ Final Checklist

Before shipping:

- [ ] `make ship-check` passes (exit 0)
- [ ] Corpus populated (volumes/weaviate_data exists)
- [ ] Secrets moved to .env (not committed)
- [ ] CI workflow added (.github/workflows/ship-gate.yml)
- [ ] Artifacts retention enabled
- [ ] Baseline metrics captured
- [ ] HTTPS configured for PWA
- [ ] CORS origin set correctly
- [ ] Canary rollback tested once (dry run)
- [ ] Day-2 runbook scheduled (daily cron)

---

## 🚀 The Moment of Truth

```bash
# 1. Pre-flight
docker-compose -f docker-compose.full-stack.yml up -d
make ship-check

# 2. If green:
make canary-start
make canary-watch

# 3. Promote gradually (3x)
make canary-promote  # After 10-15 min each

# 4. If anything goes wrong:
make canary-rollback

# 5. If all green:
# → You shipped! 🎉
```

---

## 📊 Post-Ship

### **Daily**

```bash
make day2-check
```

### **Weekly**

```bash
make trm-train       # Refresh training data
make rag-delta       # Check for drift
```

### **Monthly**

```bash
make trm-finetune    # Retrain TRM
make soak-2h         # Full load test
```

---

**🔥 You're set. Flip `make ship-check`, then canary. If it's green, it's gone!**
