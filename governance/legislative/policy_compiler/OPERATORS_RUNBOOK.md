# 🚨 Athena v1.0.2 — Operator's Runbook

**Version**: v1.0.2-ghost
**Last Updated**: October 14, 2025
**On-Call**: [Your team contact]

---

## 🎯 Quick Reference

### Critical Endpoints
```bash
Backend Health:    http://localhost:8035/health
Backend Readiness: http://localhost:8035/readiness
API Docs:          http://localhost:8035/v1/docs
Metrics:           http://localhost:9108/metrics
Grafana:           http://localhost:3001
Avatar Status:     http://localhost:8035/v1/avatar/status
```

### Emergency Commands
```bash
# Stop everything
make stop-all

# Rollback avatar features
make avatar-rollback-force

# Restart backend
make backend-restart

# Check logs
make logs-backend
make logs-frontend
```

---

## 🚀 Startup Procedures

### Full System Start
```bash
cd /path/to/athena

# 1. Start backend services
make backend

# 2. Verify backend health
curl http://localhost:8035/health

# 3. Start frontend (macOS)
cd NeuroForgeApp
swift build
.build/debug/NeuroForgeApp &

# 4. Verify avatar status
curl http://localhost:8035/v1/avatar/status | jq
```

### Monitoring Start
```bash
# Start Prometheus
docker-compose -f docker-compose.monitoring.yml up -d prometheus

# Start Grafana
docker-compose -f docker-compose.monitoring.yml up -d grafana

# Import dashboards
open http://localhost:3001
# Login: admin/admin
# Import from grafana/dashboards/
```

---

## 🔍 Health Checks

### Backend Services
```bash
# Quick health check
curl -s http://localhost:8035/health | jq

# Expected: {"status": "ok", "timestamp": <unix_ts>}

# Readiness check (includes Redis)
curl -s http://localhost:8035/readiness | jq

# Expected: {"status": "ready", "redis": "ok", ...}
```

### Avatar System
```bash
# Check avatar state
curl -s http://localhost:8035/v1/avatar/status | jq

# Expected output:
# {
#   "state": "ghost",
#   "morph_enabled": false,
#   "has_model": false,
#   "updated_at": <timestamp>
# }
```

### Metrics
```bash
# Check Prometheus metrics
curl -s http://localhost:9108/metrics | grep athena_

# Key metrics:
# - athena_avatar_state (0=ghost, 1=photoreal)
# - http_requests_total
# - http_request_latency_seconds
```

---

## ⚠️ Common Issues

### Issue: Backend Not Responding
```bash
# Check if process is running
ps aux | grep uvicorn

# Check logs
tail -f logs/backend.log

# Restart backend
make backend-restart

# If still failing, check Redis
redis-cli ping
# Expected: PONG
```

### Issue: Frontend Can't Type
```bash
# This was fixed in v1.0.2, but if it recurs:

# 1. Check focus coordinator state
# 2. Restart frontend app
# 3. Clear derived data:
rm -rf NeuroForgeApp/.build
cd NeuroForgeApp && swift build

# 4. If persistent, check for regressions in:
#    - KeyCatchingTextEditor.swift
#    - InputFocusCoordinator.swift
```

### Issue: Avatar Not Showing
```bash
# Check avatar state
curl http://localhost:8035/v1/avatar/status

# If state is wrong, switch manually:
curl -X POST http://localhost:8035/v1/avatar/switch \
  -H "Content-Type: application/json" \
  -d '{"target_state": "ghost"}'

# Check frontend console for errors
# (View → Developer → JavaScript Console)
```

### Issue: High CPU Usage
```bash
# Check which process
top -o cpu

# If backend:
# - Check for infinite loops in logs
# - Restart with lower concurrency:
#   WORKERS=2 make backend

# If frontend:
# - Check avatar rendering frequency
# - Reduce animation frame rate
```

### Issue: Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# If not running, start it:
brew services start redis
# or
docker run -d -p 6379:6379 redis:7-alpine

# Verify connection:
redis-cli
> SET test "hello"
> GET test
> DEL test
> QUIT
```

---

## 🔥 Emergency Procedures

### Total System Failure
```bash
# 1. Stop everything
make stop-all
pkill -f NeuroForgeApp

# 2. Clear state
rm -rf .rollout.state pids/* logs/*

# 3. Restart from scratch
make backend
cd NeuroForgeApp && swift build && .build/debug/NeuroForgeApp &

# 4. Verify health
curl http://localhost:8035/health
```

### Avatar System Failure
```bash
# 1. Force rollback to ghost-only
make avatar-rollback-force

# 2. Clear Redis avatar state
redis-cli DEL athena:avatar:state
redis-cli DEL athena:avatar:updated

# 3. Restart backend
make backend-restart

# 4. Verify ghost mode
curl http://localhost:8035/v1/avatar/status | jq '.state'
# Expected: "ghost"
```

### Database Corruption
```bash
# Redis is ephemeral, safe to reset
redis-cli FLUSHALL

# Restart services to reinitialize
make backend-restart
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Watch

**Avatar State** (`athena_avatar_state`)
- 0 = ghost mode (expected)
- 1 = photoreal (should be 0 in v1.0.2)

**HTTP Requests** (`http_requests_total`)
- Monitor for sudden drops (service down)
- Monitor for sudden spikes (DDoS/bot)

**Request Latency** (`http_request_latency_seconds`)
- p50 < 100ms
- p95 < 500ms
- p99 < 1s

**In-Progress Requests** (`http_requests_in_progress`)
- Should be low (<10 normally)
- High values = potential deadlock

### Alert Thresholds

```yaml
# Example Prometheus alert rules
groups:
  - name: athena
    rules:
      - alert: BackendDown
        expr: up{job="athena-backend"} == 0
        for: 1m
        severity: critical

      - alert: HighLatency
        expr: http_request_latency_seconds{quantile="0.95"} > 1
        for: 5m
        severity: warning

      - alert: AvatarStateUnexpected
        expr: athena_avatar_state != 0
        for: 1m
        severity: warning
        annotations:
          summary: "Avatar not in ghost mode"
```

---

## 🔄 Rollback Procedures

### Full Rollback to v1.0.1
```bash
# 1. Stop current services
make stop-all

# 2. Checkout previous version
git checkout v1.0.1

# 3. Rebuild
make clean
make backend
cd NeuroForgeApp && swift build

# 4. Start services
make backend &
cd NeuroForgeApp && .build/debug/NeuroForgeApp &

# 5. Verify
curl http://localhost:8035/health
```

### Partial Rollback (Avatar Only)
```bash
# Just disable avatar features
make avatar-rollback-force

# Services stay running, avatar goes to safe mode
```

---

## 📝 Log Locations

```bash
Backend:           logs/backend.log
Frontend:          logs/frontend.log (if configured)
Redis:             /usr/local/var/log/redis.log
Prometheus:        prometheus/logs/
Grafana:           grafana/logs/

# View live logs
tail -f logs/backend.log
tail -f logs/frontend.log

# Search logs
grep ERROR logs/backend.log
grep avatar logs/backend.log | tail -50
```

---

## 🔐 Security Checks

### Daily
- [ ] Check for unauthorized API access
- [ ] Review error rates for anomalies
- [ ] Verify Redis is not externally accessible
- [ ] Check disk space

### Weekly
- [ ] Review audit logs
- [ ] Update dependencies
- [ ] Check for security advisories
- [ ] Backup configuration

### Monthly
- [ ] Rotate API keys
- [ ] Review access logs
- [ ] Update SSL certificates
- [ ] Security scan

---

## 📞 Escalation Path

### Level 1: Automated Response
- Health check failures → Auto-restart
- High latency → Alert only
- Redis connection issues → Auto-reconnect (3 retries)

### Level 2: On-Call Engineer
- Backend down > 5 minutes
- Avatar system failure
- Multiple service failures
- Data corruption

### Level 3: Senior Engineer
- Security incidents
- Data loss
- Persistent system-wide failure
- Need for emergency rollback

---

## 🧪 Testing in Production

### Smoke Tests
```bash
# Run automated smoke tests
make smoke-test

# Manual checks
curl http://localhost:8035/health
curl http://localhost:8035/v1/avatar/status
curl http://localhost:9108/metrics | grep athena_avatar_state
```

### Load Testing
```bash
# Light load test
ab -n 1000 -c 10 http://localhost:8035/health

# Expected: <100ms average response time
```

---

## 📚 Reference Links

- **API Documentation**: http://localhost:8035/v1/docs
- **Architecture Docs**: `docs/ARCHITECTURE.md`
- **Release Notes**: `RELEASE_NOTES_v1.0.2.md`
- **Lint Debt**: `docs/LINT_DEBT.md`
- **GitHub Issues**: https://github.com/yourusername/athena/issues

---

## ✅ Pre-Shift Checklist

Before going on-call:
- [ ] Verify access to all systems
- [ ] Test emergency commands
- [ ] Review recent deployments
- [ ] Check current system health
- [ ] Read latest incident reports
- [ ] Update contact information

---

## 📋 Post-Incident Checklist

After resolving an incident:
- [ ] Document what happened
- [ ] Note root cause
- [ ] List actions taken
- [ ] Update runbook if needed
- [ ] Create follow-up tickets
- [ ] Notify team
- [ ] Schedule post-mortem

---

**Last Validated**: October 14, 2025
**Next Review**: November 14, 2025

*"Stay calm, check logs, follow the runbook."*
