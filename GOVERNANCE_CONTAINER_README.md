# 🐳 Governance Container Stack

Complete containerized governance system that integrates with your existing Athena infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GOVERNANCE CONTAINER STACK               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         GOVERNANCE CORE COMPONENTS                      │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐  │ │
│  │  │ Metrics Exporter│  │  Orchestrator   │  │ Canary  │  │ │
│  │  │   :9109         │  │    :9110        │  │ Monitor │  │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         MONITORING & ALERTING                          │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐  │ │
│  │  │   Prometheus    │  │    Grafana      │  │ Alert-  │  │ │
│  │  │    :9090        │  │     :3000       │  │ manager │  │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│              INTEGRATES WITH EXISTING ATHENA               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Postgres      │  │     Redis       │  │   Network   │  │
│  │                 │  │                 │  │             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Launch Governance Stack
```bash
# Launch all governance components
docker-compose -f docker-compose.governance.yml up -d

# Check status
docker-compose -f docker-compose.governance.yml ps
```

### 2. Verify Components
```bash
# Governance metrics (port 9109)
curl http://localhost:9109/metrics | head -10

# Prometheus (port 9090)
curl http://localhost:9090/-/healthy

# Grafana (port 3000)
# Open http://localhost:3000 (admin/admin)
```

### 3. Test Verdict Processing
```bash
# Send a test verdict
curl -X POST http://localhost:9110/verdict \
  -H "Content-Type: application/json" \
  -d '{"verdict": "HARD_FAIL", "actions": ["ROLLBACK"]}'
```

## Component Details

### Governance Metrics Exporter (`:9109`)
- **Purpose**: Exposes governance metrics to Prometheus
- **Metrics**: ECE, entropy drift, autoheal errors, fix confidence, etc.
- **Health**: `GET /health`

### Governance Orchestrator (`:9110`)
- **Purpose**: Processes judicial verdicts and applies actions
- **API**: `POST /verdict` - Accepts verdict JSON
- **State**: Persists to `/app/state/exec_state.json`
- **Health**: `GET /health`

### Governance Canary Monitor (`:9111`)
- **Purpose**: Monitors canary windows and makes promotion decisions
- **Metrics**: Solve rate delta, violation rate delta, etc.
- **Health**: `GET /health`

### Monitoring Stack
- **Prometheus** (`:9090`): Time-series database and alerting
- **Grafana** (`:3000`): Dashboards and visualizations
- **Alertmanager** (`:9093`): Alert routing and notifications

## Configuration

### Environment Variables
```bash
# Orchestrator
EXEC_STATE_PATH=/app/state/exec_state.json

# Canary Monitor
CANARY_WINDOW_SIZE=200

# Alert Routing (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Volume Mounts
```yaml
volumes:
  - ./state:/app/state:rw          # Execution state
  - ./policy:/app/policy:ro        # Governance policies
  - ./governance:/app/governance:ro  # Governance code
```

## Integration with Existing Athena

### Network Integration
The governance stack connects to your existing Athena network:
```yaml
networks:
  athena-network:
    external: true  # Uses your existing network
```

### Service Dependencies
```yaml
depends_on:
  - athena-postgres  # Your existing Postgres
  - athena-redis     # Your existing Redis
```

### Data Flow
```
Athena Services → Judicial Verdicts → Governance Orchestrator → Actions
                      ↓
               Governance Metrics → Prometheus → Grafana Dashboards
                      ↓
               Alert Conditions → Alertmanager → Slack/Email
```

## Development & Testing

### Local Testing
```bash
# Test verdict processing
python3 tools/verdict_replay.py --verdict HARD_FAIL --actions ROLLBACK

# Test governance integration
python3 test_governance_integration.py
```

### Build Individual Components
```bash
# Build metrics exporter
docker build -t governance-metrics ./governance/observability

# Build orchestrator
docker build -t governance-orchestrator ./orchestrator

# Build canary monitor
docker build -t governance-canary ./release
```

### Debug Containers
```bash
# View logs
docker-compose -f docker-compose.governance.yml logs governance-orchestrator

# Shell access
docker-compose -f docker-compose.governance.yml exec governance-orchestrator sh
```

## Security & Best Practices

### Non-Root Execution
All containers run as user `1001:1001` (governance user).

### Health Checks
All services include proper health checks with appropriate timeouts.

### Resource Limits
Consider adding resource limits in production:
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### Secrets Management
- Use Docker secrets or environment variables for sensitive data
- Never commit credentials to version control
- Use `.env` files for local development

## Troubleshooting

### Common Issues

**Port Conflicts**
```bash
# Check what's using ports
lsof -i :9109
# Change ports in docker-compose.governance.yml if needed
```

**Network Issues**
```bash
# Verify Athena network exists
docker network ls | grep athena

# Check service connectivity
docker-compose -f docker-compose.governance.yml exec governance-orchestrator ping athena-postgres
```

**Permission Issues**
```bash
# Fix volume permissions
docker-compose -f docker-compose.governance.yml exec governance-orchestrator chown -R governance:governance /app/state
```

### Monitoring Issues
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Grafana datasource
# Open http://localhost:3000 → Configuration → Data Sources
```

## Production Deployment

### Scaling Considerations
```yaml
services:
  governance-orchestrator:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
```

### Backup Strategy
```bash
# Backup governance state
docker run --rm -v governance_state:/data -v $(pwd):/backup alpine tar czf /backup/governance-state-$(date +%Y%m%d).tar.gz -C /data .
```

### Update Strategy
```bash
# Rolling update
docker-compose -f docker-compose.governance.yml up -d --no-deps governance-orchestrator
```

## Support & Documentation

- **Metrics Reference**: See `governance/observability/` for available metrics
- **API Documentation**: Check individual service health endpoints
- **Alert Configuration**: Review `monitoring/prometheus/alerts.yml`
- **Dashboard Templates**: Use `monitoring/grafana/dashboards/governance.json`

---

**Ready to launch your governance system?** 🚀

```bash
docker-compose -f docker-compose.governance.yml up -d
```

Your governance system will be running at:
- **Metrics**: http://localhost:9109
- **Orchestrator**: http://localhost:9110
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
