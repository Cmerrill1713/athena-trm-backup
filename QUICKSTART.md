# Athena Quick Start Guide

Get Athena running in **5 minutes** with auto-remediation enabled.

---

## Prerequisites

```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- jq, curl (for scripts)

# API Keys
export ANTHROPIC_API_KEY='your-key-here'
```

---

## Option 1: One-Command Start (Recommended)

```bash
./scripts/start_athena.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Start all Docker services
- ✅ Wait for services to be healthy
- ✅ Run comprehensive health check
- ✅ Display access URLs

---

## Option 2: Manual Start

```bash
# 1. Start services
docker compose -f docker-compose.athena-governance.yml up -d

# 2. Check health
make health-full

# 3. View logs
docker compose logs -f agi-remediator
```

---

## Verify Installation

### Check Services

```bash
# All services
curl http://localhost:9112/health  # Remediator: OK
curl http://localhost:9110/health  # Orchestrator: OK
curl http://localhost:9111/health  # Canary: OK
curl http://localhost:9090/-/healthy  # Prometheus: OK
```

### Run Demo

```bash
# Auto-remediation demo
./scripts/remediation_quickstart.sh

# Or via Makefile
make auto-remediation-demo
```

### Run Tests

```bash
# E2E tests
pytest tests/e2e/test_auto_remediation.py -v

# Or via Makefile
make auto-remediation-test
```

---

## Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Prometheus** | http://localhost:9090 | (none) |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Remediator Metrics** | http://localhost:9112/metrics | (none) |
| **Orchestrator Metrics** | http://localhost:9110/metrics | (none) |

---

## Configuration

### Event Bus Mode

```bash
# Local (development) - default
export EVENT_BUS=local

# Redis (production)
export EVENT_BUS=redis
export REDIS_URL=redis://localhost:6379/0
```

### Environment File

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

---

## Common Commands

```bash
# Start
./scripts/start_athena.sh

# Stop
docker compose -f docker-compose.athena-governance.yml down

# Restart
docker compose restart agi-remediator

# Logs
docker logs agi-remediator --tail 50
docker logs governance-orchestrator

# Health check
make health-full

# Demo
./scripts/remediation_quickstart.sh

# Tests
make auto-remediation-test
```

---

## Key Metrics

Query at http://localhost:9090:

```promql
# Remediation request rate
rate(governance_remediations_requested_total[5m])

# Success rate
rate(governance_remediations_promoted_total[1h]) 
/ 
rate(governance_remediations_completed_total[1h])

# Active services
up{job="governance-local"}
```

---

## Troubleshooting

### Services won't start

```bash
# Check Docker
docker ps
docker compose ps

# Check logs
docker logs agi-remediator
docker logs governance-orchestrator

# Restart
docker compose down
docker compose up -d
```

### Remediations not triggering

```bash
# Check event bus
docker logs agi-remediator | grep "exec.remediation"

# Check orchestrator
docker logs governance-orchestrator | grep "remediation"

# Verify metrics
curl http://localhost:9112/metrics | grep remediations
```

### Metrics not showing

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.instance | contains("9112"))'

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

---

## Next Steps

1. **Read Documentation**
   - [Auto-Remediation Guide](./AUTO_REMEDIATION_GUIDE.md)
   - [Architecture](./AUTO_REMEDIATION_ARCHITECTURE.md)
   - [Complete Summary](./PHASE_OMEGA_COMPLETE.md)

2. **Explore Features**
   - Run DGM evolution: `./scripts/dgm_quickstart.sh`
   - View Grafana dashboards
   - Check Prometheus alerts

3. **Integrate with Your System**
   - Replace remediation planner stub
   - Connect real canary validation
   - Add ChatOps notifications

---

## Support

- **Issues:** Check GitHub issues
- **Logs:** `docker compose logs`
- **Health:** `make health-full`
- **Docs:** `AUTO_REMEDIATION_GUIDE.md`

---

**You're ready! The system now automatically heals failures.** 🎯

