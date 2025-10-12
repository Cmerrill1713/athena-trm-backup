# 🧪 Tier 4 Proof Guide - 3-Minute Validation

> **Green = ship it. Yellow = fix fast.**

---

## ✅ Run This Now (3 Minutes)

```bash
make tier4-proof
```

**Expected:** All green checks ✅

---

## 🧯 Micro-Runbook (If Anything Fails)

### Collector missing (no traces/metrics)
```bash
make otel-up
curl -s http://127.0.0.1:4318/  # Should respond
make tier4-proof
```

### Rate-limit test flaps (no 429s)
```bash
export RATE_LIMIT=100/minute
make stack-restart && make tier4-proof
```

### Timeout test flaps (no 504)
```bash
export REQ_TIMEOUT_S=30
make stack-restart && make tier4-proof
```

### Graceful shutdown fails
```bash
export DRAIN_S=5
make stack-restart && make shutdown-drain-test
```

### Auth 401 errors
```bash
# Secrets loader fell back to env
export UAT_TOKEN=supersecret
export ATH_TOKEN=supersecret
make stack-restart && make athena-tests-smoke
```

---

## 🔎 Quick Spot-Checks (Receipts Not Vibes)

### Metrics Live
```bash
curl -s 127.0.0.1:8014/metrics | head
curl -s 127.0.0.1:8181/metrics | head
curl -s 127.0.0.1:8090/metrics | head
```

### Guardrails Working
```bash
for i in {1..120}; do
    curl -s -o /dev/null -w "%{http_code}\n" 127.0.0.1:8014/health
done | sort | uniq -c

# Expect: lots of 200s, then 429s
```

### Graceful Shutdown
```bash
make shutdown-drain-test

# Logs should show:
# [Shutdown] Draining for 5s ...
# [Shutdown] Done.
```

---

## 🏷️ Tag & Lock It (When Green)

```bash
git add -A
git commit -m "Tier 4: tracing + guardrails + graceful shutdown complete"
git tag -a v0.9.3-t4-complete -m "Tier 4 complete"
git push && git push origin v0.9.3-t4-complete
```

---

## 🧨 Rollback (10 Seconds)

```bash
git reset --hard v0.9.3-t4-foundation
make stack-restart
```

---

## 📈 Optional: Prove SLOs Quickly

### p95 Latency (<250ms)
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{service="bridge"}[5m])
)
```

### Error Rate (<1%)
```promql
rate(http_requests_total{service="bridge",status=~"5.."}[5m])
  /
rate(http_requests_total{service="bridge"}[5m])
```

---

## 🚀 Next Move

### Option A: Ship Tier 4 to Production
```bash
make prod-build
make prod-up
make prod-status
```

### Option B: Continue to Tier 5 (Blue-Green + Canary)
**Say "Tier 5"** and I'll deliver:
- Dockerfiles for all services
- `make prod-up` command
- Canary bridge on :8015
- Traffic mirroring
- Promote gate (error/latency thresholds)

---

## ✅ TL;DR

1. **Run:** `make tier4-proof`
2. **If green:** Tag with commands above
3. **If yellow:** Use micro-runbook, re-run
4. **When ready:** Say "Tier 5" for next layer

---

**Status:** ✅ TIER 4 WIRED
**Next:** Prove it (3 min)
**Then:** Tag or Tier 5

🎯 **Run `make tier4-proof` now!**
