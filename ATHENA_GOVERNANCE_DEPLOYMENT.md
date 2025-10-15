# Athena + Governance Unified Stack

## Overview

This merged docker-compose stack combines your core Athena infrastructure with the governance system for production-ready AI policy enforcement.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ATHENA NETWORK                               │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    GOVERNANCE LAYER                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │ │
│  │  │Metrics      │  │Orchestrator │  │Canary      │             │ │
│  │  │Exporter     │◄─┤             │◄─┤Monitor     │             │ │
│  │  │:9109        │  │:9110        │  │:9111       │             │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    ATHENA CORE SERVICES                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │ │
│  │  │API          │  │Evolutionary │  │Knowledge   │             │ │
│  │  │:8888        │  │:8014        │  │Gateway     │             │ │
│  │  │             │  │             │  │:8088       │             │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    INFRASTRUCTURE                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │ │
│  │  │Postgres     │  │Redis        │  │Weaviate    │             │ │
│  │  │:5432        │  │:6379        │  │:8090       │             │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    MONITORING                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │ │
│  │  │Prometheus   │  │Grafana      │  │AlertManager│             │ │
│  │  │:9090        │  │:3001        │  │:9093       │             │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

### Verdict → Action Pipeline
- **Governance Orchestrator** monitors actual API traffic (not test events)
- **Canary Monitor** analyzes production request patterns
- **Metrics Exporter** feeds governance KPIs to Prometheus
- **AlertManager** triggers rollbacks on policy violations

### Shared Infrastructure
- **Single Postgres** database for both Athena and governance data
- **Unified Redis** cache for session management and governance state
- **Consolidated Monitoring** with governance dashboards in Grafana
- **Common Network** (athena-network) for all service communication

## Deployment

### Start Everything
```bash
docker-compose -f docker-compose.athena-governance.yml up -d
```

### Check Health
```bash
# Governance services
curl http://localhost:9109/health  # Metrics Exporter
curl http://localhost:9110/health  # Orchestrator
curl http://localhost:9111/health  # Canary Monitor

# Core Athena services
curl http://localhost:8888/health  # API
curl http://localhost:8014/health  # Evolutionary
```

### Monitoring Access
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## Governance Features

### Active Monitoring
- **ECE Tracking**: Monitors evolutionary computation efficiency
- **Entropy Drift**: Detects unexpected behavior patterns
- **Violation Detection**: Real-time policy enforcement
- **Auto-healing**: Automatic remediation on threshold breaches

### Alert Rules
- ECE > 6%: Warning
- Entropy drift > 25%: Critical
- Violation rate spike: Warning
- Autoheal errors: Warning

## CI/CD Integration

### Pre-deployment Checks
```bash
# Run governance validation before deploy
curl -X POST http://localhost:9110/api/v1/validate-deployment \
  -H "Content-Type: application/json" \
  -d '{"environment": "production"}'
```

### Rollback Triggers
- Governance alerts automatically trigger rollback scripts
- Policy violations block deployments via GitHub Actions
- Canary failures initiate gradual traffic shifting

## Service Dependencies

```
governance-orchestrator
├── governance-metrics-exporter
├── athena-postgres
├── athena-redis
├── athena-prometheus
└── athena-api (monitors traffic)

governance-canary-monitor
├── governance-orchestrator
├── governance-metrics-exporter
├── athena-prometheus
├── athena-api
└── athena-evolutionary

athena-prometheus
├── All services (scrapes metrics)
└── alertmanager (sends alerts)
```

## Volume Management

All data persists across restarts:
- `athena_postgres_data`: Core Athena data
- `athena_prometheus_data`: Metrics history
- `athena_grafana_data`: Dashboards and configs
- Governance state stored in `./state/` directory

## Scaling Considerations

### Horizontal Scaling
- Governance services can be scaled independently
- Metrics exporters are stateless
- Orchestrator can run multiple instances

### Resource Allocation
```yaml
# Add to services as needed
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

## Troubleshooting

### Common Issues

1. **Governance services can't connect to Postgres**
   - Ensure `athena-postgres` is healthy
   - Check network connectivity: `docker network inspect athena-network`

2. **Metrics not appearing in Prometheus**
   - Verify service health: `curl http://localhost:9109/health`
   - Check Prometheus targets: http://localhost:9090/targets

3. **Alerts not firing**
   - Review alert rules in `monitoring/prometheus/alerts.yml`
   - Check AlertManager configuration

### Logs
```bash
# Governance service logs
docker-compose -f docker-compose.athena-governance.yml logs governance-orchestrator
docker-compose -f docker-compose.athena-governance.yml logs governance-metrics-exporter

# All services
docker-compose -f docker-compose.athena-governance.yml logs
```

## Migration from Separate Stacks

If migrating from separate `docker-compose.athena.yml` and `docker-compose.governance.yml`:

1. **Stop existing stacks**:
   ```bash
   docker-compose -f docker-compose.athena.yml down
   docker-compose -f docker-compose.governance.yml down
   ```

2. **Start unified stack**:
   ```bash
   docker-compose -f docker-compose.athena-governance.yml up -d
   ```

3. **Verify data migration**: Check that Postgres data is intact

4. **Update monitoring**: Grafana dashboards will be available at the new port (3001)

## Next Steps

1. **CI/CD Gates**: Add governance checks to your GitHub Actions
2. **Alert Routing**: Configure Slack/Discord notifications for governance alerts
3. **Dashboard Setup**: Import governance dashboards into Grafana
4. **Load Testing**: Validate governance performance under production load
